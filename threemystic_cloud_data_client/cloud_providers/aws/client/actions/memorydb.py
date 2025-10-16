"""The AWS database Action. This will pull the AWS rds"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

#add elasticache
class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="memorydb",
      logger_name= "cloud_data_client_aws_client_action_memorydb",
      *args, **kwargs)
    
    
    self.data_id_name = "ARN"
    
    self.arn_lambda = (lambda item: item["raw_item"][self.data_id_name])
    
    self.auto_region_resourcebytype= ["Amazon MemoryDB", "Amazon Elastic Compute Cloud - Compute", "Amazon Relational Database Service"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::MemoryDB::Cluster',
        'AWS::ElastiCache::CacheCluster'
      ]
    }
  ]
    
  
  async def __get_memorydb_tags(self, client, account, region, *args, **kwargs):
      
      resource_list = self.get_cloud_client().general_boto_call_array(
          boto_call=lambda item: client.get_resources(**item),
          boto_params={"ResourceTypeFilters": ['memorydb']},
          boto_nextkey = "PaginationToken",
          boto_key="ResourceTagMappingList"
      )

      return {
        resource["ResourceARN"].lower():resource["Tags"] for resource in resource_list
      }

  async def __get_clusters(self, client, *args, **kwargs):
    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_clusters(**item),
      boto_params={"ShowShardDetails": True},
      boto_nextkey = "NextToken",
      boto_key="Clusters"
    )
  
  async def __get_elasticache_tags(self, client, account, region, cache, *args, **kwargs):
      
    try:
      return await self.get_cloud_client().async_general_boto_call_array(
          boto_call=lambda item: client.list_tags_for_resource(**item),
          boto_params={"ResourceName": cache[self.data_id_name]},
          boto_nextkey = "Marker",
          boto_key="TagList"
      )
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"__get_elasticache_tags: {err}", extra= {"exception": err})
      return []
  
  async def __get_elasticache(self, client, *args, **kwargs):
    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_cache_clusters(**item),
      boto_params={
        "ShowCacheNodeInfo": True,
        "ShowCacheClustersNotInReplicationGroups": True
      },
      boto_nextkey = "Marker",
      boto_key="CacheClusters"
    )

  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'memorydb',  account=account, region=region)
    client_elasticache = self.get_cloud_client().get_boto_client(client= 'elasticache',  account=account, region=region)
    resourcegroupstaggingapi_client = self.get_cloud_client().get_boto_client(client= 'resourcegroupstaggingapi',  account=account, region=region)

    tasks = {
      "clusters": loop.create_task(self.__get_clusters(client= client)),
      "tags": loop.create_task(self.__get_memorydb_tags(client= resourcegroupstaggingapi_client,  account=account, region=region)),
      "elasticache": loop.create_task(self.__get_elasticache(client= client_elasticache)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    elastic_cache_data_tags_tags = {
        cache[self.data_id_name]: loop.create_task(self.__get_elasticache_tags(client= client_elasticache, cache= cache, account= account, region= region)) for cache in tasks["elasticache"].result()
    }
    if len(elastic_cache_data_tags_tags) > 0:
      await asyncio.wait(tasks.values())

    return_data = [
      self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        {
          "extra_data": {"tags": tasks["tags"].result().get(item[self.data_id_name].lower())},
          "extra_type": "memorydb"
        }, 
        item
      ]) for item in tasks["clusters"].result()
    ]

    return_data += [
      self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        {
          "extra_tags": elastic_cache_data_tags_tags[item[self.data_id_name]].result() if elastic_cache_data_tags_tags.get(item[self.data_id_name]) is not None else {},
          "extra_type": "elasticache"
        }, 
        item
      ]) for item in tasks["elasticache"].result()
    ]

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": return_data
    }
