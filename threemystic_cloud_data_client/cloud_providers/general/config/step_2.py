from threemystic_cloud_data_client.cloud_providers.general.config.base_class.base import cloud_data_client_general_config_base as base
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers



class cloud_data_client_general_config_step_2(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_general_config_step_2", *args, **kwargs)
    

  def step(self, *args, **kwargs):
    if not super().step(run_base_config= True):
      return
    
    self.update_general_config_completed(status= True)
    
    print()
    print()
    print()
    print("-------------------------------------")
    print("Resource Environment Info")
    print("By default the system will mark all accounts/subscriptions/resources as nonprod/prod based on the name. If the tag exists the tag will override general prod/nonprod setting.")
    print("It will first check for a match on the resources if nothing is found it will then look to the account/subscription. It Defaults to prod, because if something cannot be identified as nonprod it should be treated as prod for saftey.")
    print("The default nonprod names are:")
    print(self.get_nonprod_names())
    print("-------------------------------------")
    print()
    print()
    print()
    self.step_tag_new()
  
  def step_tag_new(self, *args, **kwargs):
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "environment_tag": {
          "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
          "messages":{
            "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
          },
          "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
          "desc": f"Do you use tags to determine environment?\nValid Options: {self.get_common().helper_type().bool().is_true_values()}",
          "default": None,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": True
        }
      }
    )
    if response is None:
      return

    if self.get_common().helper_type().bool().is_true(check_value= response.get("environment_tag").get("formated")):
      self.step_tag() 
    
    return
  
  def step_tag(self, *args, **kwargs):
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "tag": {
          "validation": lambda item: not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item),
          "messages":{
            "validation": f"The value cannot be empty",
          },
          "conversion": lambda item: self.get_common().helper_type().string().trim(string_value= item),
          "desc": f"What is the main tag to determin the environment?",
          "default": None,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": False
        },        
        "tag_insensitive": {
          "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
          "messages":{
            "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
          },
          "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
          "desc": f"Treat the tags as case insensitive.\nIE EnvIronmeNt and environment would be the same.\nValid Options: {self.get_common().helper_type().bool().is_true_values()}",
          "default": True,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": True
        }
      }
    )
    if response is None:
      print("-----------------------------")
      print()
      print()
      print("Base Environment Tag NOT updated/Configured")
      print()
      print()
      print("-----------------------------")
      return
    for key, item in response.items():
      self._update_config_environment_data(config_key= key, config_value= item.get("formated"))
    self._save_config()

    print("-----------------------------")
    print()
    print()
    print("Base Environment Tag updated/configured")
    print()
    print()
    print("-----------------------------")
    
    self.step_add_alttag()
  
  def step_add_alttag(self, *args, **kwargs):
    
    stop_alt_tag = False
    alt_tags_add = []
    while not stop_alt_tag:
      response = self.get_common().generate_data().generate(
        generate_data_config = {
          "environment_tag": {
            "validation": lambda item: not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item),
            "messages":{
              "validation": f"The value cannot be empty",
            },
            "conversion": lambda item: self.get_common().helper_type().string().trim(string_value= item),
            "desc": f"What is the alt tag?\n(leave empty to end or type quit or exit)",
            "default": None,
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": False
          }
        }
      )

      if response is None:
        stop_alt_tag = True
        break

      if response.get("environment_tag") is None:
        stop_alt_tag = True
        break

      if self.get_common().helper_type().string().is_null_or_whitespace(string_value= response.get("environment_tag").get("formated")):      
        stop_alt_tag = True
        break
    
      alt_tags_add.append(response.get("environment_tag").get("formated"))

    alt_tags_add = self.get_common().helper_type().list().unique_list(
      data= alt_tags_add,
      case_sensitive= not self.get_environment_data_config_value(
        config_key= "tag_insensitive",
        default_if_none= True
      )
    )
    self._update_config_environment_data(config_key= "alt_tags", config_value= alt_tags_add)
    self._save_config()
    
  
