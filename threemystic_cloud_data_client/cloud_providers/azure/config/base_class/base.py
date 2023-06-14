from threemystic_cloud_data_client.cloud_providers.azure.base_class.base import cloud_data_client_provider_azure_base as base
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers

class cloud_data_client_azure_config_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def step(self, *args, **kwargs):
    return True