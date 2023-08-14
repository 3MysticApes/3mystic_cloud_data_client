from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import ResourceManagementClient

class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="function", 
      logger_name= "cloud_data_client_azure_client_action_function",
      *args, **kwargs)
  
  async def __process_get_resources_functions(self, client, account, *args, **kwargs):    
    try:      
      return [ resource for resource in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.resources.list(filter="resourceType eq 'Microsoft.Web/sites' and (resourceKind eq 'functionapp' or resourceKind eq 'functionapp,linux')", expand="createdTime,changedTime,provisioningState")
          )
      ]
           
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_functions: {err}",
        extra={
          "exception": err
        }
      )
      return []
    
  async def _process_account_data(self, account, loop, *args, **kwargs):
    # database categories
    # https://azure.microsoft.com/en-us/products/category/databases/

    client = WebSiteManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    resource_client = ResourceManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    
    

    tasks = {
       "main": loop.create_task(self.__process_get_resources_functions(client= client,account= account)),
    }

    await asyncio.wait(tasks.values())
    return_data = []
    for resource_function_app in tasks["main"].result():
      function_app = client.web_apps.get(
        resource_group_name= resource_function_app.resource_group,
        name= resource_function_app.name
      )
      return_data.append(self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        await self.get_base_return_data(
          account= self.get_cloud_client().serialize_resource(resource= account),
          resource_id= self.get_cloud_client().get_resource_id(resource= function_app),
          resource=  function_app,
          region= self.get_cloud_client().get_resource_location(resource=  function_app),
          resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource=  function_app)],
        ),
      ]))
    return {
      "account": account,
      "data": return_data
    }
