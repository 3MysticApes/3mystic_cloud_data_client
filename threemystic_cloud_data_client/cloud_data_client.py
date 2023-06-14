from threemystic_common.base_class.base_provider import base


class cloud_data_client(base): 
  """This is a library to help with the interaction with the cloud providers"""

  def __init__(self, logger = None, common = None, *args, **kwargs) -> None: 
    super().__init__(provider= "", common= common, logger_name= "cloud_data_client", logger= logger, *args, **kwargs)
    
  def version(self, *args, **kwargs):
    if hasattr(self, "_version"):
      return self._version
    import threemystic_cloud_data_client.__version__ as __version__
    self._version = __version__.__version__
    return self.version()
    
  def get_supported_providers(self, *args, **kwargs):
    return super().get_supported_providers()
  
  def get_cloud_client(self, *args, **kwargs):
    if hasattr(self, "_cloud_client"):
      return self._cloud_client
    
    from threemystic_cloud_client.cloud_client import cloud_client
    self._cloud_client = cloud_client(logger= self.get_logger(), common= self.get_common())
    return self.get_cloud_client()
  
  def init_client(self, provider, *args, **kwargs):
    provider = self.get_common().helper_type().string().set_case(string_value= provider, case= "lower") if provider is not None else ""

    if provider not in self.get_supported_providers():
      raise self.get_common().exception(
        exception_type = "argument"
      ).not_implemented(
        logger = self.logger,
        name = "provider",
        message = f"Unknown Cloud Provided: {provider}.\nSupported Cloud Providers{self.get_supported_providers()}"
      )

    if not hasattr(self, "_client"):
      self._client = {}

    if self._client.get(provider) is not None:
      return

    if provider == "azure":
      return
    
    if provider == "aws":
      return  
       
    raise self.get_common().exception().exception(
      exception_type = "argument"
    ).not_implemented(
      logger = self.logger,
      name = "provider",
      message = f"Unknown Cloud Provided: {provider}.\nSupported Cloud Providers{self.get_supported_providers()}"
    )

  def client(self, provider, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= provider):
      raise self.get_common().exception().exception(
        exception_type = "argument"
      ).not_implemented(
        logger = self.logger,
        name = "provider",
        message = f"provider cannot be null or whitespace"
      )
  
    provider = self.get_common().helper_type().string().set_case(string_value= provider, case= "lower")
    if not hasattr(self, "_client"):
      self.init_client(provider= provider,  *args, **kwargs)
      return self.client(provider= provider, *args, **kwargs)
    
    return self._client.get(provider)

  