from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.redis import RedisManagementClient


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="memorydb", 
      logger_name= "cloud_data_client_azure_client_action_memorydb",
      *args, **kwargs)
  
 
  async def _process_account_data(self, account, loop, *args, **kwargs):
    
    client = RedisManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    
    return {
        "account": account,
        "data": [
           self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            await self.get_base_return_data(
              account= self.get_cloud_client().serialize_resource(resource= account),
              resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
              resource= item,
              region= self.get_cloud_client().get_resource_location(resource= item),
              resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
            ),
            {
              
            },
          ]) for item in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.redis.list_by_subscription()
          )
        ]
    }