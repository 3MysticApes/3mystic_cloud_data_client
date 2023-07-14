from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network.models import LoadBalancer


class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="ami", 
      logger_name= "cloud_data_client_aws_client_action", 
      data_id_name= "ImageId",
      arn_lambda = lambda item: self.get_cloud_client().get_resource_general_arn(
        resource_type= "ec2",
        resource_type_sub= "image", **item # {region, account_id, resource_id}
      ),
      auto_region_resourcebytype = ["Amazon Elastic Compute Cloud - Compute"],
      resource_group_filter= [
        {
          'Name': 'resource-type',
          'Values': [
            'AWS::EC2::Image',
          ]
        }
      ],
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
  
  
  
  async def _process_account_data(self, account, loop, *args, **kwargs):
    return {
        "account": account,
        "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            await self.get_base_return_data(
              account= account,
              resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
              resource= None,
              region= "",
              resource_groups= [],
            )
          ]) 
        ]
    }