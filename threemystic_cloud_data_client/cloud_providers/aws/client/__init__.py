from threemystic_cloud_cmdb.cloud_providers.base_class.base_client import cloud_cmdb_provider_base_client as base


class cloud_cmdb_aws_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "aws", logger_name= "cloud_cmdb_aws_client", *args, **kwargs)

  
