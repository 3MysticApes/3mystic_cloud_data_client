from threemystic_cloud_data_client.cloud_providers.base_class.base import cloud_data_client_provider_base as base
from threemystic_cloud_client.cloud_client import cloud_client

class cloud_data_client(base): 
  """This is a library to help with the interaction with the cloud providers"""

  def __init__(self, logger = None, common = None, *args, **kwargs) -> None: 
    if "provider" not in kwargs:
      kwargs["provider"] = ""
    super().__init__(common= common, logger_name= "cloud_data_client", logger= logger, *args, **kwargs)
    
  def version(self, *args, **kwargs):
    if hasattr(self, "_version"):
      return self._version
    import threemystic_cloud_data_client.__version__ as __version__
    self._version = __version__.__version__
    return self.version()
    
  def get_supported_providers(self, *args, **kwargs):
    return super().get_supported_providers()
  
  def init_client(self, provider, refresh = False, *args, **kwargs):
    provider = self.get_common().helper_type().string().set_case(string_value= provider, case= "lower") if provider is not None else ""

    if provider not in self.get_supported_providers():
      raise self.get_common().exception().exception(
        exception_type = "argument"
      ).not_implemented(
        logger= self.get_logger(),
        name = "provider",
        message = f"Unknown Cloud Provided: {provider}.\nSupported Cloud Providers{self.get_supported_providers()}"
      )

    if not hasattr(self, "_client"):
      self._client = {}

    if self._client.get(provider) is not None and not refresh:
      return

    try:
      client = cloud_client(
        logger= self.get_logger(), 
        common= self.get_common()
      )
    except:
      client = None

    if provider == "azure":
      from threemystic_cloud_data_client.cloud_providers.azure.client import cloud_data_client_azure_client as provider_cloud_data_client
      try:
        client = client.client(provider= provider)
      except:
        client = None
      
      self._client[provider] = provider_cloud_data_client(
        cloud_data_client= self,
        cloud_client =  client,
        *args, **kwargs
      )
      return
    
    if provider == "aws":
      from threemystic_cloud_data_client.cloud_providers.aws.client import cloud_data_client_aws_client as provider_cloud_data_client
      try:
        client = client.client(provider= provider)
      except:
        client = None

      self._client[provider] = provider_cloud_data_client(
        cloud_data_client= self,
        cloud_client = client,
        *args, **kwargs
      )
      return  
       
    raise self.get_common().exception().exception(
      exception_type = "argument"
    ).not_implemented(
      logger= self.get_common().get_logger(), 
      name = "provider",
      message = f"Unknown Cloud Provided: {provider}.\nSupported Cloud Providers{self.get_supported_providers()}"
    )

  def client(self, provider = None, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= provider):
      provider = self.get_provider()
      if self.get_common().helper_type().string().is_null_or_whitespace(string_value= provider):
        provider = self.get_default_provider()
        if self.get_common().helper_type().string().is_null_or_whitespace(string_value= provider):
          raise self.get_common().exception().exception(
            exception_type = "argument"
          ).not_implemented(
            logger= self.get_common().get_logger(), 
            name = "provider",
            message = f"provider cannot be null or whitespace"
          )
  
    provider = self.get_common().helper_type().string().set_case(string_value= provider, case= "lower")
    if hasattr(self, "_client"):
      if self._client.get(provider) is not None:
        return self._client.get(provider)
    
    self.init_client(provider= provider,  *args, **kwargs)
    return self.client(provider= provider, *args, **kwargs)
    
    

  