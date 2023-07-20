from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault.secrets import SecretClient
from azure.keyvault.keys import KeyClient
from azure.keyvault.administration import KeyVaultAccessControlClient


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="secrets", 
      logger_name= "cloud_data_client_azure_client_action_secrets",
      *args, **kwargs)
  
  async def __process_get_resources_key_vault_access_key(self, account, key_vault, *args, **kwargs):    
    try:
      client = KeyVaultAccessControlClient(vault_url= f'https://{key_vault}.vault.azure.net/', credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
      
      # oid = print(self.get_cloud_client().get_tenant_credential_full(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)).get("jwt").get("oid"))


      return [ key for key in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.list_properties_of_keys()
        )
      ]
           
    except Exception as err:
      return []
    
  async def __process_get_resources_key_vault_keys(self, account, key_vault, *args, **kwargs):    
    try:
      client = KeyClient(vault_url= f'https://{key_vault}.vault.azure.net/', credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
      
      return [ key for key in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.list_properties_of_keys()
        )
      ]
           
    except Exception as err:
      return []
    
  async def __process_get_resources_key_vault_secrets(self, account, key_vault, *args, **kwargs):    
    try:
      client = SecretClient(vault_url= f'https://{key_vault}.vault.azure.net/', credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    

      return [ secret for secret in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.list_properties_of_secrets()
        )
      ]
           
    except Exception as err:
      return []
    
  async def __process_get_resources_key_vaults(self, account, *args, **kwargs):    
    try:
      client = KeyVaultManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    

      return { self.get_cloud_client().get_resource_id_from_resource(resource= kv):kv for kv in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.vaults.list()
        )
      }
           
    except Exception as err:
      return {} 

  
  async def _process_account_data(self, account, loop, *args, **kwargs):
    
    # print(account)
    
    # keyvaults = await self.__process_get_resources_key_vaults(account= account)

    # for kv in keyvaults.values():
    #   print(self.get_cloud_client().serialize_resource(resource= kv))
    #   break
    
    return {
        "account": account,
        "data": [
          #  self.get_common().helper_type().dictionary().merge_dictionary([
          #   {},
          #   await self.get_base_return_data(
          #     account= self.get_cloud_client().serialize_resource(resource= account),
          #     resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
          #     resource= item,
          #     region= self.get_cloud_client().get_resource_location(resource= item),
          #     resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
          #   ),
          #   {
          #     "extra_resource": self.get_cloud_client().serialize_resource(tasks["resource"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item))),
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