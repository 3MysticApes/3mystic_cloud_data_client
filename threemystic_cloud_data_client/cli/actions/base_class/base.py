import sys
from abc import abstractmethod
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers


class cloud_data_client_action_base():
  def __init__(self, cloud_data_client = None, *args, **kwargs):
    self._cloud_data_client = cloud_data_client 
    if self._cloud_data_client is None:
      from threemystic_cloud_data_client.cloud_data_client import cloud_data_client
      self._cloud_data_client = cloud_data_client()
      
  def main(self, provider = None, *args, **kwargs):
    if self._cloud_data_client.get_common().helper_type().string().is_null_or_whitespace(string_value= provider):
      from threemystic_cloud_data_client.cloud_providers.general  import cloud_data_client_general as client
      client(common= self._cloud_data_client.get_common()).action_config()

      
      response = self._cloud_data_client.get_common().generate_data().generate(
        generate_data_config = {
          "provider": {
              "validation": lambda item: self._cloud_data_client.get_common().helper_type().string().trim(self._cloud_data_client.get_common().helper_type().string().set_case(string_value= item, case= "lower")) in self._cloud_data_client.get_supported_providers(),
              "messages":{
                "validation": f"Valid Provider Options: {self._cloud_data_client.get_supported_providers()}",
              },
              "conversion": lambda item: self._cloud_data_client.get_common().helper_type().string().trim(string_value= self._cloud_data_client.get_common().helper_type().string().set_case(string_value= item, case= "lower")) if item is not None else None,
              "desc": f"Which provider should we configure?\nLeave blank to exit.\nvalid options are {self._cloud_data_client.get_supported_providers()}",
              "default": None,
              "handler": generate_data_handlers.get_handler(handler= "base"),
              "optional": True
          }
        }
      )
      
      provider = self._cloud_data_client.get_common().helper_type().string().set_case(string_value= self.__get_provider(response), case= "lower")
      if self._cloud_data_client.get_common().helper_type().string().is_null_or_whitespace(string_value= provider):
        return

    if provider not in self._cloud_data_client.get_supported_providers():
      return
    
    if provider == "azure":
      self._process_provider_azure()

    
    if provider == "aws":
      self._process_provider_aws()
  
  @abstractmethod
  def _process_provider_aws(self, *args, **kwargs):
    pass

  @abstractmethod
  def _process_provider_azure(self, *args, **kwargs):
    pass

  def __get_provider(self, provider, *args, **kwargs):
    if provider is None:
      return ""

    if provider.get("provider") is not None:
      return self.__get_provider(provider= provider.get("provider"))
    
    return provider.get("formated") if provider.get("formated") is not None else ""