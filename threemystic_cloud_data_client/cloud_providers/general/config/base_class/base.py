from threemystic_cloud_data_client.cloud_providers.base_class.base import cloud_data_client_provider_base as base
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers

class cloud_data_client_general_config_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def step(self, *args, **kwargs):
    return True