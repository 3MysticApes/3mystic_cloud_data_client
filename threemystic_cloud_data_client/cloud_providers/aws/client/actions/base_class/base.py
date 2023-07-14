from threemystic_cloud_data_client.cloud_providers.base_class.base_data import cloud_data_client_provider_base_data as base
from abc import abstractmethod
import asyncio

class cloud_data_client_aws_client_action_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "aws", *args, **kwargs)  

  @property
  def auto_region_resourcebytype(self, *args, **kwargs):
    if hasattr(self, "_auto_region_resourcebytype"):
      return self._auto_region_resourcebytype
    
    return []
  
  @auto_region_resourcebytype.setter
  def _set_auto_region_resourcebytype(self, value, *args, **kwargs):
    self._auto_region_resourcebytype = value

  @property  
  def resource_group_filter(self, *args, **kwargs):
    if hasattr(self, "_resource_group_filter"):
      return self._resource_group_filter
    
    return []
  
  @resource_group_filter.setter
  def _set_resource_group_filter(self, value, *args, **kwargs):
    self._resource_group_filter = value
  
  @property
  def arn_lambda(self, *args, **kwargs):
    if hasattr(self, "_arn_lambda"):
      return self._arn_lambda
    
    return []
  
  @arn_lambda.setter
  def _set_arn_lambda(self, value, *args, **kwargs):
    self._arn_lambda = value
  
  @property
  def data_id_name(self):
    if hasattr(self, "_data_id_name"):
      return self._data_id_name
    
    return None
  
  @data_id_name.setter
  def _set_data_id_name(self, value):
    self._data_id_name = value

  def get_accounts(self, *args, **kwargs):

    if len(self.get_runparam_key(data_key= "data_accounts", default_value= [])) < 1:
      return [ 
        account for account in self.get_cloud_client().get_accounts() 
        if account.resource_container ]
    
    return [ 
        account for account in self.get_cloud_client().get_accounts() 
        if( account.resource_container and 
            self.get_cloud_client().get_account_id(account= account) in self.get_runparam_key(data_key= "data_accounts", default_value= []) and 
            not f'-{self.get_cloud_client().get_account_id(account= account)}' in self.get_runparam_key(data_key= "data_accounts", default_value= [])
          )
        ]
  
  @abstractmethod
  async def _process_account_data_region(self, account, region, loop, *args, **kwargs):
    pass

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
    for region in regions[self.get_cloud_client().get_account_id(account= account)]:
      region_tasks.append(loop.create_task(self._process_account_data_region(account=account, region=region, loop=loop, **kwargs)))

    if len(region_tasks)>0:
      await asyncio.wait(region_tasks)
    
    return return_data
    # return {
    #   "account": account,
    #   "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
    #       {},
    #       await self.get_base_return_data(
    #         account= account,
    #         resource_id= self.get_cloud_client().get_resource_id_from_resource(resource= item),
    #         resource= None,
    #         region= "",
    #         resource_groups= [],
    #       )
    #     ]) 
    #   ]
    # }