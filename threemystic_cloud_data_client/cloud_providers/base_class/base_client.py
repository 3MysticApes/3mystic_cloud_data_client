from threemystic_common.base_class.base_provider import base
from threemystic_common.base_class.base_script_options import base_process_options
import textwrap, argparse
import asyncio


class cloud_data_client_provider_base_client(base):
  def __init__(self, force_action_arguments = None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.__set_cloud_client(*args, **kwargs)
    self.__set_cloud_data_client(*args, **kwargs)
    self.__set_suppres_parser_help(*args, **kwargs)
    
    self._default_parser_init = {
      "prog": f'3mystic_cloud_data_client -d -p {kwargs["provider"]}',
      "formatter_class": argparse.RawDescriptionHelpFormatter,
      "description": textwrap.dedent('''\
      Requires additional settings.
        One data Action (if more than one is selected only the last one will be ran)
      '''),
      "add_help": False,
      "epilog": ""
    }
  
    self._set_action_from_arguments(force_action_arguments= force_action_arguments, *args, **kwargs)
    
    self._set_data_action()

  @classmethod
  def get_default_parser_args(cls, *args, **kwargs):
    return {
      "--cloudstorage": {
        "default": None, 
        "const": "cloudstorage",
        "dest": "data_action",
        "help": "Data Action: This pulls Cloud Storage (S3/Storage Accounts) for the provider",
        "action": 'store_const'
      },
      "--budget": {
        "default": None, 
        "const": "budget",
        "dest": "data_action",
        "help": "Data Action: This pulls a general budget to provide you insights in your accounts/subscriptions",
        "action": 'store_const'
      },
      "--storage": {
        "default": None, 
        "const": "storage",
        "dest": "data_action",
        "help": "Data Action: This pulls either VM Disks or EC2 Storage depending on the provider",
        "action": 'store_const'
      },
      "--vm": {
        "default": None, 
        "const": "vm",
        "dest": "data_action",
        "help": "Data Action: This pulls either EC2 or VM depending on the provider",
        "action": 'store_const'
      },
      "--vmss": {
        "default": None, 
        "const": "vmss",
        "dest": "data_action",
        "help": "Data Action: This pulls either ASG or VMSS depending on the provider",
        "action": 'store_const'
      }
    }
  
  def get_suppres_parser_help(self, *args, **kwargs):
    if hasattr(self, "_suppres_parser_help"):
      return self._suppres_parser_help
    return False
    

  def __set_suppres_parser_help(self, suppress_parser_help = False, *args, **kwargs):
    self._suppres_parser_help = suppress_parser_help

  def __get_action_parser_options(self, *args, **kwargs):
    if hasattr(self, "_action_process_options"):
      return self._action_process_options
    
    self._action_process_options = base_process_options(common= self.get_common())
    return self.__get_action_parser_options()
    
  def _get_action_parser(self, *args, **kwargs):
    if hasattr(self, "_action_parser"):
      return self._action_parser
    
    
    self._action_parser = self.__get_action_parser_options().get_parser(
      parser_init_kwargs = self._default_parser_init,
      parser_args = self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        self.get_default_parser_args(),
      ])
    )
    return self._get_action_parser()
  
  def get_action_from_arguments(self, *args, **kwargs):
    if hasattr(self, "_action_from_arguments"):
      return self._action_from_arguments
    
    return {}
  
  def _set_action_from_arguments(self, force_action_arguments = None, *args, **kwargs):
    if force_action_arguments is not None:
      self._action_from_arguments = force_action_arguments
      return self.get_action_from_arguments()

    processed_info = self.__get_action_parser_options().process_opts(
      parser = self._get_action_parser()
    )

    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= processed_info["processed_data"].get("data_action")):
      if not self.get_suppres_parser_help():
        self._get_action_parser().print_help()
      return None
    
    self._action_from_arguments = processed_info["processed_data"]
    return self.get_action_from_arguments()  

  def get_data_action(self, *args, **kwargs):
    if hasattr(self, "_data_action_data"):
      return self._data_action_data
    
    return None
  
  def _set_data_action(self, *args, **kwargs):
    if self.get_action_from_arguments() is None or len(self.get_action_from_arguments()) < 1:
      return

    try:
      self._data_action_data = self._process_data_action(
        provider = self.get_provider(),
        action= self.get_common().helper_type().string().set_case(string_value= self.get_action_from_arguments() .get('data_action') , case= "lower"), 
        *args, **kwargs)
      
    except Exception as err:
      print(f"The action {self.get_action_from_arguments().get('data_action')} is unknown")
      self.get_common().get_logger().exception(f"The action {self.get_action_from_arguments() .get('data_action')} is unknown", extra={"exception": err})
      if not self.get_suppres_parser_help():
        self._get_action_parser().print_help()
  
  def _process_data_action(self, provider, action, *args, **kwargs):    
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= action):
      return None
    data_action = __import__(f'threemystic_cloud_data_client.cloud_providers.{provider}.client.actions.{action}', fromlist=[f'cloud_data_client_{provider}_client_action'])
    process_data_action = getattr(data_action, f'cloud_data_client_{provider}_client_action')(
      cloud_data_client= self,
      common= self.get_common(),
      logger= self.get_common().get_logger()
    )
    return process_data_action
  
  def run(self, *args, **kwargs):
    if self.get_data_action() is None:
      return 

    results = asyncio.run(self.get_data_action().main())
    self.get_data_action().format_results(results= results, output_format= self.get_cloud_data_client().get_default_output_format())
  
  def get_cloud_client(self, *args, **kwargs):
    return self.__cloud_client
  
  def __set_cloud_client(self, cloud_client, *args, **kwargs):
    self.__cloud_client = cloud_client
  
  def get_cloud_data_client(self, *args, **kwargs):
    return self.__cloud_data_client
  
  def __set_cloud_data_client(self, cloud_data_client, *args, **kwargs):
    self.__cloud_data_client = cloud_data_client
    
  
  
    

  
  

