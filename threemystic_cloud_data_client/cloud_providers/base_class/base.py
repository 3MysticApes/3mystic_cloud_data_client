from threemystic_common.base_class.base_provider import base
import abc

class cloud_data_client_provider_base(base):
  def __init__(self, *args, **kwargs):
    if "provider" not in kwargs:
      kwargs["provider"] = self.get_default_provider()
    super().__init__(*args, **kwargs)
    
  
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
  
  
    

  
  

