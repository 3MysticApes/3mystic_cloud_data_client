from threemystic_cloud_data_client.cloud_providers.base_class.base_client import cloud_data_client_provider_base_client as base
from threemystic_common.base_class.base_script_options import base_process_options
import asyncio

class cloud_data_client_azure_client(base):
  def __init__(self, *args, **kwargs):
    super().__init__(provider= "azure", logger_name= "cloud_data_client_azure_client", *args, **kwargs)

    process_options = base_process_options(common= self.get_common())
    parser = process_options.get_parser(
      parser_init_kwargs = self._default_parser_init,
      parser_args = self.get_common().helper_type().dictionary().merge_dictionary([
         self._default_parser_args,
      ])
    )

    processed_info = process_options.process_opts(
      parser = parser
    )

    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= processed_info["processed_data"].get("data_action")):
      parser.print_help()
      return
    
    data_action = __import__(f"threemystic_cloud_data_client.cloud_providers.azure.client.actions.{processed_info['processed_data'].get('data_action')}", fromlist=['cloud_data_client_azure_client_action'])
    process_data_action = getattr(data_action, 'cloud_data_client_azure_client_action')(
      cloud_client= self.get_cloud_client(),
      common= self.get_common(),
      logger= self.get_common().get_logger()
    )
    asyncio.run(process_data_action.main())