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
    
    
    self.data_id_name = "TableArn"
    
    self.arn_lambda = (lambda item: item["raw_item"][self.data_id_name])
    
    self.auto_region_resourcebytype= ["Amazon DynamoDB"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::DynamoDB::Table',
        'AWS::DynamoDB::GlobalTable',
      ]
    }
  ]
  
  async def __dynamodb_tables_ddb_autoscale(self, client, table_name, *args, **kwargs):
    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_scaling_policies(**item),
      boto_params={
        "ServiceNamespace": 'dynamodb',
        "ResourceId": f'table/{table_name}'
      },
      boto_nextkey = "NextToken",
      boto_key="ScalingPolicies"
    )

  async def __dynamodb_tables_tags(self, client, table_arn, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_tags_of_resource(**item),
      boto_params={"ResourceArn": table_arn},
      boto_nextkey = "NextToken",
      boto_key="Tags"
    ) 

  async def __dynamodb_tables_describe(self, client, table_name, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_table(**item),
      boto_params={"TableName": table_name},
      boto_nextkey = None,
      boto_key="Table"
    ) 
  
  async def __dynamodb_tables(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_tables(**item) if item is not None and len(item) > 0 else client.list_tables(),
      boto_params={},
      boto_nextkey = "LastEvaluatedTableName",
      boto_nextkey_param = "ExclusiveStartTableName",
      boto_key="TableNames"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'dynamodb',  account=account, region=region)
    app_client = self.get_cloud_client().get_boto_client(client= 'application-autoscaling',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__dynamodb_tables(client= client)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return_data = []
    for table_name in tasks["main"].result():
      table_details = await self.__dynamodb_tables_describe(
        client= client,
        table_name= table_name
      )
      return_data.append(
        self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          {
            "extra_tags": await self.__dynamodb_tables_tags(
              client= client,
              table_arn= table_details[self.data_id_name]
            ),
            "extra_scaling_policies": await self.__dynamodb_tables_ddb_autoscale(
              client= client,
              table_name= table_name
            )
          },
          table_details
        ])
      )
    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": return_data
    }
