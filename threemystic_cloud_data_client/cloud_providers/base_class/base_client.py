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
  
    self._set_arguments_from_parameters(force_action_arguments= force_action_arguments, *args, **kwargs)
    
    self._set_data_action()

  @classmethod
  def get_default_parser_args_actions(cls, *args, **kwargs):
    return {
      "--cloudstorage": {
        "default": None, 
        "const": "cloudstorage",
        "dest": "data_action",
        "help": "Data Action: This pulls Cloud Storage (S3/Storage Accounts) for the provider",
        "action": 'store_const' # could look into append_const
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
  
  def get_parser_args(self, *args, **kwargs):
    if hasattr(self, "_data_parser_args"):
      return self._data_parser_args
    
    
    self._data_parser_args = self.get_common().helper_type().dictionary().merge_dictionary([
      {},
      {
        "--filter,-f": {
          "default": None,
          "type": str,
          "dest": "data_filter",
          "help": "Filter: JSON string representing the filter data. ex {\"condition\":\"and\", \"filters\":[{\"condition\":\"iequals\",\"key\": [\"properties\",\"storageProfile\",\"osDisk\",\"osType\"], \"value\": \"windows\"}]}",
          "action": 'store'
        },
        "--hideempty, --hide-empty": {
          "default": False,
          "dest": "data_hideempty",
          "help": "Hide accounts with no data. Default False",
          "action": 'store_true'
        },
        "--account": {
          "default": None,
          "type": str,
          "dest": "data_accounts",
          "help": "Filter: A comma seperated list of accounts to filter, put a minus to exclude accounts. 123454,12345,-234534",
          "action": 'store'
        }
      },
      self.get_default_parser_args_actions(),
    ])
    return self.get_parser_args()
  
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
        self.get_parser_args(),
      ])
    )
    return self._get_action_parser()
  
  def get_data_run_key(self, data_key = None, default_value = {}, *args, **kwargs):
    if hasattr(self, "_data_arg_param_values"):
      if data_key is None:
        return self._data_arg_param_values
      if data_key in self._data_arg_param_values:
        return self._data_arg_param_values.get(data_key)
    
    return default_value
  
  def get_data_run_action(self, *args, **kwargs):
    if hasattr(self, "_data_arg_param_values"):
      return self._data_arg_param_values.get("data_action")
    
    return None
  
  def _process_data_run_filter(self, data_filter, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= data_filter):
      data_filter = {}
    
    if data_filter is None:
      data_filter = {}
    
    if self.get_common().helper_type().general().is_type(obj= data_filter, type_check= str):
      try:
        data_filter = self.get_common().helper_json().loads(data= data_filter)
      except Exception as err:
        # will look to do something for various verbocity levels
        # print(err) 
        pass
    
    if not self.get_common().helper_type().general().is_type(obj= data_filter, type_check= dict):
      return {}
    
    return data_filter    
  
  
  def _set_arguments_from_parameters(self, data_action = None, data_filter = None, data_hideempty = None, data_accounts = None, *args, **kwargs):
    """
    If the values for the data_* params are not either None or an empty string it will override whatever is in the arguments from the script call
    """
    processed_info = self.__get_action_parser_options().process_opts(
      parser = self._get_action_parser()
    )

    self._data_arg_param_values={
      "data_action": data_action,
      "data_filter": data_filter,
      "data_hideempty": data_hideempty,
      "data_accounts": data_accounts,
    }

    for key, item in self._data_arg_param_values.items():
      if item is None or self.get_common().helper_type().string().is_null_or_whitespace(string_value= item):
        self._data_arg_param_values[key] = processed_info["processed_data"].get(key)


    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= self._data_arg_param_values.get("data_action")):
      if not self.get_suppres_parser_help():
        self._get_action_parser().print_help()
        return None
      
    self._data_arg_param_values["data_filter"] = self._process_data_run_filter(data_filter= data_filter)
    self._data_arg_param_values["data_hideempty"] = self.get_common().helper_type().bool().is_true(check_value= self._data_arg_param_values["data_hideempty"])
    

  def get_data_action(self, action = None, *args, **kwargs):
    if hasattr(self, "_data_action_data"):
      
      if self.get_common().helper_type().string().is_null_or_whitespace(string_value= action):
        action = self._data_action_data["default"]
      
      if self._data_action_data.get(action) is not None:
        return self._data_action_data.get(action)
      
      self._data_action_data[action] = self._process_data_action(
        provider = self.get_provider(),
        action= action, 
        *args, **kwargs)
      return self.get_data_action(action= action, *args, **kwargs)
  
  def _set_data_action(self, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= self.get_data_run_action()):
      return

    try:      
      action = self.get_common().helper_type().string().set_case(string_value= self.get_data_run_action() , case= "lower")
      if action != "all":
        self._data_action_data = {
          "default": action,
          action: self._process_data_action(
          provider = self.get_provider(),
          action= action, 
          *args, **kwargs)
        }
        return
      
      self._data_action_data = {
        arg_key: self._process_data_action(
          provider = self.get_provider(),
          action= arg.get("const"), 
          *args, **kwargs)
        for arg_key, arg in self.get_default_parser_args_actions().items() if arg.get("const") != "all"
      }
      self._data_action_data["default"] = list(self._data_action_data.keys())[0]
      
    except Exception as err:
      self.get_common().get_logger().exception(f"The action {self.get_data_run_action()} is unknown", extra={"exception": err})
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

    results = asyncio.run(self.get_data_action().main(run_params= self.get_data_run_key(data_key= None) ))
    self.get_data_action().format_results(results= results, output_format= self.get_cloud_data_client().get_default_output_format())
  
  def get_cloud_client(self, *args, **kwargs):
    return self.__cloud_client
  
  def __set_cloud_client(self, cloud_client, *args, **kwargs):
    self.__cloud_client = cloud_client
  
  def get_cloud_data_client(self, *args, **kwargs):
    return self.__cloud_data_client
  
  def __set_cloud_data_client(self, cloud_data_client, *args, **kwargs):
    self.__cloud_data_client = cloud_data_client
    
  
  
    

  
  

