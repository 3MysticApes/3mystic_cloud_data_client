from threemystic_cloud_data_client.cloud_providers.azure.base_class.base import cloud_data_client_provider_azure_base as base


class cloud_data_client_azure(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_azure", *args, **kwargs)
  

  def action_config(self, *args, **kwargs): 
    
    from threemystic_cloud_data_client.cloud_providers.azure.config.step_1 import cloud_data_client_azure_config_step_1 as step
    next_step = step(common= self.get_common(), logger= self.get_logger())
    
    next_step.step()


  
    
    
  
