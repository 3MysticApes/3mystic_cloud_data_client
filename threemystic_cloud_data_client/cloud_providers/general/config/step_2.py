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
    if not self.has_tag_data_config():
      return self.step_tag_new()
    
    return step_tag_clear()
  
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
  
  def step_tag_clear(self, confirm = False, *args, **kwargs):

    desc = ("Do you want to reset and clear the environment tag data?" if confirm is False else
      "Are you sure you want to reset the environment tag data?")
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "environment_tag_clear": {
          "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
          "messages":{
            "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
          },
          "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
          "desc": f"{desc}\nValid Options: {self.get_common().helper_type().bool().is_true_values()}",
          "default": None,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": True
        }
      }
    )
    if response is None:
      return

    if confirm is False and  self.get_common().helper_type().bool().is_true(check_value= response.get("environment_tag_clear").get("formated")):
      return self.step_tag_clear(confirm= True) 
    
    if confirm is True and  self.get_common().helper_type().bool().is_true(check_value= response.get("environment_tag_clear").get("formated")):
      print("-----------------------------")
      print()
      print()
      print("Base Environment Tag cleared")
      print()
      print()
      print("-----------------------------")
      self.reset_config_environment_data()
      return self.step()

    print("-----------------------------")
    print()
    print()
    print("Base Environment Tag NOT cleared")
    print()
    print()
    print("-----------------------------")
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
          "default": self.get_environment_data_config_value("tag", None),
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": self.get_environment_data_config_value("tag", None) is not None
        },        
        "tag_insensitive": {
          "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
          "messages":{
            "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
          },
          "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
          "desc": f"Treat the tags as case insensitive.\nIE EnvIronmeNt and environment would be the same.\nValid Options: {self.get_common().helper_type().bool().is_true_values()}",
          "default": self.get_environment_data_config_value("tag_insensitive", True),
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
    
    if len(self.get_environment_data_config_value("environment_tag", []])) < 1:
      return self.step_add_alttag()
    
    return self.step_tag_edit_new()
  
  def step_tag_edit_new(self, *args, **kwargs):
    print("-----------------------------")
    print()
    print()
    print("Do you want to edit an existing alt tag or add new alt tags?")
    print()
    print("1: Edit Existing")
    print("2: Remove Existing")
    print("3: New Alt Tag")
    print()
    print()
    print("-----------------------------")
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "environment_tag_options": {
          "validation": lambda item: not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item) and self.get_common().helper_type().general().is_integer(item) and self.get_common().helper_type().int().get(item) > 0 and self.get_common().helper_type().int().get(item) < 4,
          "messages":{
            "validation": f"Valid options are 1 - 3.",
          },
          "conversion": lambda item: self.get_common().helper_type().int().get(item) if not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item) else None,
          "desc": f"Please select if you want to edit or add a new alt tag.\nValid Options: 1 - 3",
          "default": None,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": False
        }
      }
    )
    if response is None:
      return

    if self.get_common().helper_type().int().get(response.get("environment_tag_options").get("formated")) == 1:
      return self.step_edit_remove__alttag(is_edit = True)
    
    if self.get_common().helper_type().int().get(response.get("environment_tag_options").get("formated")) == 1:
      return self.step_edit_remove__alttag(is_edit = False)
    
    if self.get_common().helper_type().int().get(response.get("environment_tag_options").get("formated")) == 3:
      return self.step_add_alttag() 
    
    return
  
  def step_edit_remove__alttag(self, is_edit = True, *args, **kwargs):
    if len(self.get_environment_data_config_value("environment_tag", [])) < 1:
      return self.step_add_alttag()
    
    print("-----------------------------")
    print()
    print()
    if is_edit:
      print("Which tag do you want to edit?")
    else
      print("Which tag do you want to remove?")
    print()
    print("0: Exit")
    for index, val in enumerate(self.get_environment_data_config_value("environment_tag", [])):
      print(f"{index + 1}: {val}")
    print()
    print()
    print("-----------------------------")

    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "alttag": {
          "validation": lambda item: not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item) and self.get_common().helper_type().general().is_integer(item) and self.get_common().helper_type().int().get(item) >= 0 and self.get_common().helper_type().int().get(item) <= (len(drive_item_id_options[drive_item_position]) - 1),
          "messages":{
            "validation": f"Valid options are: 0 - {len(self.get_environment_data_config_value("environment_tag", []))}",
          },
          "conversion": lambda item: self.get_common().helper_type().int().get(item) if not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item) else None,
          "desc": f"Please select the tenant to use \nValid Options: 0 -  {len(self.get_environment_data_config_value("environment_tag", []))}",
          "default": None,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": True
        },
      }
    )

    if response is None:
      return self.step_tag_edit_new()
    
    if self.get_common().helper_type().int().get(response.get("alttag").get("formated")) == 0:
      return
    
    if not is_edit:
      self.get_environment_data_config_value("environment_tag", []).pop(self.get_common().helper_type().int().get(response.get("alttag").get("formated")) - 1)
      self._save_config_environment_data()
      return self.step_tag_edit_new()
    
    self.get_environment_data_config_value("environment_tag", [])[self.get_common().helper_type().int().get(response.get("alttag").get("formated")) - 1] = self.step_add_edit_alttag(edit_tag_index= self.get_common().helper_type().int().get(response.get("alttag").get("formated")) - 1)
    self._save_config_environment_data()
    return self.step_tag_edit_new()
  
  def step_add_edit_alttag(self, edit_tag_index = None, *args, **kwargs):
    
    default_tag_value = None
    if edit_tag_index is not None:
      if edit_tag_index >=0 and edit_tag_index <= len(self.get_environment_data_config_value("environment_tag", []))
      default_tag_value = self.get_environment_data_config_value("environment_tag", [])[edit_tag_index]

    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "environment_tag": {
          "validation": lambda item: not self.get_common().helper_type().string().is_null_or_whitespace(string_value= item),
          "messages":{
            "validation": f"The value cannot be empty",
          },
          "conversion": lambda item: self.get_common().helper_type().string().trim(string_value= item),
          "desc": f"What is the alt tag?\n(leave empty or type quit or exit)",
          "default": default_tag_value,
          "handler": generate_data_handlers.get_handler(handler= "base"),
          "optional": False
        }
      }
    )

    if response is None:
      return default_tag_value

    if response.get("environment_tag") is None:
      return default_tag_value

    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= response.get("environment_tag").get("formated")):
      return default_tag_value
    
    return response.get("environment_tag").get("formated")
    


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
    
  
