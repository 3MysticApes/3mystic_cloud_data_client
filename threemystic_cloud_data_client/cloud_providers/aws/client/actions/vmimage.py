from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio


class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="ami", 
      logger_name= "cloud_data_client_aws_client_action",
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
    
    self.auto_region_resourcebytype= ["Amazon Elastic Compute Cloud - Compute"]
    self.resource_group_filter = [
      {
        'Name': 'resource-type',
        'Values': [
          'AWS::EC2::Image',
        ]
      }
    ]
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "ec2",
      resource_type_sub= "image", **item # {region, account_id, resource_id}
    ))
    self.data_id_name = "ImageId"
  
  
  
  async def _process_account_data_region(self, account, region, loop, *args, **kwargs):
    pass