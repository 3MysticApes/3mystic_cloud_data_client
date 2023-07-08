from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.synapse import SynapseManagementClient


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="datawarehouse", 
      logger_name= "cloud_data_client_azure_client_action_datawarehouse", 
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
  
 
  async def _process_account_data(self, account, loop, *args, **kwargs):
    
    client = SynapseManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    
    return {
        "account": account,
        "data": [
           self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            self.get_base_return_data(
              account= self.get_cloud_client().serialize_azresource(resource= account),
              resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
              resource= item,
              region= self.get_cloud_client().get_resource_location(resource= item),
              resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
            ),
            {
              "extra_sql_pools": [
                self.get_cloud_client().serialize_azresource(resource= pool)
                for pool in client.sql_pools.list_by_workspace(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= item), workspace_name= item.name)
              ],
              "extra_big_data_pools": [
                self.get_cloud_client().serialize_azresource(resource= pool)
                for pool in client.big_data_pools.list_by_workspace(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= item), workspace_name= item.name)
              ] 
            },
          ]) for item in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.workspaces.list()
          )
        ]
    }