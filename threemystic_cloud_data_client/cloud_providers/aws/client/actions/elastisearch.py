"""The AWS dns Action. This will pull the AWS route53"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

# dynamodb
class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="elastisearch",
      logger_name= "cloud_data_client_aws_client_action_elastisearch",
      *args, **kwargs)
    
    
    self.data_id_name = "ARN"
    
    self.arn_lambda = (lambda item: item["raw_item"][self.data_id_name])
    
    self.auto_region_resourcebytype= ["Amazon Elasticsearch Service"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::OpenSearchService::Domain',
      ]
    }
  ]
  
  async def __domainnames_tags(self, client, domain, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda: client.list_tags(ARN=domain.get(self.data_id_name)),
      boto_params= None,
      boto_nextkey = None,
      boto_key="TagList"
    )
  
  async def __domainnames_describe(self, client, domains_configuration, domain_chunked, *args, **kwargs):

    for domain in self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: client.describe_domains(**item),
        boto_params= {"DomainNames": [domain_name.get("DomainName") for domain_name in domain_chunked]},
        boto_nextkey = None,
        boto_key="DomainStatusList"
      ):
      domains_configuration[domain["DomainName"]] = domain
  
  async def __domainnames(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_domain_names(**item),
      boto_params= None,
      boto_nextkey = None,
      boto_key="DomainNames"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'opensearch',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__domainnames(client= client)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())
    
    domains_configuration = {}
    for domain_chunked in self.get_common().helper_type().list().array_chucked(tasks["main"].result(), 5):
      await self.__domainnames_describe(
        client= client,
        domains_configuration= domains_configuration,
        domain_chunked= domain_chunked
      )

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": [
        self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          {
            "extra_data":{"tags": await self.__domainnames_tags(client= client, domain= item)}
          }, 
          item
        ]) for item in tasks["main"].result()
        ]
    }
