"""The AWS dns Action. This will pull the AWS route53"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="function",
      logger_name= "cloud_data_client_aws_client_action_function",
      *args, **kwargs)
    
    
    self.data_id_name = "FunctionArn"
    
    self.arn_lambda = (lambda item: self.__get_functionarn_noversion(function= item["raw_item"][self.data_id_name]))
    
    self.auto_region_resourcebytype= ["AWS Lambda"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::Lambda::Function',
      ]
    }
  ]

  def __get_function_filesystem_encrypted_state(self, function, efs_encrypted_state, *args, **kwargs):
    running_state = None

    if function.get("FileSystemConfigs") is None:
      return running_state
    
    if len(function["FileSystemConfigs"]):
      return running_state
    
    for fs in function["FileSystemConfigs"]:
      if running_state is not None:
        if running_state == "all" and efs_encrypted_state[fs["Arn"].lower()]:
          continue

        if running_state == "none" and efs_encrypted_state[fs["Arn"].lower()]:
          running_state = "partial"
        continue
      
      if efs_encrypted_state[fs["Arn"].lower()]:
        running_state = "all"
        continue

      running_state = "none"
            
    return running_state
  
  def __get_provisioned_concurrency(self, client, function_name, qualifier, *args, **kwargs):
    
    try:
      pc = self.get_cloud_client().general_boto_call_single(
        boto_call=lambda: client.get_provisioned_concurrency_config(
          FunctionName=function_name,
          Qualifier=qualifier),
        boto_params= None,
        boto_nextkey = None,
        boto_key= None,

      )
      return pc['RequestedProvisionedConcurrentExecutions']
    except client.exceptions.ProvisionedConcurrencyConfigNotFoundException as error:
      self.get_common().get_logger().exception(
        msg= f"No Provisioned Concurrency Config found for this function - {function_name}",
        extra= {
          "exception": error
        }
      )
      return 0

  def __get_functionarn_noversion(self, function, *args, **kwargs):
    return ":".join((function["FunctionArn"].split(":"))[:7])    
  

  async def __lambda_functions_efs_encrypted_state(self, client, *args, **kwargs):

    efs_list_all = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.describe_file_systems(**item),
      boto_params={},
      boto_nextkey = "NextMarker",
      boto_nextkey_param = "Marker",
      boto_key="FileSystems"
    )

    efs_encrypted_state = {}
    for efs in efs_list_all:
        efs_encrypted_state[efs["FileSystemArn"].lower()] = efs["Encrypted"]
    
    return efs_encrypted_state
  
  async def __lambda_functions_tags(self, client, *args, **kwargs):

    resource_list = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.get_resources(**item),
      boto_params={"ResourceTypeFilters": ['lambda']},
      boto_nextkey = "PaginationToken",
      boto_key="ResourceTagMappingList"
    )

    return {
      resource["ResourceARN"]:resource["Tags"] for resource in resource_list
    }
  
  async def __lambda_functions_versions(self, client, function_name, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_versions_by_function(**item),
      boto_params={"FunctionName": function_name},
      boto_nextkey = "NextMarker",
      boto_nextkey_param = "Marker",
      boto_key="Versions"
    )
  
  async def __lambda_functions_aliases(self, client, function_name, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_aliases(**item),
      boto_params={
        "FunctionName":function_name
      },
      boto_nextkey = "NextMarker",
      boto_nextkey_param = "Marker",
      boto_key="Aliases"
    )
  
  async def __lambda_functions_invocations(self, client, function_name, *args, **kwargs):

    datapoints = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.get_metric_statistics(**item),
      boto_params={ 
            "Namespace":'AWS/Lambda',
            "MetricName":'Invocations',
            "Dimensions":[
                {
                    'Name': 'FunctionName',
                    'Value': function_name
                }
            ],
            "StartTime": (self.get_data_start() + self.get_common().helper_type().datetime().time_delta(days= -30, dt= self.get_data_start())),
            "EndTime": self.get_data_start(),
            "Period":86400,
            "Statistics":['Sum']
        },
      boto_nextkey = "NextMarker",
      boto_nextkey_param = "Marker",
      boto_key="Aliases"
    )

    sum = 0
    for dp in datapoints:
        sum += dp['Sum']
    return sum
  
  async def __lambda_functions(self, client, *args, **kwargs):

    return self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.list_functions(**item),
      boto_params={},
      boto_nextkey = "NextMarker",
      boto_nextkey_param = "Marker",
      boto_key="Functions"
    )
    
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    client = self.get_cloud_client().get_boto_client(client= 'lambda',  account=account, region=region)
    resourcetagging_client = self.get_cloud_client().get_boto_client(client= 'resourcegroupstaggingapi',  account=account, region=region)
    efs_client = self.get_cloud_client().get_boto_client(client= 'efs',  account=account, region=region)
    cw_client = self.get_cloud_client().get_boto_client(client= 'cloudwatch',  account=account, region=region)

    tasks = {
      "main": loop.create_task(self.__lambda_functions(client= client)),
      "tags": loop.create_task(self.__lambda_functions_tags(client= resourcetagging_client)),
      "efs_encrypted_state": loop.create_task(self.__lambda_functions_efs_encrypted_state(client= efs_client)),
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return_data = []
    for function in tasks["main"].result():
      
      versions = await self.__lambda_functions_versions(
        client= client,
        function_name= function["FunctionName"]
      )
      aliases = await self.__lambda_functions_aliases(
        client= client,
        function_name= function["FunctionName"]
      )

      running_version = None
      running_version_codesha = function.get("CodeSha256")

      for version in versions:
        if version["CodeSha256"] != running_version_codesha:
          continue

        running_version = version
        break
      
      concurrency = 0
      if running_version is not None:
        concurrency = self.__get_provisioned_concurrency(
          client= client,
          function_name= function["FunctionName"],
          qualifier= running_version["Version"]
        )
      
      if concurrency == 0:
        for alias in aliases:
          if concurrency != 0:
            break
          
          concurrency = self.__get_provisioned_concurrency(
            client= client,
            function_name= function["FunctionName"],
            qualifier= alias['Name']
          )

      is_vpc_lambda = function.get('VpcConfig') is not None \
        and function['VpcConfig'].get('SubnetIds') is not None \
        and len(function['VpcConfig'].get('SubnetIds')) > 0   
      
      multi_az = True if not is_vpc_lambda else len(function['VpcConfig'].get('SubnetIds')) > 1
      if function.get('VpcConfig') != None:
        if function['VpcConfig'].get('SubnetIds') != None and len(function['VpcConfig'].get('SubnetIds')) > 1:
          multi_az = True

      return_data.append(self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        {
          "extra_tags": tasks["tags"].result().get(function[self.data_id_name]),
          "extra_efs_encrypted_state": self.__get_function_filesystem_encrypted_state(
            function= function,
            efs_encrypted_state= tasks["efs_encrypted_state"].result()
          ),
          "extra_provisioned_concurrency": concurrency,
          "extra_is_vpc_lambda": is_vpc_lambda,
          "extra_multi_az": multi_az,
          "extra_invocation_count": await self.__lambda_functions_invocations(
            client= cw_client,
            function_name= ["FunctionName"]
          ),
          "extra_running_version": running_version,
          "extra_versions": versions
        },
        function
      ]))


    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": return_data
    }
