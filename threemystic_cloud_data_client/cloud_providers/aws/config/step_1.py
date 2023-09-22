from threemystic_cloud_data_client.cloud_providers.aws.config.base_class.base import cloud_data_client_aws_config_base as base
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers
from threemystic_cloud_client.cloud_providers.aws import cloud_client_aws as client
from threemystic_cloud_data_client.cloud_providers.general  import cloud_data_client_general as data_client

class cloud_data_client_aws_config_step_1(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_aws_config_step_1", *args, **kwargs)
    
  def check_cloud_client(self, *args, **kwargs):
    cloud_client = client( common= self.get_common(), logger= self.get_common().get_logger())
    if cloud_client.is_provider_config_completed():
      print(f"The client for the provider aws has already been configured. You can Update it now if you would like.")
      response = self.get_common().generate_data().generate(
        generate_data_config = {
          "base_config": {
            "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
            "messages":{
              "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
            },
            "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
            "desc": f"Do you need to configure the Cloud Client.\nValid Options: {self.get_common().helper_type().bool().is_true_values()}",
            "default": None,
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": True
          }
        }
      )

      if response is None:
        return
      
      if not self.get_common().helper_type().bool().is_true(check_value= response.get("base_config").get("formated")):
        return
    
    if not cloud_client.is_provider_config_completed():
      print("You must configure the cloud client provider for AWS...")
      self.get_common().helper_type().datetime().time_sleep(seconds= 2)

    cloud_client.action_config()

  def check_cloud_general(self, *args, **kwargs):
    client = data_client( common= self.get_common())

    if self.is_general_config_completed():
      print()
      print()
      print("--------------------------------------------------------------")
      print(f"The general config has been configured, do you want to update?")
      response = self.get_common().generate_data().generate(
        generate_data_config = {
          "base_config": {
            "validation": lambda item: self.get_common().helper_type().bool().is_bool(check_value= item),
            "messages":{
              "validation": f"Valid options for Yes are: {self.get_common().helper_type().bool().is_true_values()}",
            },
            "conversion": lambda item: self.get_common().helper_type().bool().is_true(check_value= item),
            "desc": f"Data Client: Do you want to configure base config?\nLeave blank to exit.\nValid Options: {self.get_common().helper_type().bool().is_true_values()}",
            "default": None,
            "handler": generate_data_handlers.get_handler(handler= "base"),
            "optional": True
          }
        }
      )

      if response is None:
        return
      
      if not self.get_common().helper_type().bool().is_true(check_value= response.get("base_config").get("formated")):
        return
    
    if not self.is_general_config_completed():
      print("You must configure the General Config...")
      self.get_common().helper_type().datetime().time_sleep(seconds= 2)
    client.action_config()

  def step(self, *args, **kwargs):
    
    self.check_cloud_client(*args, **kwargs)    
    self.check_cloud_general(*args, **kwargs)

    print()
    print()
    print()
    print(f"No additional config is required at this time for Data Client: {self.get_provider()}")
    
  
