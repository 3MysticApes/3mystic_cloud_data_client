import sys
from threemystic_common.base_class.base_script_options import base_process_options


class cloud_data_client_cli(base_process_options):
  def __init__(self, *args, **kwargs):
    from threemystic_cloud_data_client.cloud_data_client import cloud_data_client
    self._cloud_data_client = cloud_data_client()
    
    super().__init__(common= self._cloud_data_client.get_common(), *args, **kwargs)

    self.parser = self.get_parser(
      parser_init_kwargs = {
        "description": "One Action is required"
      },
      parser_args = {
        # I can create other actions just by duplication this and changing the const,
        "--version": {
            "default": None, 
            "const": "version",
            "dest": "client_action",
            "help": "Action: outputs the versions of the app being used.",
            "action": 'store_const'
        },
        "--config,-c": {
            "default": None, 
            "const": "config",
            "dest": "client_action",
            "help": "Action: This is so you can setup the data client",
            "action": 'store_const'
        },
        "--data,-d": {
            "default": None, 
            "const": "data",
            "dest": "client_action",
            "help": "Action: Pull the various Data from the provider",
            "action": 'store_const'
        },
        "--provider,-p": {
            "default": None, 
            "type": str,
            "choices": self._cloud_data_client.get_supported_providers(),
            "dest": "client_provider",
            "help": "Provider: This is to set the provider that should be used",
            "action": 'store'
        },
      }
    )

    processed_info = self.process_opts(
      parser = self.parser
    )

    for key, value in processed_info["processed_data"].items():
      setattr(self, f"_{key}", value)
    
    
  def process_client_action(self, force_action = None, *args, **kwargs):
    if self._cloud_data_client.get_common().helper_type().string().is_null_or_whitespace(string_value= force_action):
      force_action = self.__get_client_acount()
    if force_action == "version":
      self.version_dispaly()
      return
    
    if force_action == "config":
      if not "provider" in kwargs:
        if not self._cloud_data_client.get_common().helper_type().string().is_null_or_whitespace(string_value= self._client_provider):
          kwargs["provider"] = self._client_provider
          
      from threemystic_cloud_data_client.cli.actions.config import cloud_data_client_config as user_action
      user_action(cloud_client= self._cloud_data_client).main(*args, **kwargs)
      return
    
    if force_action == "data":
      if not "provider" in kwargs:
        if not self._cloud_data_client.get_common().helper_type().string().is_null_or_whitespace(string_value= self._client_provider):
          kwargs["provider"] = self._client_provider
      self._cloud_data_client.client(*args, **kwargs).run()
      return



    return

  def version_dispaly(self, *args, **kwargs): 
    from threemystic_cloud_client.cloud_client import cloud_client
    cloud_client = cloud_client(
      logger= self._cloud_data_client.get_common().get_logger(), 
      common= self._cloud_data_client.get_common())
    print(f"You currenly have installed")
    print(f"3mystic_cloud_data_client: v{self._cloud_data_client.version()}")
    print(f"3mystic_cloud_client: v{cloud_client.version()}")
    print(f"3mystic_common: v{self._cloud_data_client.get_common().version()}")
    print()

  def __get_client_acount(self, *args, **kwargs):
    if not hasattr(self, "_client_action"):
      return None
    
    return self._client_action
  def main(self, *args, **kwargs):    
    if self.__get_client_acount() is None:
      print(f"Thank you for using the 3 Mystic Apes Cloud Client.")
      self.version_dispaly()
      print()
      self.parser.print_help()
      return
    
    self.process_client_action( )

def main(*args, **kwargs):    
  cloud_data_client_cli(*args, **kwargs).main(*args, **kwargs)
    

if __name__ == '__main__':   
  cloud_data_client_cli().main(sys.argv[1:])