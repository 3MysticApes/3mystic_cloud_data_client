from threemystic_cloud_data_client.cloud_providers.base_class.base_client import cloud_data_client_provider_base_client as base

class cloud_data_client_aws_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "aws", logger_name= "cloud_data_client_aws_client", *args, **kwargs)
    
    
  def get_client_parser_args_actions(self, *args, **kwargs):
    return {
       "--elastisearch,--es": {
        "default": None, 
        "const": "elastisearch",
        "dest": "data_action",
        "help": "Data Action: This pulls Elasticsearch data from aws",
        "action": 'store_const' # could look into append_const
      },
      "--certificates,--ssl": {
        "default": None, 
        "const": "certificates",
        "dest": "data_action",
        "help": "Data Action: This pulls Certificats information from services like acm",
        "action": 'store_const'
      },
    }
  