"""The AWS dns Action. This will pull the AWS route53"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="dns",
      logger_name= "cloud_data_client_aws_client_action_dns",
      *args, **kwargs)
    
    
    self.data_id_name = "CertificateArn"
    
    self.arn_lambda = (lambda item: item["raw_item"][self.data_id_name])
    
    self.auto_region_resourcebytype= None # ["AWS::ACM::Certificate"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::ACM::Certificate',
      ]
    }
  ]
    
  
  async def __acm_certificates_tags(self, client, account, region, certificate_arn, *args, **kwargs):
      
      resource_list = self.get_cloud_client().general_boto_call_array(
          boto_call=lambda item: client.list_tags_for_certificate(**item),
          boto_params={"CertificateArn": certificate_arn},
          boto_nextkey = None,
          boto_key="Tags"
      )

      return resource_list
  
  async def __acm_certificates(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_certificates(**item),
      boto_params={},
      boto_nextkey = "NextToken",
      boto_key="CertificateSummaryList"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'acm',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__acm_certificates(client= client)),
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
            "extra_tags": await self.__acm_certificates_tags(client= client, account= account, region= region, certificate_arn= item[self.data_id_name])
          }, 
          item
        ]) for item in tasks["main"].result()
        ]
    }
