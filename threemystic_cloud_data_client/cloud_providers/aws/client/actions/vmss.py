"""The AWS vmss Action. This will pull the AWS ASGs"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.vmimage import cloud_data_client_aws_client_action as vmimage_data

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="vmss",
      logger_name= "cloud_data_client_aws_client_action_vmss",
      *args, **kwargs)
    
    
    self.data_id_name = "AutoScalingGroupARN"
    
    self.arn_lambda = (lambda item: item["extra_id"])
    
    self.auto_region_resourcebytype= ["Amazon Elastic Compute Cloud - Compute"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::EC2::Instance',
      ]
    },
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::AutoScaling::AutoScalingGroup',
      ]
    }
  ]
    
  
  async def _pre_load_main_process(self, pool, *args, **kwarg):
    self.required_extra_data["instances_information"] = {}
    if self.required_extra_data.get("ami") is None:
      base_action_params = {
        "cloud_data_client": self._get_cloud_data_client_raw(),
        "common": self.get_common(),
        "logger": self.get_common().get_logger()
      }
     
      ami_data = vmimage_data(
        **base_action_params
      )
      tmp_ami_data = await ami_data.main(pool=pool, run_params= self.get_runparam_key(data_key= None))
      self.required_extra_data["ami"] = await ami_data.get_data_by_id(results= tmp_ami_data, id_override = "extra_id_only")

  def _process_preloaded_data(self, preloaded_data = None, *args, **kwargs):
    self.required_extra_data = {}
    if preloaded_data is not None:
      if preloaded_data.get("ami") is not None:        
        if len(preloaded_data.get("ami")) > 0:
          self.required_extra_data["ami"] = preloaded_data.get("ami")
  
  async def __getImageInfo(self, image_id, *args, **kwargs):
    if image_id in self.required_extra_data["ami"]:
      return {
        "Id": image_id,
        "Name": self.required_extra_data["ami"][image_id]["Name"],
        "Description": self.required_extra_data["ami"].get("Description")
      }


    return {
      "Id": image_id,
    }
  
  async def process_account_region_asgInstances_get_launchtemplate_version(self, ec2_client, id, version, *args, **kwargs):
      lt_details = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: ec2_client.describe_launch_template_versions(**item),
        boto_params={"LaunchTemplateId": id, "Versions": [str(version)] },
        boto_nextkey = None,
        boto_key="LaunchTemplateVersions"
      )

      if len(lt_details) < 1:
          return {}

      return (await self.__get_imagedetails_template(lt_details))[0]
  
  async def process_account_region_asgInstances_get_launchtemplate_getversions(self, ec2_client, id, minversion, maxversion, *args, **kwargs):
      
    minversion = minversion if minversion > 1 else 1
    if minversion == maxversion:
      return [(await self.process_account_region_asgInstances_get_launchtemplate_version(ec2_client, id, minversion))]
    
    lt_details = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: ec2_client.describe_launch_template_versions(**item),
      boto_params={"LaunchTemplateId": id, "MinVersion": str(minversion if minversion > 1 else 1), "MaxVersion": str(maxversion)  },
      boto_nextkey = None,
      boto_key="LaunchTemplateVersions"
    )

    if len(lt_details) < 1:
      return []

    return await self.__get_imagedetails_template(lt_details)
  
  async def process_account_region_asgInstances_get_launchtemplate_getversionlast5(self, ec2_client, id, latest_version, *args, **kwargs):
      last10_versions = await self.process_account_region_asgInstances_get_launchtemplate_getversions(ec2_client, id, latest_version - 10, latest_version)
      if len(last10_versions) < 2:
        return last10_versions
        
      last10_versions.sort(key=lambda item: item["VersionNumber"], reverse=True)

      if len(last10_versions) < 5:
        return last10_versions
      
      return last10_versions[:5]

  async def __get_imagedetails_template(self, templates_details ):
    for lt_details in templates_details:
      lt_details["LaunchTemplateData"]["extra_image"] = await self.__getImageInfo(image_id= lt_details["LaunchTemplateData"]["ImageId"])
    
    return templates_details
  
  async def process_account_region_asgInstances_get_launchtemplates(self, ec2_client, launch_tempalte_details, loop, *args, **kwargs):
      lt_details = {}
      launch_template_ids = []

      for version, template_ids in launch_tempalte_details.items():
          for id in template_ids:
            if lt_details.get(id) is None:
              launch_template_ids.append(id)
              lt_details[id] = {
                "versions": {
                  version.lower(): await self.process_account_region_asgInstances_get_launchtemplate_version(ec2_client, id, version) 
                }
              }           
              continue
              
            if version in lt_details[id]["versions"]:
              continue
            
            lt_details[id]["versions"][version] = await self.process_account_region_asgInstances_get_launchtemplate_version(ec2_client, id, version) 
      
      launch_templates_details = { item["LaunchTemplateId"]:item for item in self.get_cloud_client().general_boto_call_array(
            boto_call=lambda item: ec2_client.describe_launch_templates(**item),
            boto_params={"LaunchTemplateIds": launch_template_ids },
            boto_nextkey = "NextToken",
            boto_key="LaunchTemplates"
        )}
      
      get_last5_tasks = []
      for id, details in lt_details.items():
        details["template"] = launch_templates_details[id]
        if "$latest" not in details["versions"]:
          details["versions"]["$latest"] = (await self.process_account_region_asgInstances_get_launchtemplate_version(ec2_client, id, "$Latest"))
          

        if "$default" not in details["versions"]:
          details["versions"]["$default"] = (await self.process_account_region_asgInstances_get_launchtemplate_version(ec2_client, id, "$Default"))

        
        latest_version = details["versions"]["$latest"]["VersionNumber"]
        default_version = details["versions"]["$default"]["VersionNumber"]

        if default_version not in details["versions"]:
          details["versions"][default_version] = details["versions"]["$default"]
        try:
          if latest_version not in details["versions"]:
            details["versions"][latest_version] = details["versions"]["$latest"]
        except:
            print(latest_version)
            print(details)
            raise

        get_last5_tasks.append(loop.create_task(self.process_account_region_asgInstances_get_launchtemplate_getversionlast5(ec2_client=ec2_client, id=id, latest_version=latest_version)))
        
      if len(get_last5_tasks) < 1:
        return lt_details
        
      await asyncio.wait(get_last5_tasks)
      for task in get_last5_tasks:
        versions = task.result()
        for version in versions:
          if version["VersionNumber"] in lt_details[version["LaunchTemplateId"]]["versions"]:
            continue

          lt_details[version["LaunchTemplateId"]]["versions"][version["VersionNumber"]] = version
      
      return lt_details
  
  async def process_account_region_asgInstances_get_launchconfigs(self, auto_scaling_client, launch_configuration_names = None):
    boto_params = {}

    if launch_configuration_names is not None and len(launch_configuration_names) < 1:
      return {}
        
    if launch_configuration_names is not None:
      boto_params["LaunchConfigurationNames"] = launch_configuration_names
    
    return {config["LaunchConfigurationName"]:config for config in  self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: auto_scaling_client.describe_launch_configurations(**item),
      boto_params= boto_params,
      boto_nextkey = "NextToken",
      boto_key="LaunchConfigurations"
    ) } 
  
  def __get_launch_template_version(self, launch_template_details, *args, **kwarg):
    return launch_template_details["Version"] if launch_template_details.get("Version") is not None else "$Default"
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    auto_scaling_client = self.get_cloud_client().get_boto_client(
      client= "autoscaling",
      account= account,
      region= region
    )

    ec2_client = self.get_cloud_client().get_boto_client(
      client= "ec2",
      account= account,
      region= region
    )

    groups = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: auto_scaling_client.describe_auto_scaling_groups(**item),
      boto_params={ },
      boto_nextkey = "NextToken",
      boto_key="AutoScalingGroups"
    )

    launch_configuration_names = []
    launch_tempalte_details = {}
    for g in groups:
      if 'LaunchConfigurationName' in g:
        launch_configuration_names.append(g['LaunchConfigurationName'])
        continue
      
      if 'MixedInstancesPolicy' in g and 'LaunchTemplate' not in g:
        g['LaunchTemplate'] = g['MixedInstancesPolicy']['LaunchTemplate']['LaunchTemplateSpecification']

      if 'LaunchTemplate' in g:
        template_version = self.__get_launch_template_version(g['LaunchTemplate'])
        if launch_tempalte_details.get(template_version) is None:
          launch_tempalte_details[template_version] = []
        launch_tempalte_details[template_version].append(g['LaunchTemplate']["LaunchTemplateId"])
        continue

        

    task_deployconfig = {
      "config": loop.create_task(self.process_account_region_asgInstances_get_launchconfigs(auto_scaling_client, launch_configuration_names)),
      "template": loop.create_task(self.process_account_region_asgInstances_get_launchtemplates(ec2_client, launch_tempalte_details, loop))
    }

    await asyncio.wait(task_deployconfig.values())

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": [
          self.get_common().helper_type().dictionary().merge_dictionary([
            {},
            {
              "extra_launchconfig": self.get_common().helper_type().dictionary().merge_dictionary([
                {},
                {"extra_image": await self.__getImageInfo(image_id= task_deployconfig["config"].result().get(item['LaunchConfigurationName'])["ImageId"])},
                task_deployconfig["config"].result().get(item['LaunchConfigurationName'])
              ]) if item.get('LaunchConfigurationName') is not None else {},
              "extra_launchtemplate": task_deployconfig["template"].result().get(item['LaunchTemplate']["LaunchTemplateId"]) if item.get('LaunchTemplate') is not None else {},
            },
            item
          ]) for item in groups
        ]
    }
