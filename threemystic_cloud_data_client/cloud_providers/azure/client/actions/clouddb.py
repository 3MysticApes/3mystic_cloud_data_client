from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.cosmosdb import CosmosDBManagementClient

class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="clouddb", 
      logger_name= "cloud_data_client_azure_client_action_clouddb",
      *args, **kwargs)
  
  async def __process_get_db_cosmosdb(self, client, account, *args, **kwargs):    
    try:
      # I need to look into this more but the cassandra clusters list seems to be standalone
      # client.cassandra_clusters.list_by_subscription
      return_data = []
      for db in self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.database_accounts.list()
        ):
        return_data.append(
          {"extra":{
            "extra_dbtype": "cosmosdb"
          }, "resource": db 
        })
      
      return return_data
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_db_cosmos: {err}",
        extra={
          "exception": err
        }
      )
      return []
    
  async def _process_account_data(self, account, loop, *args, **kwargs):
    # database categories
    # https://azure.microsoft.com/en-us/products/category/databases/

    client = CosmosDBManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))


    tasks = {
       "main": loop.create_task(self.__process_get_db_cosmosdb(client= client,account= account)),
    }

    await asyncio.wait(tasks.values())
    
    return {
      "account": account,
      "data": [
          self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          await self.get_base_return_data(
            account= self.get_cloud_client().serialize_resource(resource= account),
            resource_id= self.get_cloud_client().get_resource_id(resource= item.get("resource")),
            resource=  item.get("resource"),
            region= self.get_cloud_client().get_resource_location(resource=  item.get("resource")),
            resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource=  item.get("resource"))],
          ),
          item.get("extra"),
        ]) for item in tasks["main"].result()
      ]
    }
