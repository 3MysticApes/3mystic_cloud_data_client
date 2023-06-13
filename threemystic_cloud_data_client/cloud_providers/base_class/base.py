from threemystic_common.base_class.base_provider import base
import abc

class cloud_client_provider_base(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self._post_init(*args, **kwargs)

  
  def _post_init(self, *args, **kwargs):
    pass
  
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
    return self.get_common().get_threemystic_directory_config().joinpath(f"{self.get_main_directory_name()}/3mystic_cloud_client_config_{self.get_provider()}")
  
  def get_config(self, refresh = False, *args, **kwargs):
    if hasattr(self, "_config_data") and not refresh:
      return self._config_data
    
    self._config_data = self.__load_config()    
    return self.get_config(*args, **kwargs)
  
  
  def action_config(self, *args, **kwargs):
    print("Provider config not configured")
  
  
    

  
  

