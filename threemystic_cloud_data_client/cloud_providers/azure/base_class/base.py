from threemystic_cloud_client.cloud_providers.base_class.base import cloud_client_provider_base as base

class cloud_data_client_provider_aws_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "azure", *args, **kwargs)  
