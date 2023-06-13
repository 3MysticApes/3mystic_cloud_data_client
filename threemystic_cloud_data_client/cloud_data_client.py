from threemystic_cloud_data_client.base_class.base import base


class cloud_data_client(base): 
  """This is a library to help with the interaction with the cloud providers"""

  def __init__(self, logger = None, common = None, *args, **kwargs) -> None: 
    super().__init__(common= common, cloud_client = None, logger_name= "cloud_data_client", logger= logger, *args, **kwargs)
    
  def version(self, *args, **kwargs):
    if hasattr(self, "_version"):
      return self._version
    import threemystic_cloud_data_client.__version__ as __version__
    self._version = __version__.__version__
    return self.version()
    
  def get_supported_providers(self, *args, **kwargs):
    return ["aws", "azure"]
  
  def get_cloud_client(self, *args, **kwargs):
    if hasattr(self, "_cloud_client"):
      return self._cloud_client
    
    from threemystic_cloud_client.cloud_client import cloud_client
    self._cloud_client = cloud_client(logger= self.get_logger(), common= self.get_common())
    return self.get_cloud_client()

  