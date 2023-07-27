"""The AWS vm Action. This will pull the AWS EC2s"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="database",
      logger_name= "cloud_data_client_aws_client_action_database",
      *args, **kwargs)
    
    
    self.data_id_name = "DBInstanceIdentifier"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "rds",
      resource_type_sub= "db", **item # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype= ["Amazon Relational Database Service"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::RDS::DBCluster',
      ]
    },
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::RDS::DBInstance',
      ]
    }
  ]
    
  
  async def __clusters(self, client, *args, **kwargs):

    db_clusters = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_db_clusters(**item),
      boto_params={},
      boto_nextkey = "Marker",
      boto_key="DBClusters"
    )

    cluster_search = {}
    db_clusters_byid = {}
    for cluster in db_clusters:
      db_clusters_byid[cluster["DBClusterIdentifier"]] = self.get_common().helper_type().dictionary().merge_dictionary(
        [
          {"extra_tags":  self.get_cloud_client().get_resource_tags_as_dictionary(resource= cluster)}, 
          cluster
        ]
      )
      
      if cluster.get("DBClusterMembers") is None:
        continue

      if len(cluster.get("DBClusterMembers")) < 1:
        continue

      for member in cluster.get("DBClusterMembers"):
        cluster_search[member["DBInstanceIdentifier"]] = cluster["DBClusterIdentifier"]
    
    return {
      "clusters": db_clusters_byid,
      "cluster_dbmembers": cluster_search
    }
  
  async def __get_databases(self, client, *args, **kwargs):
    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_db_instances(**item),
      boto_params={},
      boto_nextkey = "Marker",
      boto_key="DBInstances"
    ) 
  
  def __get_maintenance_key(self, ResourceIdentifier, *args, **kwargs):
    resource_identifier_split = ResourceIdentifier.split(":")

    return f"{resource_identifier_split[-2]}:{resource_identifier_split[-1]}"
  
  def __get_cluster_data_db(self, clusters, db, *args, **kwargs):
    if not db["DBInstanceIdentifier"] in clusters["cluster_dbmembers"]:
      return None
    
    return clusters["clusters"][clusters["cluster_dbmembers"][db["DBInstanceIdentifier"]]]
  
  async def __get_maintenance_actions(self, client, *args, **kwargs):
    pending_maintenance_actions = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_pending_maintenance_actions(**item),
      boto_params={},
      boto_nextkey = "Marker",
      boto_key="PendingMaintenanceActions"
    )

    pending_maintenance_actions_db = {}
    for action in pending_maintenance_actions:
      action_key = self.__get_maintenance_key(action["ResourceIdentifier"])
      if pending_maintenance_actions_db.get(action_key) is None:
        pending_maintenance_actions_db[action_key] = []

      pending_maintenance_actions_db[action_key].append(action)
    
    return pending_maintenance_actions_db
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'rds',  account=account, region=region)

    tasks = {
      "clusters": loop.create_task(self.__clusters(client= client)),
      "databases": loop.create_task(self.__get_databases(client= client)),
      "pending_maintenance_actions": loop.create_task(self.__get_maintenance_actions(client= client)),
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
          "extra_cluster": self.__get_cluster_data_db(clusters= tasks["clusters"].result(), db= item),
          "extra_pending_maintenance_actions": tasks["pending_maintenance_actions"].result().get(item["DBInstanceIdentifier"]),
          },
          item
        ]) for item in tasks["databases"].result()
      ]
    }
