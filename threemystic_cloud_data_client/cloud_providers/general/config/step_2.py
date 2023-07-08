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
    response = self.get_common().generate_data().generate(
      generate_data_config = {
        "reset_cloud_share": {
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
      next_step.step(cloud_share= self.get_cloud_share_config_value(config_key= "type"))

    if self.get_common().helper_type().bool().is_true(check_value= response.get("reset_cloud_share").get("formated")):
      self.reset_config_cloud_share()
    
    next_step.step(cloud_share= self.get_cloud_share_config_value(config_key= "type"))
    return

    
    
  
