from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.privatedns import PrivateDnsManagementClient
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.resource import ResourceManagementClient



class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="memorydb", 
      logger_name= "cloud_data_client_azure_client_action_memorydb", 
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
  
  async def __process_get_resources_public(self, client, account, *args, **kwargs):    
    try:      
      return { self.get_cloud_client().get_resource_id_from_resource(resource= dns):dns for dns in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.zones.list()
        )
      }
           
    except Exception as err:
      return {}
  
  async def __process_get_resources_public_record_sets(self, client, account, dns, *args, **kwargs):    
    try:      
      return { self.get_cloud_client().get_resource_id_from_resource(resource= dns):dns for dns in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.record_sets.list(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
        )
      }
           
    except Exception as err:
      return {}
  
  async def __process_get_resources_private_dns(self, client, account, *args, **kwargs):    
    try:      
      return { self.get_cloud_client().get_resource_id_from_resource(resource= dns):dns for dns in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.private_zones.list()
        )
      }
           
    except Exception as err:
      return {}
  
  async def __process_get_resources_private_dns_network(self, client, account, dns, *args, **kwargs):    
    try:      
      return { self.get_cloud_client().get_resource_id_from_resource(resource= dns):dns for dns in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.virtual_network_links.list(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
        )
      }
           
    except Exception as err:
      return {}
  
  async def __process_get_resources_private_dns_record_sets(self, client, account, dns, *args, **kwargs):    
    try:      
      return { self.get_cloud_client().get_resource_id_from_resource(resource= dns):dns for dns in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.record_sets.list(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
        )
      }
           
    except Exception as err:
      return {}
  
  async def __process_get_resources_resource_dns(self, account, *args, **kwargs):    
    resource_client = ResourceManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    try:
        return {self.get_cloud_client().get_resource_id_from_resource(resource= resource): resource for resource in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: resource_client.resources.list(filter="resourceType eq 'Microsoft.Network/privateDnsZones' or resourceType eq 'Microsoft.Network/dnsZones'", expand="createdTime,changedTime,provisioningState")
          )
        }
    except:
        return {}
    
  
  async def _process_account_data(self, account, loop, *args, **kwargs):
    
    privatedns_client = PrivateDnsManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    publicdns_client = DnsManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    
    tasks = {
      "resources": loop.create_tasks(self.__process_get_resources_resource_dns(account= account)),
      "privatedns": loop.create_tasks(self.__process_get_resources_private_dns(client= privatedns_client, account= account)),
      "public": loop.create_tasks(self.__process_get_resources_public(client= publicdns_client, account= account))
    }
    # WIP
    # This will be dns zones (route53, public/private DNS azure)

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