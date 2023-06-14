from threemystic_cloud_data_client.cloud_providers.azure.base_class.base import cloud_data_client_provider_azure_base as base


class cloud_data_client_azure_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_azure_client", *args, **kwargs)
  
