from threemystic_cloud_data_client.cloud_providers.aws.base_class.base import cloud_data_client_provider_aws_base as base
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers

class cloud_data_client_aws_config_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def step(self, *args, **kwargs):    
    return self.ensure_cloud_client_config_completed()