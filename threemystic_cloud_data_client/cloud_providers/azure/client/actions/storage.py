from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.costmanagement.models import TimeframeType, OperatorType, QueryColumnType, QueryDefinition, QueryTimePeriod, QueryDataset, QueryAggregation, QueryGrouping, QueryFilter, QueryComparisonExpression
from azure.mgmt.compute.models import VirtualMachineScaleSet, VirtualMachineScaleSetVM, Disk

from threemystic_cloud_data_client.cloud_providers.azure.client.actions.vm import cloud_data_client_azure_client_action as vm_action
from threemystic_cloud_data_client.cloud_providers.azure.client.actions.vmss import cloud_data_client_azure_client_action as vmss_action

class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="storage", 
      logger_name= "cloud_data_client_azure_client_action_storage", 
      uniqueid_lambda = lambda: True
      *args, **kwargs)
  
  
    
  def __get_cost_by_resource_query_definition_mtd(self):
    mtd = self.get_cloud_client().get_default_querydefinition()
    mtd.timeframe = TimeframeType.MONTH_TO_DATE

    mtd.dataset.filter = QueryFilter(
        dimensions= QueryComparisonExpression(
        name= "ResourceType",
        operator= OperatorType.IN_ENUM,
        values= ["Microsoft.Compute/disks"]
      )
    )
    mtd.dataset.grouping= [
      QueryGrouping(
        type= QueryColumnType.DIMENSION,
        name= "ResourceId"
      )
    ]

    return mtd
  
  def __get_cost_by_resource_query_definition_ytd(self):
    ytd = self.__get_cost_by_resource_query_definition_mtd()
    ytd.timeframe = TimeframeType.CUSTOM
    ytd.time_period = QueryTimePeriod(
      from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().get().year}-01-01T00:00:00+00:00"),
      to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().get().year}-12-31T23:59:59+00:00")      
    )

    ytd.dataset.filter = QueryFilter(
        dimensions= QueryComparisonExpression(
        name= "ResourceType",
        operator= OperatorType.IN_ENUM,
        values= ["Microsoft.Compute/disks"]
      )
    )
    ytd.dataset.grouping= [
      QueryGrouping(
        type= QueryColumnType.DIMENSION,
        name= "ResourceId"
      )
    ]

    return ytd

  async def _pre_load_main_process(self, pool, *args, **kwarg):
    self.__vm = None
    base_action_params = {
      "cloud_data_client": self.get_cloud_data_client(),
      "common": self.get_common(),
      "logger": self.get_common().get_logger()
    }
    # This is required because #the normal disk command only looks at long lived disks
    vmss_data = vmss_action(
      **base_action_params
    )
    self.__vmss = await vmss_data.main(pool=pool) 

    self.__cost_by_resource_query_definition = {
      "MTD": self.__get_cost_by_resource_query_definition_mtd(),
      "YTD": self.__get_cost_by_resource_query_definition_ytd()
    }

    vm_data = vm_action(
      **base_action_params
    )
      
    self.__vm = await vm_data.main(pool=pool)
      

  async def __get_attached_devices_vm_check_os(self, disk, vm_os_disk = None, *args, **kwarg):
    if vm_os_disk is None:
      return False
    
    if vm_os_disk.get("managed_disk") is None:
      return False
    
    return True if vm_os_disk.get("managed_disk")["id"] == disk.id else False

  async def __get_attached_devices_vm_check_data(self, disk, vm_data_disks = None, *args, **kwarg):
      if vm_data_disks is None:
        return False
      
      if len(vm_data_disks) < 1:
        return False
      
      for mdisk in vm_data_disks:
        if mdisk["id"] == disk.id:
          return True 

      return False
  async def __get_attached_devices_vm_check(self, disk, vm, vmss= None, *args, **kwarg):
    if vm.get("storage_profile") is None:
      return None

    tasks = {
      "os_disk": self.__get_attached_devices_vm_check_os(disk= disk, vm_os_disk= vm["storage_profile"].get("os_disk")),
      "data_disks": self.__get_attached_devices_vm_check_data(disk= disk, vm_os_disk= vm["storage_profile"].get("data_disks"))
    }

    await asyncio.wait(tasks.values())

    for _, task in tasks.items():
      if task.result():
        return self.common.merge_dictionary({
          "extra_disk_group_type": "vm" if vmss is None else "vmss", 
          "extra_disk_group": None if vmss is None else vmss["name"],
          "extra_disk_group_primary": None if vmss is None else vmss["extra_vmss_vms"][0]["id"] == vm["id"] 
          }, 
          vm)

    return None



  async def __get_attached_devices_vm(self, account, disk, loop, *args, **kwarg):
    if self.__vm is None:
      return None
    
    account_id = self.get_cloud_client().get_account_id(account= account)
    if self.__vm.get(account_id) is None:
      return None

    tasks = []
    for vm in self.__vm[account_id]:
      tasks.append(loop.create_task(self.__get_attached_devices_vm_check(vm= vm, disk= disk )))
      done_tasks, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout= 1)
      tasks = [task for task in tasks]
      for done in done_tasks:
        if done.result() is not None:
          return [ done.result() ]
    
    return None

  async def __get_attached_devices_vmss(self, account, disk, loop, *args, **kwarg):
    if self.__vmss is None:
      return None

    account_id = self.get_cloud_client().get_account_id(account= account)
    if self.__vmss.get(account_id) is None:
      return None
    
    tasks = []
    for vmss in self.__vmss[account_id]:
      for vm in vmss["extra_vmss_vms"]:
        tasks.append(loop.create_task(self.__get_attached_devices_vm_check(vm= vm, disk= disk, vmss= vmss )))
        done_tasks, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout= 1)
        tasks = [task for task in tasks]
        for done in done_tasks:
          if done.result() is not None:
            return [ done.result() ]
    
    return None
      
  async def __get_attached_devices(self, account, disk, loop, *args, **kwarg):
    tasks = {
      "vm": loop.create_task(self.__get_attached_devices_vm(account= account, disk= disk, loop= loop)),
      "vmss": loop.create_task(self.__get_attached_devices_vmss(account= account, disk= disk, loop= loop))
    }

    await asyncio.wait(tasks.values())

    return_data = []
    for _, item in tasks.items():
      if item.result() is None:
        continue
      
      return_data += item.result()

    return return_data

  async def __get_account_disk_merged(self, account, cost_by_resource, item, loop, *args, **kwarg):
    return self.get_common().helper_type().dictionary().merge_dictionary({
          "extra_account": self.get_cloud_client().serialize_azresource(resource= account),
          "extra_region": self.get_cloud_client().get_azresource_location(resource= item),
          "extra_resourcegroups": [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
          "extra_id": self.get_cloud_client().get_resource_id_from_resource(resource= item),
          "extra_attached_devices": (await self.__get_attached_devices(account=account, disk= item, loop= loop)),
          "extra_resource_cost": {
            period: cost_by_resource_results.get(self.get_cloud_client().get_resource_id_from_resource(resource= item)) for period, cost_by_resource_results in cost_by_resource.items()
          }
        }, self.get_cloud_client().serialize_azresource(resource= item))

  def __process_vmss_vm_disks_skip(self, vm: VirtualMachineScaleSetVM, *args, **kwarg):
    if not hasattr(vm, "storage_profile"):
      return True

    if not hasattr(vm.storage_profile, "os_disk"):
      return True

    if not hasattr(vm.storage_profile.os_disk, "managed_disk"):
      return True

    return False

  def __convert_vmss_vm_disks_disks_creationData(self, vm: VirtualMachineScaleSetVM, *args, **kwarg):
    creationData = {
      "createOption": vm.storage_profile.os_disk.create_option,
      "imageReference": vm.storage_profile.image_reference,
    }
    return creationData

  async def __convert_vmss_vm_disks_disks(self, vmss:VirtualMachineScaleSet, vm: VirtualMachineScaleSetVM, *args, **kwarg):
    os_disk_data = {
      "id": vm.storage_profile.os_disk.managed_disk.id,
      "name": vm.storage_profile.os_disk.name,
      "location": vmss.location,
      "tags": vmss.tags,
      "sku": {
        "name": vm.storage_profile.os_disk.managed_disk.storage_account_type,
        "tier": vm.storage_profile.os_disk.managed_disk.storage_account_type.split('_')[0]
      },
      "type": "Microsoft.Compute/disks",
      "properties": {
        "osType": vm.storage_profile.os_disk.os_type,
        'creationData': (self.__convert_vmss_vm_disks_disks_creationData(vm= vm)),
        "diskSizeGB": vm.storage_profile.os_disk.disk_size_gb,
        "diskSizeBytes": vm.storage_profile.os_disk.disk_size_gb * 1024 * 1024 * 1024,
      }

    }
    os_disk = self.get_cloud_client().deserialize_azresource(
      aztype= Disk,
      resource= os_disk_data
    )

    if len(vm.storage_profile.data_disks) > 0:
      raise Exception(f"vmss {vmss.name} - ({vmss.id}) has vm {vm.name} that has data disks. Update Script")

    return [os_disk]

  async def __process_vmss_vm_disks(self, vmss:VirtualMachineScaleSet, vm: VirtualMachineScaleSetVM, *args, **kwarg):
    return (await self.__convert_vmss_vm_disks_disks(vm= vm, vmss= vmss))
    
    

  async def __get_account_vmss_disks(self, account, cost_by_resource, loop, *args, **kwarg):
    return_disks = []
    account_id = self.get_cloud_client().get_account_id(account= account)

    for vmss in self.__vmss[account_id]:
      for vm in vmss["extra_vmss_vms"]:
        vm_object = self.get_cloud_client().deserialize_azresource(aztype= VirtualMachineScaleSetVM, resource= vm)
        if self.__process_vmss_vm_disks_skip(vm=vm_object):
          continue
        return_disks += (await self.__process_vmss_vm_disks(vm= vm_object, vmss= self.get_cloud_client().deserialize_azresource(aztype= VirtualMachineScaleSet, resource= vmss)))
    
    disk_tasks = [ loop.create_task(self.__get_account_disk_merged(account= account, cost_by_resource= cost_by_resource, item= item, loop= loop)) for item in return_disks]
    if len(disk_tasks) < 1:
      return []
    await asyncio.wait(disk_tasks)
    return [ task.result() for task in disk_tasks]
        

  async def __get_account_disks(self, account, cost_by_resource, loop, *args, **kwarg):
    client = ComputeManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))

    disk_tasks = [ loop.create_task(self.__get_account_disk_merged(account= account, cost_by_resource= cost_by_resource, item= item, loop= loop)) for item in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.disks.list()
          )]
    if len(disk_tasks) < 1:
      return []
    await asyncio.wait(disk_tasks)
    return [ task.result() for task in disk_tasks]


  async def _process_account_data(self, account, loop, *args, **kwarg):
    cost_by_resource = {}
    
    for period, query in self.__cost_by_resource_query_definition.items():
      cost_by_resource[period] = {}
      resource_cost_details = self.get_cloud_client().get_costmanagement_account(account= account, query_definition= query)
      
      if resource_cost_details is not None:
        for row in resource_cost_details.rows:
          if cost_by_resource[period].get(row[1].lower()) is None:
            cost_by_resource[period][row[1].lower()] = row[0]
            continue

          cost_by_resource[period][row[1].lower()] += row[0]
          
    
    return {
      "account": account,
      "data": (
        (await self.__get_account_disks(account= account, cost_by_resource= cost_by_resource, loop= loop)) +
        (await self.__get_account_vmss_disks(account= account, cost_by_resource= cost_by_resource, loop= loop)) 
      )
    }