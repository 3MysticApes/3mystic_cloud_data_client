from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault.secrets import SecretClient
from azure.keyvault.keys import KeyClient
from azure.keyvault.administration import KeyVaultAccessControlClient


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="datawarehouse", 
      logger_name= "cloud_data_client_azure_client_action_datawarehouse", 
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
  
 
  async def _process_account_data(self, account, loop, *args, **kwargs):
    
    # WIP
    #  redshift/synapse
    
    return {
        "account": account,
        "data": [
          #  self.get_common().helper_type().dictionary().merge_dictionary([
          #   {},
          #   self.get_base_return_data(
          #     account= self.get_cloud_client().serialize_azresource(resource= account),
          #     resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
          #     resource= item,
          #     region= self.get_cloud_client().get_azresource_location(resource= item),
          #     resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
          #   ),
          #   {
          #     "extra_resource": self.get_cloud_client().serialize_azresource(tasks["resource"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item))),
          #     "extra_availability_set": tasks["availability_sets"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
          #     "extra_nics": tasks["nics"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
          #     "extra_load_balancers": await self._process_account_data_get_vm_load_balancers(
          #       vm_nics= tasks["nics"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
          #       load_balancers_by_nics = tasks["load_balancers"].result()
          #     ),
          #   },
          # ]) for item in self.get_cloud_client().sdk_request(
          #  tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          #  lambda_sdk_command=lambda: client.virtual_machines.list_all()
          # )
        ]
    }