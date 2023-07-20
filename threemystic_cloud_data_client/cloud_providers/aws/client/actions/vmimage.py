from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio


class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="ami", 
      logger_name= "cloud_data_client_aws_client_action",
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
    
    
    self.data_id_name = "ImageId"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "ec2",
      resource_type_sub= "image", **item # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype= ["Amazon Elastic Compute Cloud - Compute"]
    self.resource_group_filter = [
      {
        'Name': 'resource-type',
        'Values': [
          'AWS::EC2::Image',
        ]
      }
    ]
  
  
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    ec2_client = self.get_cloud_client().get_boto_client(
      client= "ec2",
      account= account,
      region= region
    )

    awsdata = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: ec2_client.describe_images(**item),
      boto_params= {"Owners": ["self"], "IncludeDeprecated": True},
      boto_nextkey = "NextToken",
      boto_key="Images"
    )

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": awsdata
    }
