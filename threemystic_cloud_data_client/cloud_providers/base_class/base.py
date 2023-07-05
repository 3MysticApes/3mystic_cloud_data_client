from threemystic_common.base_class.base_provider import base
from threemystic_cloud_data_client.cli import cloud_data_client_cli
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers
from threemystic_cloud_client.cloud_providers.aws import cloud_client_aws as aws_client
from threemystic_cloud_client.cloud_providers.azure import cloud_client_azure as azure_client

class cloud_data_client_provider_base(base):
  def __init__(self, *args, **kwargs):
    if "provider" not in kwargs:
      kwargs["provider"] = self.get_default_provider()
    super().__init__(*args, **kwargs)
    
  def _setup_another_config(self):
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "repeat_config": {
            "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
            "messages":{
              "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
            },
            "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
            "desc": f"Do you want to setup another provider?: {self.get_common().helper_type().bool().is_true_values()}",
            "default": None,
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": True
        }
      }
    )

    if response is None:
      return
    
    if response.get("repeat_config") is None:
      return
    
    if response.get("repeat_config").get("formated") is not True:
      return
    
    print()
    print()
    print("-------------------------------------------------------------------------")
    print()
    print()

    cloud_data_client_cli().process_client_action("config")

  def update_provider_config_completed(self, status, *args, **kwargs):
    self.get_config()["_config_process"] = status
    self._save_config()
  
  def is_cloud_client_config_completed(self, *args, **kwargs):
    cloud_client = None
    if self.get_provider() == "azure":
      cloud_client = azure_client( common= self.get_common(), logger= self.get_common().get_logger())
    if self.get_provider() == "aws":
      cloud_client = aws_client( common= self.get_common(), logger= self.get_common().get_logger())
    
    if cloud_client is not None:
      return cloud_client.is_provider_config_completed()

    return False
  
  def ensure_cloud_client_config_completed(self, *args, **kwargs):
    if self.is_cloud_client_config_completed():
      return True
    cloud_client = None
    if self.get_provider() == "azure":
      cloud_client = azure_client( common= self.get_common(), logger= self.get_common().get_logger())
    if self.get_provider() == "aws":
      cloud_client = aws_client( common= self.get_common(), logger= self.get_common().get_logger())
    
    if cloud_client is not None:
      cloud_client._setup_another_config()
    
    return False

    
  
  def is_provider_config_completed(self, *args, **kwargs):
    return self.get_config().get("_config_process") is True and self.is_cloud_client_config_completed()
  
  def get_main_directory_name(self, *args, **kwargs):
    return "data_client"  

  def __load_config(self, *args, **kwargs):
    config_data = self.get_common().helper_config().load(
      path= self.config_path(),
      config_type= "yaml"
    )
    if config_data is not None:
      return config_data
    
    return {}

  def config_path(self, *args, **kwargs):
    return self.get_common().get_threemystic_directory_config().joinpath(f"{self.get_main_directory_name()}/config")
  
  def get_config(self, refresh = False, *args, **kwargs):
    if hasattr(self, "_config_data") and not refresh:
      return self._config_data
    
    self._config_data = self.__load_config()    
    return self.get_config(*args, **kwargs)

  def _update_config(self,config_key, config_value, refresh= False,  *args, **kwargs):
     self.get_config(refresh = True)[config_key] = config_value
     
  def _save_config(self, *args, **kwargs):
     if not self.config_path().parent.exists():
       self.config_path().parent.mkdir(parents= True)
     self.config_path().write_text(
      data= self.get_common().helper_yaml().dumps(data= self.get_config())
     )
     self.get_config(refresh = True) 
  
  def get_config_value(self, config_key, default_if_none = None, refresh = False, *args, **kwargs):
    config_value = self.get_config(refresh= refresh).get(config_key)
    if config_value is not None:
      return config_value
    
    return default_if_none
  
  def set_default_fiscal_year_start(self, value, refresh = False, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value=value):
      value = self.get_default_fiscal_year_start(refresh= refresh)

    self.get_config(refresh= refresh)["fiscal_year_start"] = value
    self._save_config()
  
  def get_default_fiscal_year_start(self, refresh = False, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value=self.get_config(refresh= refresh).get("fiscal_year_start")):
      return "01/01"
    
    if self.get_common().helper_type().datetime().datetime_from_string(dt_string= f'{self.get_common().helper_type().datetime().get().year}/{self.get_config().get("default_output_format")}') is not None:
      return "01/01"
    
    return self.get_common().helper_type().string().set_case(string_value= self.get_config().get("fiscal_year_start"), case= "lower")
  
  def get_default_output_format(self, refresh = False, *args, **kwargs):
    
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value=self.get_config(refresh= refresh).get("default_output_format")):
      return "json"
    
    if self.get_common().helper_type().string().set_case(string_value= self.get_config().get("default_output_format"), case= "lower") not in self.get_supported_output_format():
      return "json"
    
    return self.get_common().helper_type().string().set_case(string_value= self.get_config().get("default_output_format"), case= "lower")
  
  def set_default_output_format(self, value, refresh = False, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value=value):
      value = self.get_default_output_format(refresh= refresh)

    self.get_config(refresh= refresh)["default_output_format"] = value
    self._save_config()
  
  def get_default_provider(self, refresh = False, *args, **kwargs):
    return self.get_config(refresh= refresh).get("default_provider")
  
  def set_default_provider(self, value, refresh = False, *args, **kwargs):
    self.get_config(refresh= refresh)["default_provider"] = value
    self._save_config()

  def action_config(self, *args, **kwargs):
    print("Provider config not configured")

  def action_data(self, *args, **kwargs):
    print("Provider config not configured")
  
  
    

  
  

