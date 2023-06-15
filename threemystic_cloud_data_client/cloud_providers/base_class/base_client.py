from threemystic_common.base_class.base_provider import base
import textwrap, argparse

class cloud_data_client_provider_base_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.__set_cloud_client(*args, **kwargs)
    self.__set_cloud_data_client(*args, **kwargs)
    
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

    self._default_parser_args = {
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
      },
      "--storage": {
        "default": None, 
        "const": "vmss",
        "dest": "data_action",
        "help": "Data Action: This pulls either VM Disks or EC2 Storage depending on the provider",
        "action": 'store_const'
      },
      "--blob": {
        "default": None, 
        "const": "vmss",
        "dest": "data_action",
        "help": "Data Action: This pulls Cloud Storage (S3/Storage Accounts) for the provider",
        "action": 'store_const'
      }
    }
  
  def get_cloud_client(self, *args, **kwargs):
    return self.__cloud_client
  
  def __set_cloud_client(self, cloud_client, *args, **kwargs):
    self.__cloud_client = cloud_client
  
  def get_cloud_data_client(self, *args, **kwargs):
    return self.__cloud_data_client
  
  def __set_cloud_data_client(self, cloud_data_client, *args, **kwargs):
    self.__cloud_data_client = cloud_data_client
    
  
  
    

  
  

