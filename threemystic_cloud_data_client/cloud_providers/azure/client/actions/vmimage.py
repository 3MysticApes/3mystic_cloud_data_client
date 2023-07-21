from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from azure.mgmt.compute import ComputeManagementClient



class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="vmimage", 
      logger_name= "cloud_data_client_azure_client_action_vmimage",
      *args, **kwargs)
      
  async def _process_account_data(self, account, loop, *args, **kwargs):
    client = ComputeManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
    image_galleries = self.get_cloud_client().sdk_request(
           tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
           lambda_sdk_command=lambda: client.galleries.list()
          )
    
    image_gallery_images = { }
    
    for gallery in image_galleries:
      for image in self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
          lambda_sdk_command=lambda: client.gallery_images.list_by_gallery(
            resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= gallery),
            gallery_name= gallery.name
          )
        ):
        image_gallery_images[self.get_cloud_client().get_resource_id(resource= gallery)] = self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          {"extra_versions": [
            self.get_cloud_client().serialize_resource(resource= image_version) 
            for image_version in self.get_cloud_client().sdk_request(
            tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
            lambda_sdk_command=lambda: client.gallery_image_versions.list_by_gallery_image(
                resource_group_name= self.get_cloud_client().get_resource_group_from_resource(resource= gallery),
                gallery_name= gallery.name,
                gallery_image_name= image.name
              )
            )
          ]},
          self.get_cloud_client().serialize_resource(resource= image)
          
        ])


    return {
      "account": account,
      "data": [
          self.get_common().helper_type().dictionary().merge_dictionary([
          {},
          await self.get_base_return_data(
            account= self.get_cloud_client().serialize_resource(resource= account),
            resource_id= self.get_cloud_client().get_resource_id(resource= item),
            resource= item,
            region= self.get_cloud_client().get_resource_location(resource= item),
            resource_groups= [self.get_cloud_client().get_resource_group_from_resource(resource= item)],
          ),
          image_gallery_images[self.get_cloud_client().get_resource_id(resource= item)],
        ]) for item in image_gallery_images
      ]
    }