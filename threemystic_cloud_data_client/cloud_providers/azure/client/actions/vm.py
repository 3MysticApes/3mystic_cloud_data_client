from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network.models import LoadBalancer


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="vm", 
      logger_name= "cloud_data_client_azure_client_action_vm", 
      uniqueid_lambda = lambda: True
      *args, **kwargs)
  
  

  async def __process_get_resources_vm_public_ips(self, account, *args, **kwargs):    
    try:
        client = NetworkManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))

        return { self.get_cloud_client().get_resource_id_from_resource(resource= public_ip):public_ip for public_ip in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.public_ip_addresses.list_all()
          )
        }
           
    except Exception as err:
      return {} 

  async def __process_get_resources_vm_load_balancers(self, account, public_ips, *args, **kwargs):    
    try:
      client = NetworkManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
      return_data = {}
      load_balancers = {self.get_cloud_client().get_resource_id_from_resource(resource= lb): self.get_cloud_client().serialize_azresource(resource= lb) for lb in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.load_balancers.list_all()
        )}
      
      load_balancers_front_end = {}
      for id_lb, lb in load_balancers.items():
        for frontend_ip in lb.frontend_ip_configurations:
          for frontend_ip_load_balancing_rule in frontend_ip.load_balancing_rules:
            load_balancers_front_end[self.get_cloud_client().get_resource_id_from_resource(resource= frontend_ip_load_balancing_rule)] = {
              "id_lb": id_lb,
              "id_public_ip": self.get_cloud_client().get_resource_id_from_resource(resource= frontend_ip.public_ip_address)
            }
        
      for backend_address_pool in LoadBalancer(lb).backend_address_pools:
        vm_data = []
        for backend_address_load_balancing_rule in backend_address_pool.load_balancing_rules:
          vm_data.append({
            "load_balancer": load_balancers[load_balancers_front_end[self.get_cloud_client().get_resource_id_from_resource(resource= backend_address_load_balancing_rule)]["id_lb"]],
            "public_ip": self.get_cloud_client().serialize_azresource(resource= public_ips[load_balancers_front_end[self.get_cloud_client().get_resource_id_from_resource(resource= backend_address_load_balancing_rule)]["id_public_ip"]]),
          })

        for backend_address in backend_address_pool.load_balancer_backend_addresses:
          if backend_address.network_interface_ip_configuration is not None:
            if self.get_cloud_client().get_resource_id_from_resource(resource= backend_address.network_interface_ip_configuration) is not None:
              key = self.get_cloud_client().get_resource_id_from_resource(resource= backend_address.network_interface_ip_configuration)
            else:
              key = backend_address.ip_address

            if return_data.get(key) is not None:
              return_data[key].append(vm_data)
              continue

            return_data[key] = vm_data
   
      return return_data      
           
    except Exception as err:
      return {} 

  async def __process_get_resources_vm_nics(self, account, public_ips, *args, **kwargs):    
    try:
      client = NetworkManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
      return_data = {}
      for nic in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.network_interfaces.list_all()
        ):
          if nic.virtual_machine is None:
            continue
          if return_data.get( self.get_cloud_client().get_resource_id_from_resource(resource= nic.virtual_machine)) is not None:
            return_data.get( self.get_cloud_client().get_resource_id_from_resource(resource= nic.virtual_machine)).append(
              self.get_common().helper_type().dictionary().merge_dictionary([
                {},
                {
                  "extra_public_ips": [
                    self.get_cloud_client().serialize_azresource(resource= public_ips[self.get_cloud_client().get_resource_id_from_resource(resource= ip_config.public_ip_address)])
                    for ip_config in nic.ip_configurations if self.get_cloud_client().get_resource_id_from_resource(resource= ip_config.public_ip_address) is not None]
                },
                self.get_cloud_client().serialize_azresource(resource= nic)
              ])
            )
            continue
          

          return_data[self.get_cloud_client().get_resource_id_from_resource(resource= nic.virtual_machine)] = [
            self.get_common().helper_type().dictionary().merge_dictionary([
              {},
              {
                "extra_public_ips": [
                  self.get_cloud_client().serialize_azresource(resource= public_ips[self.get_cloud_client().get_resource_id_from_resource(resource= ip_config.public_ip_address)])
                  for ip_config in nic.ip_configurations if self.get_cloud_client().get_resource_id_from_resource(resource= ip_config.public_ip_address) is not None]
              },
              self.get_cloud_client().serialize_azresource(resource= nic)
            ])
          ]
      
      return return_data
          
        
           
    except Exception as err:
      return {}

  async def __process_get_resources_vm_availability_sets(self, client:ComputeManagementClient, account, *args, **kwargs):    
    try:
      return_data = {}

      for availability_set in  self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.availability_sets.list_by_subscription()
        ):
          for vm in availability_set.virtual_machines:
            return_data[self.get_cloud_client().get_resource_id_from_resource(resource= vm)] = availability_set
      
      return return_data
    except Exception as err:
      return {}
    
  async def __process_get_resources_vm(self, account, *args, **kwargs):
    resource_client = ResourceManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    try:
        return {self.get_cloud_client().get_resource_id_from_resource(resource= resource): resource for resource in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: resource_client.resources.list(filter="resourceType eq 'Microsoft.Compute/virtualMachines'", expand="createdTime,changedTime,provisioningState")
          )
        }
    except:
        return {}

  async def _process_account_data_get_vm_load_balancers(self, vm_nics, load_balancers_by_nics, *args, **kwargs):
    return_load_balancers = []
    for nic in vm_nics:
      return_load_balancers += [lb_data for nic_id, lb_data in load_balancers_by_nics.items() if nic_id == self.get_cloud_client().get_resource_id_from_resource(resource= nic)]
      # I might look into the whole private IP agress later, the issue is I have to validate networks
    
    return return_load_balancers
  
  async def _process_account_data(self, account, loop, *args, **kwargs):
    client = ComputeManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    public_ips = await self.__process_get_resources_vm_public_ips(account= account)
    tasks = {
        "resource": loop.create_task(self.__process_get_resources_vm(account= account)),
        "availability_sets": loop.create_task(self.__process_get_resources_vm_availability_sets(client= client, account= account)),
        "nics": loop.create_task(self.__process_get_resources_vm_nics(account= account, public_ips= public_ips)),
        "load_balancers": loop.create_task(self.__process_get_resources_vm_load_balancers(account= account, public_ips= public_ips)),
    }

    await asyncio.wait(tasks.values())

    return {
        "account": account,
        "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            self.get_base_return_data(
              account= self.get_cloud_client().serialize_azresource(resource= account),
              resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
              resource= item,
              region= self.get_cloud_client().get_azresource_location(resource= item),
              resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
            ),
            {
              "extra_resource": self.get_cloud_client().serialize_azresource(tasks["resource"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item))),
              "extra_availability_set": self.get_cloud_client().serialize_azresource(tasks["availability_sets"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item))),
              "extra_nics": tasks["nics"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
              "extra_load_balancers": await self._process_account_data_get_vm_load_balancers(
                vm_nics= tasks["nics"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
                load_balancers_by_nics = tasks["load_balancers"].result()
              ),
            },
          ]) for item in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.virtual_machines.list_all()
          )
        ]
    }