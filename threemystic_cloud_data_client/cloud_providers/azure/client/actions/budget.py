from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="budget", 
      logger_name= "cloud_data_client_azure_client_action_budget", 
      uniqueid_lambda = lambda: True
      *args, **kwargs)
  
        
  async def _process_account_data(self, account, loop, *args, **kwargs):
   if self.get_common().helper_type().string().is_null_or_whitespace(string_value= kwargs.get("fiscal_year_start")):
     kwargs["fiscal_year_start"] = self.get_cloud_data_client().get_default_fiscal_year_start()
   return {}