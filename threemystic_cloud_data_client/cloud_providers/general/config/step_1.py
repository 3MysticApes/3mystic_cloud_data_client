from threemystic_cloud_data_client.cloud_providers.general.config.base_class.base import cloud_data_client_general_config_base as base
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers



class cloud_data_client_general_config_step_1(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_general_config_step_1", *args, **kwargs)
    

  def step(self, *args, **kwargs):
    if not super().step(run_base_config= True):
      return
    
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "default_provider": {
            "validation": lambda item: self.get_common().helper_type().string().set_case(string_value= item, case= "lower") in self.get_supported_providers(),
            "messages":{
              "validation": f"Valid options are: {self.get_supported_providers()}",
            },
            "conversion": lambda item: self.get_common().helper_type().string().set_case(string_value= item, case= "lower"),
            "desc": f"What do you want as the the default provider? \nValid Options: {self.get_supported_providers()}",
            "default": self.get_default_provider(),
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": True
        },        
        "default_output_format": {
            "validation": lambda item: self.get_common().helper_type().string().set_case(string_value= item, case= "lower") in self.get_supported_output_format(),
            "messages":{
              "validation": f"Valid options are: {self.get_supported_output_format()}",
            },
            "conversion": lambda item: self.get_common().helper_type().string().set_case(string_value= item, case= "lower"),
            "desc": f"What is the default output format.\nValid Options: {self.get_supported_output_format()}",
            "default": self.get_default_output_format(),
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": not self.get_common().helper_type().string().is_null_or_whitespace(string_value= self.get_default_output_format())
        },        
        "fiscal_year_start": {
            "validation": lambda item: not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item) and self.get_common().helper_type().datetime().datetime_from_string(dt_string= f'{self.get_common().helper_type().datetime().get().year}/{item}') is not None,
            "messages":{
              "validation": f"Please provide a valid date in the following format mm/dd",
            },
            "conversion": lambda item: self.get_common().helper_type().string().set_case(string_value= item, case= "lower"),
            "desc": f"What is the fiscal year start date? ex mm/dd (10/01)",
            "default": self.get_default_fiscal_year_start(),
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": not self.get_common().helper_type().string().is_null_or_whitespace(string_value= self.get_default_fiscal_year_start())
        }
      }
    )

    if(response is not None):
      for key, item in response.items():
        self._update_config(config_key= key, config_value= item.get("formated"))
      self._save_config()
      print("-----------------------------")
      print()
      print()
      print("Base Configuration is updated")
      print()
      print()
      print("-----------------------------")

    
    
  
