from threemystic_common.base_class.base_general import base as main_base


class base(main_base): 
  """This is a library to help with the interaction with the cloud providers"""

  def __init__(self, logger_name, init_object = None, common = None,  logger = None, *args, **kwargs) -> None:
    self.__init_common(
      common= common,
      init_object= init_object,
      logger_name= logger_name,
      logger= logger,
      *args, **kwargs
    )


  