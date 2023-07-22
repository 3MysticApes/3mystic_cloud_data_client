from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.vmimage import cloud_data_client_aws_client_action as vmimage_data

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="vm",
      logger_name= "cloud_data_client_aws_client_action_vm",
      *args, **kwargs)
    
    
    self.data_id_name = "InstanceId"
    
    self.arn_lambda = (lambda item: self.get_cloud_client().get_resource_general_arn(
      resource_type= "ec2",
      resource_type_sub= "instance", **item # {region, account_id, resource_id}
    ))
    
    self.auto_region_resourcebytype= ["Amazon Elastic Compute Cloud - Compute"]
    self.resource_group_filter = [
    {
      'Name': 'resource-type',
      'Values': [
        'AWS::EC2::Instance',
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
      # This is required because #the normal disk command only looks at long lived disks
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
    
  def __get_asg_extra_data(self, instance_tags = None, asg_data = None, *args, **kwargs):
    if asg_data is not None:
      return {"arn": asg_data["AutoScalingGroupARN"], "name":  asg_data["AutoScalingGroupName"]}
    
    if instance_tags is not None:
      if instance_tags.get("aws:autoscaling:groupName") is not None:
        return {"name":  instance_tags.get("aws:autoscaling:groupName")}

    return None
  
  async def __get_asg_by_instance(self, account, region, *args, **kwargs):

    auto_scaling_client = self.get_cloud_client().get_boto_client(
      client= "autoscaling",
      account= account,
      region= region
    )

    groups = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: auto_scaling_client.describe_auto_scaling_groups(**item),
      boto_params={ },
      boto_nextkey = "NextToken",
      boto_key="AutoScalingGroups",
      logger = self.get_common().get_logger()
    )

    return_data = {}

    for asg in groups:
      for instance in asg["Instances"]:
        return_data[instance["InstanceId"]] = self.__get_asg_extra_data(asg_data= asg)
    
    return return_data
  
  async def __process_account_region_lbinstances_targethealth(self, alb_client, targetgroup_arn, *args, **kwargs):
    return alb_client.describe_target_health(TargetGroupArn=targetgroup_arn)

  async def __process_account_region_lbinstances_targetgroups(self, alb_client, lb_arn, *args, **kwargs):
    return alb_client.describe_target_groups(LoadBalancerArn=lb_arn)
  
  async def __process_account_region_lbinstances(self, account, region, loop, *args, **kwargs):

      lbInstances = {}
      
      elbClassic = self.get_cloud_client().get_boto_client(
        client= "elb",
        account= account,
        region= region
      )

      elbs = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: elbClassic.describe_load_balancers(),
        boto_params={},
        boto_nextkey = None,
        boto_key="LoadBalancerDescriptions",
        logger = self.get_common().get_logger()
      )
      
      for elb in elbs:
        numInstances = len(elb['Instances'])
        if numInstances < 1:
          continue
        for i in elb['Instances']:
          if not i['InstanceId'] in lbInstances:
            lbInstances[i['InstanceId']] = {}
          if elb['LoadBalancerName'] in lbInstances[i['InstanceId']]:
            continue
          lbInstances[i['InstanceId']][elb['LoadBalancerName']] = ({"instance": i['InstanceId'], "lbType": "ELB", "lbName": elb['LoadBalancerName'], "lbDNSName": elb['DNSName']})
      
      alb = self.get_cloud_client().get_boto_client(
        client= "elbv2",
        account= account,
        region= region
      )

      albs = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: alb.describe_load_balancers(),
        boto_params={},
        boto_nextkey = None,
        boto_key="LoadBalancers",
        logger = self.get_common().get_logger()
      )
      if len(albs) < 1:
        return lbInstances

      targetGroups = { 
        lb['LoadBalancerArn']: loop.create_task(self.__process_account_region_lbinstances_targetgroups(alb_client= alb, lb_arn= lb['LoadBalancerArn'])) for lb in albs
      }
      
      if len(targetGroups) < 1:
        return lbInstances
      await asyncio.wait(targetGroups.values())
    
      for lb in albs:   
        targets_health = {
          group['TargetGroupArn']: loop.create_task(self.__process_account_region_lbinstances_targethealth(alb_client= alb, targetgroup_arn= group['TargetGroupArn'])) for group in targetGroups[lb['LoadBalancerArn']].result()['TargetGroups']
        }  
        if len(targets_health) < 1:
         continue
        await asyncio.wait(targets_health.values())     

        for _, targets in targets_health.items():
          for target in targets.result()['TargetHealthDescriptions']:
            if len(target['Target']) < 1:
              continue

            if not target['Target']['Id'] in lbInstances:
              lbInstances[target['Target']['Id']] = {}
            if lb['LoadBalancerName'] in lbInstances[target['Target']['Id']]:
              continue
            lbInstances[target['Target']['Id']][lb['LoadBalancerName']] = ({"instance": target['Target']['Id'], "lbType": "ALB", "lbName": lb['LoadBalancerName'], "lbDNSName": lb['DNSName']})        
      
      return lbInstances
  
  async def __get_ec2_volume_details(self, ec2_client, *args, **kwargs):
        
      volumne_data = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: ec2_client.describe_volumes(**item),
        boto_params={},
        boto_nextkey = "NextToken",
        boto_key="Volumes"
      )

      return { data["VolumeId"]:data for data in volumne_data }
  
  async def __getImageInfo(self, imageId):
    if imageId in self.required_extra_data["ami"]:
      return {
        "Id": imageId,
        "Name": self.required_extra_data["ami"][imageId]["Name"],
        "Description": self.required_extra_data["ami"].get("Description")
      }


    return {
      "Id": imageId,
    }
  
  async def __get_instance_attribute(self, client, instance, loop, attribute = None, *args, **kwargs):
    # Full attribute list
    # 'instanceType','kernel','ramdisk','userData','disableApiTermination','instanceInitiatedShutdownBehavior','rootDeviceName','blockDeviceMapping','productCodes','sourceDestCheck','groupSet','ebsOptimized','sriovNetSupport','enaSupport','enclaveOptions','disableApiStop'
    # to use groupSet you need to specify an interface ID when multiple interfaces are attached

    full_attribute_list = ['instanceType','kernel','ramdisk','userData','disableApiTermination','instanceInitiatedShutdownBehavior','rootDeviceName','blockDeviceMapping','productCodes','sourceDestCheck','groupSet','ebsOptimized','sriovNetSupport','enaSupport','enclaveOptions','disableApiStop']
    instance_attributes_dict = {attr.lower():attr for attr in full_attribute_list}
    if attribute is None:
      attribute = ['instanceInitiatedShutdownBehavior','disableApiTermination','disableApiStop']
      
    elif self.get_common().helper_type().general().is_type(obj=attribute, type_check=str):
      attribute = [ attr.strip() for attr in attribute.split(",") if not self.get_common().helper_type().string().is_null_or_whitespace(string_value= attribute) ]

    if len(attribute) < 1:
      return None
    
    if len(attribute) > 1:
      tasks = {
        attr.lower(): loop.create_task(self.__get_instance_attribute(client= client, instance= instance, loop= loop, attribute= attr, *args, **kwargs)) for attr in attribute

      }
      await asyncio.wait(tasks.values())
      return {attr:task.result() for attr,task in tasks.items()}


    attribute = attribute[0].lower()
    if attribute not in instance_attributes_dict:
      return None

    if attribute == "groupset" and instance.get("NetworkInterfaces") is not None and len(instance.get("NetworkInterfaces")) > 1:
        return {
          "extra_instance_attribute": instance_attributes_dict[attribute],
          "Value": "Multiple Interfaces"
        }
    try:        
      return self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        {"extra_instance_attribute": instance_attributes_dict[attribute]},
        await self.get_cloud_client().async_general_boto_call_single(
          boto_call=lambda item: client.describe_instance_attribute(**item),
          boto_params={"Attribute": instance_attributes_dict[attribute], "InstanceId": instance["InstanceId"]},
          boto_nextkey = None,
          boto_key= lambda item: item.get(self.get_common().helper_type().list().find_item(data= item.keys(), filter= lambda search: search.lower() != "instanceid" and search.lower() != "responsemetadata" )),
          error_codes_raise= ["InvalidInstanceID.NotFound"],
          logger = self.get_common().get_logger()
        )
      ])
    except Exception as ex:
      raise self.get_common().exception().exception(
        exception_type = "generic"
      ).exception(
        logger= self.get_logger(),
        name = f"Check Instance: {instance['InstanceId']} - {kwargs['account']}",
        message = f"unable to get extra_instance_attribute {instance_attributes_dict[attribute]}",
        exception= ex
      )
  
  async def __getSSMInfo(self, ssm_client, account, region, instance, filter = [], *args, **kwargs):

    if self.get_cloud_client().get_account_id(account) not in self.required_extra_data["instances_information"]:
      instances_information = self.get_cloud_client().general_boto_call_array(
        boto_call=lambda item: ssm_client.describe_instance_information(**item),
        boto_params={"Filters": filter},
        boto_nextkey = "NextToken",
        boto_key="InstanceInformationList",
        logger = self.get_common().get_logger()
      )

      self.required_extra_data["instances_information"][self.get_cloud_client().get_account_id(account)] = {instance["InstanceId"]:instance for instance in instances_information}

    if instance["InstanceId"] not in self.required_extra_data["instances_information"][self.get_cloud_client().get_account_id(account)]:
      return {}

    instance_information = self.required_extra_data["instances_information"][self.get_cloud_client().get_account_id(account)][instance["InstanceId"]]

    return {
        "PlatformName": instance_information.get('PlatformName'),
        "PlatformVersion": instance_information.get('PlatformVersion'),
        "PingStatus": instance_information.get('PingStatus'),
        "PingTime": instance_information.get('LastPingDateTime'),
        "Version": instance_information.get('AgentVersion'),
    } 
  
  async def __get_instance_withextra_data(self, ec2_client, ssm_client, task_asg_by_instance, account, region, lbInstances, instance, loop, *args, **kwargs):
      
      
      extra_data_tasks = {
        "extra_image": loop.create_task(self.__getImageInfo(imageId= instance["ImageId"])),
        "extra_instance_attributes": loop.create_task(self.__get_instance_attribute(account=account, client= ec2_client, instance=instance, loop= loop)),
        "extra_ssminfo": loop.create_task(self.__getSSMInfo(account=account, region=region, ssm_client=ssm_client, instance=instance)),
        "_ignore_extra_asg": task_asg_by_instance
        
      }      

      extra_data = {
        "extra_platform": instance["Platform"] if not self.get_common().helper_type().string().is_null_or_whitespace(string_value= instance.get("Platform")) else "Linux",
        "extra_subnet": instance["SubnetId"] if instance.get("SubnetId") is not None else "EC2Classic",
        "extra_vpc": instance["VpcId"] if instance.get("VpcId") is not None else "EC2Classic",
        "extra_lb": lbInstances.get(instance["InstanceId"]) if lbInstances is not None else None,
      }

      await asyncio.wait(extra_data_tasks.values())

      for key,item in extra_data_tasks.items():
        if key.lower().startswith("_ignore_"):
          continue
        extra_data[key]= item.result()

      extra_data["extra_asg"] = extra_data_tasks["_ignore_extra_asg"].result().get(instance["InstanceId"]) if extra_data_tasks["_ignore_extra_asg"].result() is not None else None
      if extra_data["extra_asg"] is None:
        extra_data["extra_asg"] = self.__get_asg_extra_data(instance_tags= extra_data["extra_tags"])
      
      return self.get_common().helper_type().dictionary().merge_dictionary([{}, extra_data, instance])
  
  def __is_ec2_ebs_encrypted_state(self, running_state, block_device_details):
    if block_device_details is None:
      if self.get_common().helper_type().string().is_null_or_whitespace(running_state):
          return None
      return running_state.lower()
    
    if running_state is None: 
      if not block_device_details["Encrypted"]:
        return "none"
      return "all"
    
    if running_state.lower() == "all"  and block_device_details["Encrypted"]:
      return "all"
    
    return "partial"
  
  async def __get_ec2_instances(self, ec2_client, ssm_client, task_asg_by_instance, account, region, loop, *args, **kwargs):
    instances_reservations = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: ec2_client.describe_instances(**item),
      boto_params={},
      boto_nextkey = "NextToken",
      boto_key="Reservations",
      logger = self.get_common().get_logger()
    )

    if len(instances_reservations) < 1:
      return []

    pre_process_tasks = {
      "lb_instances": loop.create_task(self.__process_account_region_lbinstances(account, region, loop, *args, **kwargs)),
      "volume_details": loop.create_task(self.__get_ec2_volume_details(ec2_client= ec2_client, *args, **kwargs))

    }
    await asyncio.wait(pre_process_tasks.values())
    
  
    instance_tasks = []

    instance_ebs_encrypted = {}
    for reservation in instances_reservations:
      for instance in reservation["Instances"]:
        if (instance["State"].get("Name")).lower() == "terminated":
          continue
        
        instance_ebs_encrypted[instance[self.data_id_name]] = None
        instance_tasks.append(loop.create_task(self.__get_instance_withextra_data(ec2_client=ec2_client, ssm_client= ssm_client, task_asg_by_instance= task_asg_by_instance, account= account, region= region, lbInstances=pre_process_tasks["lb_instances"].result(), instance= instance, loop= loop)))
        if instance.get("BlockDeviceMappings") is not None:
          for block_device in instance["BlockDeviceMappings"]:
            if block_device.get("Ebs") is None:
              instance_ebs_encrypted[instance[self.data_id_name]] = self.__is_ec2_ebs_encrypted_state(
                running_state= instance_ebs_encrypted[instance[self.data_id_name]],
                block_device_details= None
              )
              continue
            
            block_device["Ebs"]["extra_details"] = pre_process_tasks["volume_details"].result().get(block_device["Ebs"]["VolumeId"])
            instance_ebs_encrypted[instance[self.data_id_name]] = self.__is_ec2_ebs_encrypted_state(
              running_state= instance_ebs_encrypted[instance[self.data_id_name]],
              block_device_details= block_device["Ebs"]["extra_details"]
            )
          
          instance["extra_ebs_encrypted_state"] = instance_ebs_encrypted[instance[self.data_id_name]]


    await asyncio.wait(instance_tasks)
    return [ instance.result() for instance in instance_tasks]
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    ec2_client = self.get_cloud_client().get_boto_client(
      client= "ec2",
      account= account,
      region= region
    )
    ssm_client = self.get_cloud_client().get_boto_client(
      client= "ssm",
      account= account,
      region= region
    )

    task_asg_by_instance = loop.create_task(self.__get_asg_by_instance(account, region))
    tasks = {
      "instances": loop.create_task(self.__get_ec2_instances(ec2_client= ec2_client, ssm_client= ssm_client, task_asg_by_instance= task_asg_by_instance, account= account, region= region, loop= loop, **kwargs))
    }
    
    if len(tasks) > 0:
      await asyncio.wait(tasks.values())

    return {
      "region": region,
      "resource_groups": resource_groups,
      "data": []
    }
