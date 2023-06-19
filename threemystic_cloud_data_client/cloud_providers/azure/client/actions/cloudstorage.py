from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.storage import StorageManagementClient

class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="blob", 
      logger_name= "cloud_data_client_azure_client_action_blob", 
      uniqueid_lambda = lambda: True
      *args, **kwargs)
  
  
    
  async def _process_account_data_blob_containers(self, client:StorageManagementClient, account, storage_account, **kwargs):
      try:
        resource_group= self.get_cloud_client().get_resource_group_from_resource(resource= storage_account)
        storage_account_name= self.get_cloud_client().get_resource_name_from_resource(resource= storage_account)
        return [self.get_cloud_client().serialize_azresource(resource= item) for item in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.blob_containers.list(resource_group_name= resource_group, account_name= storage_account_name)
        )]
      except:
        return []
      
  async def _process_storage_account_by_page(self, client:StorageManagementClient, account, **kwargs):
      
      process_object = []
      for _, page in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: enumerate(client.storage_accounts.list().by_page())
        ):
        for storage_account in page:
          for blob_container in await self._process_account_data_blob_containers(client= client, account= account, storage_account= storage_account):
            process_object.append({
              "container": blob_container,
              "storage_account": storage_account
            })
          process_object.append({
            "container": None,
            "storage_account": storage_account
          })
      
      return process_object

  async def _process_account_data(self, account, loop, **kwargs):

    client = StorageManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    process_object = await self._process_storage_account_by_page(client= client, account= account)
      
    return {
        "account": account,
        "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          self.get_base_return_data(
            account= self.get_cloud_client().serialize_azresource(resource= account),
            resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item.get("container") if item.get("container") is not None else item.get("storage_account")),
            resource = item.get("container"),
            region= self.get_cloud_client().get_azresource_location(resource= item.get("storage_account")),
            resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item.get("storage_account"))],
          ),
          {
            "extra_storage_account": item.get("storage_account")
          }
        ]) for item in process_object]
    }