from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.sqlvirtualmachine import SqlVirtualMachineManagementClient
from azure.mgmt.rdbms.mysql import MySQLManagementClient
from azure.mgmt.rdbms.mariadb import MariaDBManagementClient
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient

class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="database", 
      logger_name= "cloud_data_client_azure_client_action_database", 
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
  
  async def __process_get_db_sql(self, client, account, *args, **kwargs):    
    try:
      return_data = []
      for db in self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.managed_instances.list()
        ):
        return_data.append(
          {"extra":{
            "extra_dbtype": "sqlmi"
          }, "resource": db 
        })        
      
      for db in self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.servers.list()
        ):
        return_data.append({
          "extra":{
            "extra_dbtype": "sql",
            "extra_databases": [ self.get_cloud_client().serialize_azresource(resource= pool) for pool in self.get_cloud_client().sdk_request(
              tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
              lambda_sdk_command=lambda: client.databases.list_by_server(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= db), server_name= db.name)
              )
            ],
            "extra_elastic_pool": [ 
              self.get_common().helper_type().dictionary().merge_dictionary([
                {},
                {
                  "extra_databases": [ self.get_cloud_client().serialize_azresource(resource= pool) for pool in self.get_cloud_client().sdk_request(
                    tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
                    lambda_sdk_command=lambda: client.databases.list_by_elastic_pool(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= db), server_name= db.name, elastic_pool_name= pool.name)
                    )
                  ]
                },
                self.get_cloud_client().serialize_azresource(resource= pool)]) for pool in self.get_cloud_client().sdk_request(
              tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
              lambda_sdk_command=lambda: client.elastic_pools.list_by_server(resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= db), server_name= db.name)
              )
            ]
          }, 
          "resource": db 
        })

        return return_data



    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_db_cosmos: {err}",
        extra={
          "exception": err
        }
      )
      return []
  
  async def __process_get_db_sqlvm(self, client, account, *args, **kwargs):    
    try:

      return_data = []
      for db in self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.sql_virtual_machines.list()
        ):
        return_data.append(
          {"extra":{
            "extra_dbtype": "sqlvm"
          }, "resource": db 
        }) 
      
      return return_data


    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_db_sqlvm: {err}",
        extra={
          "exception": err
        }
      )
      return []

  async def __process_get_db_cosmos(self, client, account, *args, **kwargs):    
    try:
      # I need to look into this more but the cassandra clusters list seems to be standalone
      # client.cassandra_clusters.list_by_subscription
      return_data = []
      for db in self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.database_accounts.list()
        ):
        return_data.append(
          {"extra":{
            "extra_dbtype": "cosmosdb"
          }, "resource": db 
        }) 
      
      return return_data
    except Exception as err:
      self.get_common().get_logger().exception(
        msg= f"__process_get_db_cosmos: {err}",
        extra={
          "exception": err
        }
      )
      return []
    
  async def _process_account_data(self, account, loop, *args, **kwargs):
    # database categories
    # https://azure.microsoft.com/en-us/products/category/databases/

    cosmosdb_client = CosmosDBManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    sql_client = SqlManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    sqlvm_client = SqlVirtualMachineManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    mysql_client = MySQLManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    mariadb_client = MariaDBManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    postgres_client = PostgreSQLManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    
    tasks = {
       "cosmosdb_client": loop.create_task(self.__process_get_db_cosmos(client= cosmosdb_client,account= account)),
       "sql_client": loop.create_task(self.__process_get_db_sql(client= sql_client,account= account)),
       "sqlvm_client": loop.create_task(self.__process_get_db_sqlvm(client= sqlvm_client,account= account)),
       "mysql_client": loop.create_task(self.__process_get_db_cosmos(client= cosmosdb_client,account= account)),
       "mariadb_client": loop.create_task(self.__process_get_db_cosmos(client= cosmosdb_client,account= account)),
       "postgres_client": loop.create_task(self.__process_get_db_cosmos(client= cosmosdb_client,account= account)),
    }

    return {
        "account": account,
        "data": [
          #  self.get_common().helper_type().dictionary().merge_dictionary([
          #   {},
          #   self.get_base_return_data(
          #     account= self.get_cloud_client().serialize_azresource(resource= account),
          #     resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
          #     resource= item,
          #     region= self.get_cloud_client().get_azresource_location(resource= item),
          #     resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
          #   ),
          #   {
          #     "extra_resource": self.get_cloud_client().serialize_azresource(tasks["resource"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item))),
          #     "2": tasks["availability_sets"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
          #     "extra_nics": tasks["nics"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
          #     "extra_load_balancers": await self._process_account_data_get_vm_load_balancers(
          #       vm_nics= tasks["nics"].result().get(self.get_cloud_client().get_resource_id_from_resource(resource= item)),
          #       load_balancers_by_nics = tasks["load_balancers"].result()
          #     ),
          #   },
          # ]) for item in self.get_cloud_client().sdk_request(
          #  tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          #  lambda_sdk_command=lambda: client.virtual_machines.list_all()
          # )
        ]
    }