"""The AWS dns Action. This will pull the AWS route53"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from botocore.exceptions import ClientError


class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="cloudstorage",
      logger_name= "cloud_data_client_aws_client_action_cloudstorage",
      *args, **kwargs)
    
    
    self.data_id_name = "Name"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "s3",
      resource_type_sub= "",
      region = "",
      account_id = item["account_id"],
      resource_id = item["resource_id"] # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype = None
    self.account_region_override = {"us-east-1": "us-east-1"}
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::S3::Bucket',
      ]
    }
  ]
    
  async def __s3_list_buckets_details_tagging(self, client, bucket_name, *args, **kwargs):

    try:
      return self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: client.get_bucket_tagging(**item),
        boto_params={"Bucket": bucket_name},
        boto_nextkey = None,
        boto_key="TagSet",
        error_codes_return=["NoSuchTagSet"],
        error_codes_raise=["NoSuchBucket", "AccessDenied", "accessdeniedexception"]
      )
    except ClientError as error:
      return []
    
  async def __s3_list_buckets_details_version(self, client, bucket_name, *args, **kwargs):

    try:
      versioning = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: client.get_bucket_versioning(**item),
        boto_params={"Bucket": bucket_name},
        boto_nextkey = None,
        boto_key=lambda item: ["Disabled"] if item.get("ResponseMetadata") is not None and item["ResponseMetadata"].get("HTTPStatusCode") == 200 else [item['Status']],
        error_codes_raise=["NoSuchBucket", "AccessDenied", "accessdeniedexception"]
      )
    except ClientError as error:
      if error.response['Error']['Code'] == 'NoSuchBucket':
        return "NoSuchBucket"
      else:
        return "AccessDenied"
    

    
    if len(versioning) < 1:
      return "None"

    return versioning[0]
    
  async def __s3_list_buckets_details_encryption_rules(self, client, bucket_name, *args, **kwargs):
    try:
      return self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: client.get_bucket_encryption(**item),
        boto_params={"Bucket": bucket_name},
        boto_nextkey = None,
        boto_key=lambda item: item["ServerSideEncryptionConfiguration"].get("Rules") if item.get("ServerSideEncryptionConfiguration") is not None else [],
        error_codes_raise=["NoSuchBucket", "ServerSideEncryptionConfigurationNotFoundError", "AccessDenied", "accessdeniedexception"]
      )
    except ClientError as error:
      if error.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
        return "None"
      elif error.response['Error']['Code'] == 'NoSuchBucket':
        return "NoSuchBucket"
      else:
        return "AccessDenied"
    
    
    
  async def __s3_list_buckets_details_lifecycle(self, client, bucket_name, *args, **kwargs):
    try:
      lifecycle_config = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: client.get_bucket_lifecycle_configuration(**item),
        boto_params={"Bucket": bucket_name},
        boto_nextkey = None,
        boto_key="Rules",
        error_codes_raise=["NoSuchLifecycleConfiguration", "NoSuchBucket", "AccessDenied"]
      )
    except ClientError as error:
      if error.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
        return ['STANDARD', 'Forever']
      elif error.response['Error']['Code'] == 'NoSuchBucket':
        return ['NoSuchBucket', 'BucketNameError']
      elif error.response['Error']['Code'] == 'AccessDenied':
        return ['AccessDenied', 'AccessPolicyError']
      else:
        raise error

    for r in lifecycle_config:
      #Expiration sometimes returns 'ExpiredObjectDeleteMarker' instead of 'Days'
      if 'Transitions' in r and 'Expiration' in r:
        for c in r['Transitions']:
          if 'Days' in ['Expiration']:
            return [c['StorageClass'], r['Expiration']['Days']]
          else:
            return [c['StorageClass'], 'Forever']

      elif 'Transitions' in r:
        for c in r['Transitions']:
          return [c['StorageClass'], 'Forever']
      elif 'Expiration' in r:
        if 'Days' in ['Expiration']:
          return ['STANDARD', r['Expiration']['Days']]

        else:
          return ['STANDARD', 'Forever']
      else:
        return ['STANDARD', 'Forever']

    return None
  async def __s3_list_buckets_details_size(self, client, bucket_name, *args, **kwargs):
    # https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/aws-services-cloudwatch-metrics.html
    size_24hours = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.get_metric_statistics(**item),
      boto_params={
        "Namespace": 'AWS/S3', 
        "MetricName":'BucketSizeBytes', 
        "Dimensions": [
          {'Name': 'BucketName', 'Value': bucket_name},
          {'Name': 'StorageType', 'Value': 'StandardStorage'}
        ],
        "Statistics":['Average'],
        "Period":3600,
        "StartTime":(
          (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(
            dt= self.get_data_start(),
            days= 7,
            hours= self.get_data_start().hour,
            minutes= self.get_data_start().minute,
            seconds= self.get_data_start().second,
            microseconds= self.get_data_start().microsecond
      
          )).isoformat()
        ),
        "EndTime":self.get_data_start().isoformat()
      },
      boto_nextkey = None,
      boto_key="Datapoints"
    )

    if len(size_24hours) < 1:
      return None
    
    return size_24hours

  async def __s3_list_buckets_details(self, client, cw_client, bucket_name, loop, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= bucket_name):
      return None
    
    tasks = {
      "size7days": loop.create_task(self.__s3_list_buckets_details_size(client= cw_client, bucket_name= bucket_name)),
      "lifecycle": loop.create_task(self.__s3_list_buckets_details_lifecycle(client= client, bucket_name= bucket_name)),
      "encryption_rules": loop.create_task(self.__s3_list_buckets_details_encryption_rules(client= client, bucket_name= bucket_name)),
      "version": loop.create_task(self.__s3_list_buckets_details_version(client= client, bucket_name= bucket_name)),
      "tags": loop.create_task(self.__s3_list_buckets_details_tagging(client= client, bucket_name= bucket_name)),
    }
    await asyncio.wait(tasks.values())
    return tasks
  
  async def __s3_list_buckets(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda: client.list_buckets(),
      boto_params= None,
      boto_nextkey = None,
      boto_key="Buckets"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 's3',  account=account, region=region)
    cw_client = self.get_cloud_client().get_boto_client(client= 'cloudwatch',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__s3_list_buckets(client= client)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return_data = []
    for bucket in tasks["main"].result():
      s3_details = await self.__s3_list_buckets_details(
        client= client,
        cw_client= cw_client,
        bucket_name= bucket[self.data_id_name],
        loop= loop
      )

      return_data.append(
        self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          {
            "extra_tags": s3_details["tags"].result(),
            "extra_version": s3_details["version"].result(),
            "extra_encryption_rules": s3_details["encryption_rules"].result(),
            "extra_lifecycle": s3_details["lifecycle"].result(),
            "extra_size7days": s3_details["size7days"].result()
          },
          bucket
        ])
      )
    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": return_data
    }
