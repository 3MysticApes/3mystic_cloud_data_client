import sys
import abc
from threemystic_common.base_class.generate_data.generate_data_handlers import generate_data_handlers


class cloud_data_client_action_base():
  def __init__(self, cloud_data_client = None, *args, **kwargs):
    self._cloud_data_client = cloud_data_client 
    if self._cloud_data_client is None:
      from threemystic_cloud_data_client.cloud_data_client import cloud_data_client
      self._cloud_data_client = cloud_data_client()
      

  
