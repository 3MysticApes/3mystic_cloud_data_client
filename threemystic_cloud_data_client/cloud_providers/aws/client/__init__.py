from threemystic_cloud_data_client.cloud_providers.aws.base_class.base import cloud_data_client_provider_aws_base as base


class cloud_data_client_aws_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_aws_client", *args, **kwargs)
  
