from threemystic_cloud_data_client.cli.actions.base_class.base import cloud_data_client_action_base as base


class cloud_data_client_config(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)


  def _process_provider_aws(self, *args, **kwargs):
      from threemystic_cloud_data_client.cloud_providers.aws  import cloud_client_aws as client
      client(common= self._cloud_client).action_config()


  def _process_provider_azure(self, *args, **kwargs):
      from threemystic_cloud_client.cloud_providers.azure import cloud_client_azure as client
      client(common= self._cloud_client).action_config()

      

  
