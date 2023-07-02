from threemystic_cloud_data_client.cloud_providers.base_class.base_data import cloud_data_client_provider_base_data as base

class cloud_data_client_azure_client_action_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "azure", *args, **kwargs)  

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