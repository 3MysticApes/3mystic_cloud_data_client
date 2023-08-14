"""The AWS vm Action. This will pull the AWS EC2s"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.vmimage import cloud_data_client_aws_client_action as vmimage_data

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="storage",
      logger_name= "cloud_data_client_aws_client_action_storage",
      *args, **kwargs)
    
    
    self.data_id_name = "extra_id"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "rds" if "rds" in item["raw_item"]["attached"] else "ec2",
      resource_type_sub= "db" if "rds" in item["raw_item"]["attached"] else "volume", **item # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype= ["Amazon Elastic Compute Cloud - Compute"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::EC2::Instance',
      ]
    },
    {
        'Name': 'resource-type',
        'Values': [
            'AWS::RDS::DBInstance',
        ]
    }
  ]
    
  async def __rds_volumes(self, client, *args, **kwargs):

    return {
      "data":self.get_cloud_client().general_boto_call_array(
          boto_call=lambda item: client.describe_db_instances(**item),
          boto_params={},
          boto_nextkey = "Marker",
          boto_key="DBInstances"
      ),
      "group": self.get_cloud_client().general_boto_call_array(
          boto_call=lambda item: client.describe_db_clusters(**item),
          boto_params={},
          boto_nextkey = "Marker",
          boto_key="DBClusters"
      )
    }
  
  async def __ec2_volumes(self, client, autoscaling_client, *args, **kwargs):
    asgs = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: autoscaling_client.describe_volumes(**item),
      boto_params= {},
      boto_nextkey = "NextToken",
      boto_key="AutoScalingGroups"
    )

    
    processed_asg = {}
    for g in asgs:
        for i in g['Instances']:
            processed_asg[i['InstanceId']] = {
                "name": g["AutoScalingGroupName"],
                "primary_instance": g['Instances'][0]['InstanceId']
            }

    return {
      "data":self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: client.describe_volumes(**item),
        boto_params= {},
        boto_nextkey = "NextToken",
        boto_key="Volumes"
      ),
      "group": processed_asg
    }

  async def __rds_volumes_process(self, account, region, data_item, group, *args, **kwargs):
    cluster = self.get_common().helper_type().list().find_item(group, lambda item: self.get_common().helper_type().list().find_item(item["DBClusterMembers"], lambda item: item["DBInstanceIdentifier"] == data_item["DBInstanceIdentifier"] ) ) if group is not None else None
    cluster_primary = self.get_common().helper_type().list().find_item(cluster["DBClusterMembers"], lambda item: item["IsClusterWriter"] ) if cluster is not None else None

    extra_resource_group_arns = []

    extra_resource_group_arns.append(
    (self.get_cloud_client().get_resource_general_arn(
      resource_type= "rds",
      resource_type_sub= "db",
      region= region, account_id= self.get_cloud_client().get_account_id(account= account), resource_id= primary_instance
    ))
    )

    return {
      "data":data_item,
      "extras":{
        "extra_resource_group_arns": extra_resource_group_arns,
        "extra_type": data_item.get("StorageType").upper(),
        "extra_id": data_item.get("DBInstanceIdentifier"),
        "extra_name": data_item.get("DBName"),
        "extra_size": data_item.get("AllocatedStorage"),
        "extra_encrypted": data_item.get("StorageEncrypted"),
        "extra_attached": ["rds"],
        "extra_group_type": "dbcluster" if cluster is not None else None,
        "extra_group": cluster.get("DBClusterIdentifier") if cluster is not None else None,
        "extra_group_primary": cluster_primary.get("DBInstanceIdentifier") == data_item.get("DBInstanceIdentifier") if cluster is not None else None,
        "extra_tags": data_item["TagList"]
      }    
    }
  
  def __ec2_volumes_process_attached(self, data_item, force_id_lower = False, *args, **kwargs):
    if not force_id_lower:
        return [ attached["InstanceId"] for attached in data_item["Attachments"] ] if data_item.get("Attachments") is not None else None
    
    return [ attached["InstanceId"].lower() for attached in data_item["Attachments"] ] if data_item.get("Attachments") is not None else None
  
  async def __ec2_volumes_process(self, account, region, data_item, group, *args, **kwargs):
    asg_name = None
    primary_instance = None
    if group is not None:
        for attachment in data_item["Attachments"]:
            if attachment["InstanceId"] in group:
                asg_name = group[attachment["InstanceId"]]["name"]
                primary_instance = group[attachment["InstanceId"]]["primary_instance"]
                break

    storage_name = self.get_common().helper_type().list().find_item(data_item["Tags"], lambda item: item["Key"].lower() == "name") if data_item.get("Tags") is not None else None
    extra_resource_group_arns = []
    if primary_instance is not None:
       extra_resource_group_arns.append(
        (self.get_cloud_client().get_resource_general_arn(
          resource_type= "ec2",
          resource_type_sub= "instance",
          region= region, account_id= self.get_cloud_client().get_account_id(account= account), resource_id= primary_instance
        ))
       )
    if data_item.get("Attachments") is not None:
      for attachment in data_item["Attachments"]:
         if attachment.get("InstanceId") is None:
            continue
         extra_resource_group_arns.append(
            (self.get_cloud_client().get_resource_general_arn(
              resource_type= "ec2",
              resource_type_sub= "instance",
              region= region, account_id= self.get_cloud_client().get_account_id(account= account), resource_id= attachment.get("InstanceId")
            ))
          )

    return {
      "data":data_item,
      "extras":{
        "extra_resource_group_arns": extra_resource_group_arns,
        "extra_type": data_item.get("VolumeType").upper(),
        "extra_id": data_item.get("VolumeId"),
        "extra_name": storage_name["Value"] if storage_name is not None and storage_name.get("Value") is not None else None,
        "extra_size": data_item.get("Size"),
        "extra_encrypted": data_item.get("Encrypted"),
        "extra_attached": self.__ec2_volumes_process_attached(data_item= data_item),
        "extra_group_type": "asg" if not self.get_common().helper_type().string().is_null_or_whitespace(asg_name) else None,
        "extra_group": asg_name if not self.get_common().helper_type().string().is_null_or_whitespace(asg_name) else None,
        "extra_group_primary": primary_instance in [ attachment['InstanceId'] for attachment in data_item["Attachments"]  ] if not self.get_common().helper_type().string().is_null_or_whitespace(asg_name) and data_item.get("Attachments") is not None else None, 
        "extra_tags": data_item.get("Tags")
      }      
    }
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(
      client= "ec2",
      account= account,
      region= region
    )
    autoscaling_client = self.get_cloud_client().get_boto_client(
      client= "autoscaling",
      account= account,
      region= region
    )
    autoscaling_client = self.get_cloud_client().get_boto_client(
      client= "rds",
      account= account,
      region= region
    )

    tasks = {
      "ec2": loop.create_task(self.__ec2_volumes(client= client, autoscaling_client= autoscaling_client)),
      "rds": loop.create_task(self.__rds_volumes(client= client)),
    }
    tasks_data_function = { 
      "ec2": self.__ec2_volumes_process,
      "rds": self.__rds_volumes_process,
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return_data = []
    for item, vals in tasks.items():
      for data in vals.result()["data"] if vals.result().get("data") is not None else vals.result():
         if tasks_data_function.get(item) is None:
            continue
         details = await tasks_data_function[item](
            account= account, region= region,
            data_item= data, 
            group= vals.result().get("group"),
         )

         return_data.append(
          self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            details["extras"],
            details["data"]
          ])
        )
    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": return_data
    }