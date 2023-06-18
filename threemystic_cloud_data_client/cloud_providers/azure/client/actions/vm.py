from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="vm", 
      logger_name= "cloud_data_client_azure_client_action_vm", 
      uniqueid_lambda = lambda: True
      *args, **kwargs)
  
  
    
  async def __process_get_resources_vm(self, account, *args, **kwargs):
    resource_client = ResourceManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    try:
        return {resource.id: resource for resource in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: resource_client.resources.list(filter="resourceType eq 'Microsoft.Compute/virtualMachines'", expand="createdTime,changedTime,provisioningState")
          )
        }
    except:
        return []
        
  async def _process_account_data(self, account, loop, *args, **kwargs):
    client = ComputeManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    tasks = {
        "resource": loop.create_task(self.__process_get_resources_vm(account= account))
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
          {"extra_resource": self.common.serialize_azresource(tasks["resource"].result().get(item.id))},]) for item in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.virtual_machines.list_all()
          )
        ]
    }