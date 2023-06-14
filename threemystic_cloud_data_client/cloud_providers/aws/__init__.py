from threemystic_cloud_data_client.cloud_providers.aws.base_class.base import cloud_data_client_provider_aws_base as base


class cloud_data_client_aws(base):
  def __init__(self, *args, **kwargs):
    super().__init__(logger_name= "cloud_data_client_aws", *args, **kwargs)

  def action_config(self, *args, **kwargs): 
    
    from threemystic_cloud_data_client.cloud_providers.aws.config.step_1 import cloud_data_client_aws_config_step_1 as step
    next_step = step(common= self.get_common(), logger= self.get_logger())
    
    next_step.step()


  
    
    
  
