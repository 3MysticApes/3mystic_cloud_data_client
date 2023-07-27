"""The AWS dns Action. This will pull the AWS route53"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="datawarehouse",
      logger_name= "cloud_data_client_aws_client_action_datawarehouse",
      *args, **kwargs)
    
    
    self.data_id_name = "ClusterIdentifier"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "redshift",
      resource_type_sub= "cluster", **item # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype= ["Amazon Redshift"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::Redshift::Cluster',
        'AWS::Redshift::ClusterParameterGroup',
        'AWS::Redshift::ClusterSecurityGroup',
        'AWS::Redshift::ClusterSecurityGroupIngress',
        'AWS::Redshift::ClusterSubnetGroup'
      ]
    },
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::Redshift::EndpointAccess',
        'AWS::Redshift::EndpointAuthorization',
        'AWS::Redshift::EventSubscription',
        'AWS::Redshift::ScheduledAction',
      ]
    }
  ]
    
  
  async def __redshift(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_clusters(**item),
      boto_params={},
      boto_nextkey = "Marker",
      boto_key="Clusters"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'redshift',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__redshift(client= client)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": tasks["main"].result()
    }
