"""The AWS dns Action. This will pull the AWS route53"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

# dynamodb
class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="clouddb",
      logger_name= "cloud_data_client_aws_client_action_clouddb",
      *args, **kwargs)
    
    
    self.data_id_name = "Id"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "route53",
      resource_type_sub= "hostedzone", **item # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype= ["Amazon MemoryDB"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::Route53::HostedZone',
      ]
    }
  ]
    
  
  async def __hostedzones(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_hosted_zones(**item),
      boto_params={},
      boto_nextkey = "NextMarker",
      boto_nextkey_param = "Marker",
      boto_key="HostedZones"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'route53',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__hostedzones(client= client)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": [
        self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          {
            "extra_tags": {}
          }, 
          item
        ]) for item in tasks["main"].result()
        ]
    }
