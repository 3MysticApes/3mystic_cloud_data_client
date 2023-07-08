from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.privatedns import PrivateDnsManagementClient
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.resource import ResourceManagementClient



class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="dns", 
      logger_name= "cloud_data_client_azure_client_action_dns", 
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
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_public: {err}",
        extra={
          "exception": err
        }
      )
      return {}
  
  async def __process_get_resources_public_record_sets(self, client, account, dns, *args, **kwargs):    
    try:      
      return [ record_set for record_set in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.record_sets.list_all_by_dns_zone(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
        )
      ]
           
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_public_record_sets: {err}",
        extra={
          "exception": err
        }
      )
      return []
  
  async def __process_get_resources_private_dns(self, client, account, *args, **kwargs):    
    try:      
      return { self.get_cloud_client().get_resource_id_from_resource(resource= dns):dns for dns in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.private_zones.list()
        )
      }
           
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_private_dns: {err}",
        extra={
          "exception": err
        }
      )
      return {}
  
  async def __process_get_resources_private_dns_network(self, client, account, dns, *args, **kwargs):    
    try:      
      return [ network for network in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.virtual_network_links.list(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
        )
      ]
           
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_private_dns_network: {err}",
        extra={
          "exception": err
        }
      )
      return []
  
  async def __process_get_resources_private_dns_record_sets(self, client, account, dns, *args, **kwargs):    
    try:      
      return [ record_set for record_set in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.record_sets.list(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
        )
      ]
           
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_private_dns_record_sets: {err}",
        extra={
          "exception": err
        }
      )
      return []
  
  async def __process_get_resources_resource_dns(self, account, *args, **kwargs):    
    resource_client = ResourceManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    try:
        return {self.get_cloud_client().get_resource_id_from_resource(resource= resource): resource for resource in self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: resource_client.resources.list(filter="resourceType eq 'Microsoft.Network/privateDnsZones' or resourceType eq 'Microsoft.Network/dnsZones'", expand="createdTime,changedTime,provisioningState")
          )
        }
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_resource_dns: {err}",
        extra={
          "exception": err
        }
      )
      return {}
  
  async def __process_get_resources_dns_get(self, client_private, client_public, account, dns, value, *args, **kwargs):    
    try:

      if value is not None:
        return value
      
      if self.get_common().helper_type().string().set_case(string_value= dns.type, case= "lower") == "microsoft.network/privatednszones":
        return self.get_cloud_client().sdk_request(
            tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
            lambda_sdk_command=lambda: client_private.private_zones.get(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
          )
      
      return self.get_cloud_client().sdk_request(
            tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
            lambda_sdk_command=lambda: client_public.zones.get(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= dns), private_zone_name= dns.name)
          )
           
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_resources_dns_get: {err}",
        extra={
          "exception": err
        }
      )
      return dns
    
  
  async def _process_account_data(self, account, loop, *args, **kwargs):

    privatedns_client = PrivateDnsManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    publicdns_client = DnsManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    
    tasks = {
      "resources": loop.create_task(self.__process_get_resources_resource_dns(account= account)),
      "privatedns": loop.create_task(self.__process_get_resources_private_dns(client= privatedns_client, account= account)),
      "public": loop.create_task(self.__process_get_resources_public(client= publicdns_client, account= account))
    }

    await asyncio.wait(tasks.values())
    tasks_data = {}

    for id, dns in tasks["resources"].result().items():
      resource_type = self.get_common().helper_type().string().set_case(string_value= dns.type, case= "lower")
      
      tasks_data[f'{id};item'] = loop.create_task(self.__process_get_resources_dns_get(
        client_private= privatedns_client,
        client_public= publicdns_client,
        account= account,
        dns= dns,
        value= tasks["privatedns"].result().get(id) if resource_type == "microsoft.network/privatednszones" else tasks["public"].result().get(id)
      ))
      
      if resource_type == "microsoft.network/privatednszones":
        tasks_data[f'{id};record_sets'] = loop.create_task(self.__process_get_resources_private_dns_record_sets(
          client= privatedns_client,
          account= account,
          dns= dns
        ))
        tasks_data[f'{id};network'] = loop.create_task(self.__process_get_resources_private_dns_network(
          client= privatedns_client,
          account= account,
          dns= dns
        ))
        continue
        
      tasks_data[f'{id};record_sets'] = loop.create_task(self.__process_get_resources_public_record_sets(
        client= publicdns_client,
        account= account,
        dns= dns
      ))
    
    if len(tasks_data) > 0:
      await asyncio.wait(tasks_data.values())

    return {
      "account": account,
      "data": [
          self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          self.get_base_return_data(
            account= self.get_cloud_client().serialize_azresource(resource= account),
            resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= tasks_data[f'{id};item'].result()),
            resource= tasks_data[f'{id};item'].result(),
            region= self.get_cloud_client().get_resource_location(resource= tasks_data[f'{id};item'].result()),
            resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= tasks_data[f'{id};item'].result())],
          ),
          {
            "extra_record_sets": [ self.get_cloud_client().serialize_azresource(resource= zone) for zone in tasks_data[f'{id};record_sets'].result() ] if tasks_data[f'{id};record_sets'].result() is not None else None,
            "extra_vnet_link": [ self.get_cloud_client().serialize_azresource(resource= link) for link in tasks_data[f'{id};network'].result() ] if self.get_common().helper_type().string().set_case(string_value= raw_resource.type, case= "lower") == "microsoft.network/privatednszones" and tasks_data[f'{id};network'].result() is not None else None,
          },
        ]) for id, raw_resource in tasks["resources"].result().items()
      ]
    }