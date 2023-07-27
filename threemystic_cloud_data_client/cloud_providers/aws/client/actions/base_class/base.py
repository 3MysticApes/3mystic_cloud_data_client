from threemystic_cloud_data_client.cloud_providers.base_class.base_data import cloud_data_client_provider_base_data as base
from abc import abstractmethod
import asyncio

class cloud_data_client_aws_client_action_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "aws", *args, **kwargs)

  @property
  def skip_global_region(self, *args, **kwargs):
    if hasattr(self, "_skip_global_region"):
      return self._skip_global_region
    
    return True
  
  @skip_global_region.setter
  def skip_global_region(self, value, *args, **kwargs):
    self._skip_global_region = value

  @property
  def override_global_region(self, *args, **kwargs):
    if hasattr(self, "_override_global_region"):
      return self._override_global_region
    
    return None
  
  @override_global_region.setter
  def override_global_region(self, value, *args, **kwargs):
    self._override_global_region = value

  @property
  def auto_region_resourcebytype(self, *args, **kwargs):
    if hasattr(self, "_auto_region_resourcebytype"):
      return self._auto_region_resourcebytype
    
    return []
  
  @auto_region_resourcebytype.setter
  def auto_region_resourcebytype(self, value, *args, **kwargs):
    self._auto_region_resourcebytype = value

  @property  
  def resource_group_filter(self, *args, **kwargs):
    if hasattr(self, "_resource_group_filter"):
      return self._resource_group_filter
    
    return []
  
  @resource_group_filter.setter
  def resource_group_filter(self, value, *args, **kwargs):
    self._resource_group_filter = value
  
  @property
  def arn_lambda(self, *args, **kwargs):
    if hasattr(self, "_arn_lambda"):
      return self._arn_lambda
    
    return lambda item: None
  
  @arn_lambda.setter
  def arn_lambda(self, value, *args, **kwargs):
    self._arn_lambda = value
  
  @property
  def data_id_name(self):
    if hasattr(self, "_data_id_name"):
      return self._data_id_name
    
    return None
  
  @data_id_name.setter
  def data_id_name(self, value):
    self._data_id_name = value

  def get_accounts(self, *args, **kwargs):

    return self.get_cloud_client().get_accounts()
  
  @abstractmethod
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    pass
  
  async def _process_account_region(self, account, region, loop, *args, **kwargs):
    resource_groups = self.__process_account_region_rg(account= account, region= region, loop= loop)
    return await self._process_account_data_region(
      account= account,
      region= region,
      resource_groups= resource_groups if resource_groups is not None else {}, 
      loop= loop,
      **kwargs
    )

  def __process_account_region_rg(self, account, region, loop, *args, **kwargs):
    rg_client = self.get_cloud_client().get_boto_client(
        client= "resource-groups",
        account= account,
        region= region
    )

    resource_groups_by_resource = {}
    
    if self.resource_group_filter is None:
      return resource_groups_by_resource
    
    if len(self.resource_group_filter) < 1:
      return resource_groups_by_resource

    resource_groups = self.get_cloud_client().get_resource_groups(account=account, region=region, rg_client=rg_client)
    
    if len(resource_groups) > 0:
      for filter_item in self.resource_group_filter:
        for resource_id, groups in self.get_cloud_client().get_resource_group_from_resource(account=account, region=region, rg_client=rg_client, resource_groups=resource_groups, filters_resource=[filter_item]).items():
          resource_id = resource_id.lower()
          if resource_id not in resource_groups_by_resource:
            resource_groups_by_resource[resource_id] = groups
            continue

          resource_groups_by_resource[resource_id] += groups
      
      return resource_groups_by_resource

  async def _process_account_data(self, account, loop, *args, **kwargs):

    regions = self.get_cloud_client().get_accounts_regions_costexplorer(
      accounts= [account],
      services= self.auto_region_resourcebytype
    ) if self.auto_region_resourcebytype is not None else {self.get_cloud_client().get_account_id(account= account): []}

    return_data = {
      "account": account,
      "data": [  ]
    }
    if self.get_cloud_client().get_account_id(account= account) not in regions:
      return return_data

    region_tasks = []
    # if self.override_global_region

    for region_key, region in regions[self.get_cloud_client().get_account_id(account= account)].items():
      if region_key == "global" and self.skip_global_region:
        continue
      
      if self.get_common().helper_type().string().is_null_or_whitespace(string_value= self.override_global_region):
        region_tasks.append(loop.create_task(self._process_account_region(account=account, region=region, loop=loop, **kwargs)))
        continue
      
      if region_key != "global":
        region_tasks.append(loop.create_task(self._process_account_region(account=account, region=region, loop=loop, **kwargs)))
        continue

      if self.get_common().helper_type().string().set_case(string_value= self.override_global_region, case= "lower") in regions[self.get_cloud_client().get_account_id(account= account)]:
        continue

      region_tasks.append(loop.create_task(self._process_account_region(account=account, region= self.override_global_region, loop=loop, **kwargs)))


    if len(region_tasks)>0:
      await asyncio.wait(region_tasks)
    
    for region_task in region_tasks:
      if region_task.result() is None:
        continue

      for item in region_task.result().get("data"):
        resource_arn = self.arn_lambda(
          {
            "region": region_task.result().get("region"),
            "account_id": self.get_cloud_client().get_account_id(account= account),
            "resource_id": item.get(self.data_id_name),
            "raw_item": item
          }
        )
        return_data["data"].append(
          self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            await self.get_base_return_data(
              account= account,
              resource_id= resource_arn,
              resource= item,
              region= region_task.result().get("region"),
              resource_groups= region_task.result().get("resource_groups").get(resource_arn) if region_task.result().get("resource_groups").get(resource_arn) is not None else [],
            ),
            {
              "extra_id_only": item.get(self.data_id_name)
            }
          ])
        )
    return return_data
