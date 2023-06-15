from threemystic_cloud_data_client.cloud_providers.base_class.base_data import cloud_data_client_provider_base_data as base

class cloud_data_client_azure_client_action_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "azure", *args, **kwargs)  

  def get_accounts(self, *args, **kwargs):
    # return [ account for account in self.get_cloud_client().get_accounts() ]
    return [ account for account in self.get_cloud_client().get_accounts() if account.resource_container ]