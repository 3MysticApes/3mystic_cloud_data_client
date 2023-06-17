from threemystic_cloud_data_client.cloud_providers.base_class.base_client import cloud_data_client_provider_base_client as base

class cloud_data_client_azure_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "azure", logger_name= "cloud_data_client_azure_client", *args, **kwargs)
    
    
  
  