from threemystic_cloud_data_client.cloud_providers.aws.base_class.base import cloud_client_provider_aws_base as base


class cloud_data_client_aws(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_aws", *args, **kwargs)
  
  # There is not post init when in Config Mode
  def _post_init(self, *args, **kwargs):
    pass
  



  
    
    
  
