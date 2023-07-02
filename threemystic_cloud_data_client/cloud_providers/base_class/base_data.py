from threemystic_common.base_class.base_provider import base
from abc import abstractmethod
import asyncio, concurrent.futures, socket, errno
from tqdm.asyncio import tqdm

class cloud_data_client_provider_base_data(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)   
    
    self._set_cloud_data_client(*args, **kwargs)
    self._set_client_name(*args, **kwargs)
    self._set_resource_uniqueid_lambda(*args, **kwargs)
    self._set_max_process_pool(*args, **kwargs)
    self._set_max_thread_pool(*args, **kwargs)
    self._set_data_start(*args, **kwargs)

  @abstractmethod
  def get_accounts(self):
    pass
  
  @abstractmethod
  async def _process_account_data(self, **kwargs):
    raise Exception("_process_account_data is not DEFINED")
  
  def get_data_start(self, *args, **kwargs):
    return self.__data_start
  
  def _set_data_start(self, *args, **kwargs):
    self.__data_start = self.get_common().helper_type().datetime().get()

  def get_max_process_pool(self, *args, **kwargs):
    return self._max_process_pool
  
  def _set_max_process_pool(self, max_thread_pool = 5, *args, **kwargs):
    self._max_process_pool = max_thread_pool

  def get_max_thread_pool(self, *args, **kwargs):
    return self._max_thread_pool
  
  def _set_max_thread_pool(self, max_thread_pool = 35, *args, **kwargs):
    self._max_thread_pool = max_thread_pool
  
  def get_cloud_client(self, *args, **kwargs):
    return self._get_cloud_data_client_raw().get_cloud_client()
  
  def _get_cloud_data_client_raw(self, *args, **kwargs):
    return self._cloud_data_client
  
  def get_cloud_data_client(self, *args, **kwargs):
    return self._get_cloud_data_client_raw().get_cloud_data_client()
  
  def _set_cloud_data_client(self, cloud_data_client, *args, **kwargs):
    self._cloud_data_client = cloud_data_client

  def get_client_name(self, *args, **kwargs):
    return self._client_name
  
  def _set_client_name(self, data_action, *args, **kwargs):
    self._client_name = f"{self.get_provider()}-{data_action}-data"

  def get_resource_uniqueid_lambda(self, *args, **kwargs):
    return self._uniqueid_lambda
  
  def _set_resource_uniqueid_lambda(self, uniqueid_lambda, *args, **kwargs):
    self._uniqueid_lambda = uniqueid_lambda
  
  async def _pre_load_main_process(self, *args, **kwargs):
    pass
  
  def get_base_return_data(self, account= None, resource_id = None, resource = None, region= None, resource_groups= None, *args, **kwargs):
    return self.get_common().helper_type().dictionary().merge_dictionary([
      {},
      {
        "extra_account": self.get_cloud_client().serialize_azresource(resource= account),
        "extra_region": (
          region if not None else (
            self.get_cloud_client().get_azresource_location(resource= resource) if resource is not None else None)),
        "extra_resourcegroups": resource_groups,
        "extra_id": (
          resource_id if not None else (
            self.get_cloud_client().get_azresource_location(resource= resource) if resource is not None else (
            self.get_cloud_client().get_account_id(account= account) if account is not None else  None))),
      },
      self.get_cloud_client().serialize_azresource(resource= resource) if resource is not None else self.get_cloud_client().serialize_azresource(resource= account)
    ])
  
  def format_results(self, results, output_format = None, *args, **kwargs):        
    if output_format is None or (self.get_common().helper_type().string().set_case(string_value= output_format, case= "lower") not in self.get_supported_output_format()):
      output_format = "json"
    
    try:
      if output_format == "yaml":
        print(self.get_common().helper_yaml().dumps(data= results))
        return
        # print(results)
        # work in progress
        # from tabulate import tabulate
        # tablulate_data = []
        # headers = None
        # for _, item_data in results.items():
        #   if len(item_data) > 0 and headers is None:
        #     headers = [key for key in item_data[0].keys()]
        #   for data in item_data:
        #     tablulate_data += [ (val if self.common.is_numeric(val) or self.common.is_type(val, str) else json.dumps(val, default=self.common.json_dumps_serializable_default))  for val in data.values() ] 
        # print(tablulate_data)
        # print (tabulate(
        #   tabular_data= tablulate_data, 
        #   headers= headers,
        # ))
      
      print( self.get_common().helper_json().dumps(data= results, indent=2))
      return
        
    
    
      
    except socket.error as e:
      if e.errno != errno.EPIPE:
        raise

  async def __main_poolexecutor(self, *args, **kwargs):   
    with concurrent.futures.ThreadPoolExecutor(self.get_max_thread_pool()) as pool:
        return await self.main_process(
          pool= pool,
          **kwargs
        )
  
  def get_runparam_key(self, data_key, default_value = {}, *args, **kwargs):

    if data_key is not None and data_key in self.__run_params:
      if self.get_common().helper_type().general().is_type(obj= self.__run_params.get(data_key), type_check= type(default_value)):
        return self.__run_params.get(data_key)
    
    return default_value
  
  def _set_run_params(self, run_params = None, *args, **kwargs):
    if run_params is None:
      self.__run_params = {}
      return
    
    if not self.get_common().helper_type().general().is_type(obj= run_params, type_check= dict):
      self.__run_params = {}
      return
    
    if "data_action" in run_params:
      del run_params["data_action"]
    
    self.__run_params = self.get_common().helper_type().dictionary().merge_dictionary([
      {},
      {
        "data_filter": {},
        "data_hideempty": False,
        "data_accounts": None
      },
      run_params
    ])

    if self.__run_params.get("data_accounts") is not None:
      if not self.get_common().helper_type().general().is_type(obj= self.__run_params.get("data_accounts"), type_check= str):
        self.__run_params["data_accounts"] = self.get_common().helper_type().string().split(string_value= self.__run_params.get("data_accounts"), separator= "[,;]")

    if not self.get_common().helper_type().general().is_type(obj= self.__run_params.get("data_accounts"), type_check= list):
      self.__run_params["data_accounts"] = []
      
    if self.__run_params["data_accounts"] is None:
      self.__run_params["data_accounts"] = []
  
  
  def _process_data_filter_condition_in(self, condition, condition_value, data_value, *args, **kwargs):
    condition_settings = self._process_data_filter_condition_settings("in", condition)

    if condition_settings.get("case_insensitive") is True:
      data_value = self.get_common().helper_type().string().set_case(string_value= data_value, case= "lower")
      if self.get_common().helper_type().general().is_type(obj= condition_value, type_check= str):
        condition_value = self.get_common().helper_type().string().set_case(string_value= value, case= "lower")
      elif self.get_common().helper_type().general().is_type(obj= condition_value, type_check= list):
        condition_value = [self.get_common().helper_type().string().set_case(string_value= value, case= "lower") for value in condition_value]
      else:
        raise self.get_common().exception().exception(
          exception_type = "argument"
        ).not_implemented(
          logger= self.get_common().get_logger(), 
          name = "condition_value",
          message = f"condition_value should be either string or list: condition_value - {type(condition_value)}"
        )

    if condition_settings.get("not") is True:
      return data_value not in condition_value
    
    return data_value in condition_value
  
  def _process_data_filter_condition_less_than(self, condition, condition_value, data_value, *args, **kwargs):
    condition_settings = self._process_data_filter_condition_settings("lt", condition)

    if condition_settings.get("case_insensitive") is True:
      data_value = self.get_common().helper_type().string().set_case(string_value= data_value, case= "lower")
      condition_value = self.get_common().helper_type().string().set_case(string_value= condition_value, case= "lower")

    if condition_settings.get("not") is True and condition_settings.get("equals") is False:
      return not (data_value < condition_value)
    
    if condition_settings.get("not") is True and condition_settings.get("equals") is True:
      return not (data_value <= condition_value)
    
    if condition_settings.get("equals") is True:
      return (data_value <= condition_value)
    
    return data_value < condition_value
  
  def _process_data_filter_condition_greater_than(self, condition, condition_value, data_value, *args, **kwargs):
    condition_settings = self._process_data_filter_condition_settings("gt", condition)

    if condition_settings.get("case_insensitive") is True:
      data_value = self.get_common().helper_type().string().set_case(string_value= data_value, case= "lower")
      condition_value = self.get_common().helper_type().string().set_case(string_value= condition_value, case= "lower")

    if condition_settings.get("not") is True and condition_settings.get("equals") is False:
      return not (data_value > condition_value)
    
    if condition_settings.get("not") is True and condition_settings.get("equals") is True:
      return not (data_value >= condition_value)
    
    if condition_settings.get("equals") is True:
      return (data_value >= condition_value)
    
    return data_value > condition_value
  
  def _process_data_filter_condition_equals(self, condition, condition_value, data_value, *args, **kwargs):
    
    condition_settings = self._process_data_filter_condition_settings("equals", condition)

    if condition_settings.get("case_insensitive") is True:
      data_value = self.get_common().helper_type().string().set_case(string_value= data_value, case= "lower")
      condition_value = self.get_common().helper_type().string().set_case(string_value= condition_value, case= "lower")

    if condition_settings.get("not") is True:
      return data_value != condition_value
    
    return data_value == condition_value
    
  
  
  def _process_data_filter_condition_settings(self, condition, condition_value, *args, **kwargs):
    condition_settings = {
      "not": False,
      "case_insensitive": False,
      "equals": False
    }
    if condition == condition_value:
      return condition_settings
    
    while condition != condition_value:
      if condition_value[0:3] == "not":
        condition_settings["not"] = True
        condition_value=condition_value[3:]
        continue
      if condition_value[0:1] == "i":
        condition_settings["case_insensitive"] = True
        condition_value=condition_value[1:]
        continue
      if condition_value[0:1] == "e":
        condition_settings["equals"] = True
        condition_value=condition_value[1:]
        
      break

    return condition_settings
    

  def _process_data_filter_condition(self, condition, data_item, *args, **kwargs):
    if condition is None:
      return True
    
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= condition.get("condition")):
      return True

    key_value = condition.get("key")
    if key_value is None:
      return True
    if self.get_common().helper_type().general().is_type(obj= key_value, type_check= str):
      if self.get_common().helper_type().string().is_null_or_whitespace(string_value= key_value):
        return True

    condition_operator = self.get_common().helper_type().string().set_case(string_value= condition.get("condition"), case= "lower")
    data_value = self.get_common().helper_type().general().get_container_value(container= data_item, value_key= key_value)
    
    if condition_operator.endswith("equals"):
      return self._process_data_filter_condition_equals(condition= condition_operator, condition_value= condition.get("value"), data_value= data_value)
    
    if condition_operator.endswith("gt"):
      return self._process_data_filter_condition_greater_than(condition= condition_operator, condition_value= condition.get("value"), data_value= data_value)
    
    if condition_operator.endswith("lt"):
      return self._process_data_filter_condition_less_than(condition= condition_operator, condition_value= condition.get("value"), data_value= data_value)
    
    if condition_operator.endswith("in"):
      return self._process_data_filter_condition_in(condition= condition_operator, condition_value= condition.get("value"), data_value= data_value)
    
    if condition_operator.endswith("and"):
      if condition.get("filters") is None:
        return True
      if self.get_common().helper_type().general().is_type(obj= condition.get("filters"), type_check= dict):
        condition["filters"] = [condition.get("filters")]
      
      running_value = True
      for filter in condition.get("filters"):
        running_value = running_value and self._process_data_filter_condition(
          condition= filter,
          data_item= data_item
        )
      
      return running_value
    
    if condition_operator.endswith("or"):
      if condition.get("filters") is None:
        return True
      if self.get_common().helper_type().general().is_type(obj= condition.get("filters"), type_check= dict):
        condition["filters"] = [condition.get("filters")]
      
      running_value = False
      for filter in condition.get("filters"):
        running_value = running_value or self._process_data_filter_condition(
          condition= filter,
          data_item= data_item
        )
      
      return running_value


  def _process_data_filter_is_row_valid(self, data_item, *args, **kwargs):
    data_filter = self.get_runparam_key(data_key= "data_filter", default_value= {})
    if len(data_filter) < 1:
      return True
    
    return self._process_data_filter_condition(condition= data_filter, data_item= data_item)
    

  def _process_data_filter(self, data, *args, **kwargs):
    if len(self.get_runparam_key(data_key= "data_filter", default_value= {})) < 1:
      return data
    
    return [data_item for data_item in data if self._process_data_filter_is_row_valid(data_item= data_item)]


  async def main(self, pool= None, run_params = None, *args, **kwargs):   
    self._set_run_params(run_params= run_params)
    if pool == None:
      return await self.__main_poolexecutor(*args, **kwargs)
    
    return await self.main_process(
          pool= pool,
          **kwargs
        )
  
  async def _progressbar_close(self, progressbar):
    if progressbar is None:
      return
    
    await self._progressbar_update(progressbar)
    progressbar.close()
    await asyncio.sleep(.25)

  async def _progressbar_update(self, progressbar, update_count = None):
    if progressbar is None:
      return
    
    if update_count is None:
      progressbar.update()  
      return

    progressbar.update(n=update_count)

  async def _process_done_all_complete(self, pending_tasks, timeout = None, *args, **kwargs):
    done_tasks, pending_tasks = await asyncio.wait(pending_tasks, timeout= timeout, return_when= asyncio.ALL_COMPLETED)
    
    return {
      "done": [task_done for task_done in done_tasks],
      "tasks": [task_pending for task_pending in pending_tasks]
    } 

  async def _process_done_first_complete(self, pending_tasks, timeout = .25, *args, **kwargs):

    done_tasks, pending_tasks = await asyncio.wait(pending_tasks, timeout= timeout, return_when= asyncio.FIRST_COMPLETED)

    return {
      "done": [task_done for task_done in done_tasks],
      "tasks": [task_pending for task_pending in pending_tasks]
    }
  
  async def _process_done_auto(self, pending_tasks, timeout = .25, return_when = asyncio.FIRST_COMPLETED, *args, **kwargs):
    if return_when == asyncio.FIRST_COMPLETED:
      return await self._process_done_first_complete(pending_tasks= pending_tasks, timeout= timeout)
    
    return await self._process_done_all_complete(pending_tasks= pending_tasks, timeout= timeout)
  
  async def process_done(self, pending_tasks, account_progress = None, timeout = .25, return_when = asyncio.FIRST_COMPLETED, *args, **kwargs):
    if len(pending_tasks) < 1:
      return {
        "tasks": pending_tasks,
        "tasks_processed": [],
        "done_count": 0,
      }
    
    done_results = await self._process_done_auto(pending_tasks= pending_tasks, timeout= timeout, return_when= return_when)
    done_count = len(done_results["done"])

    if done_count > 0 and account_progress is not None:
      await self._progressbar_update(progressbar= account_progress, update_count= done_count)
      
    return {
        "tasks": done_results["tasks"],
        "tasks_processed": done_results["done"],
        "done_count": done_count,
    }
  
  async def _process_account(self, *args, **kwargs):
    return await self._process_account_data(*args, **kwargs)
  
  async def process_account(self, *args, **kwargs):
    return await self._process_account(*args, **kwargs)
  
  def process_account_sync(self, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    results =  loop.run_until_complete(self.process_account(loop= loop, *args, **kwargs))
    loop.close()
    return results
  
  async def main_process(self, pool, loop= None, *args, **kwargs):    
    
    print(f"Running: {self.get_client_name()} - {self.get_data_start()}")

    await self._pre_load_main_process(pool= pool)

    accounts = self.get_accounts(*args, **kwargs)

    tasks = []
    tasks_processed = []
    if loop is None:
      loop = asyncio.get_event_loop()

    for account in accounts:
      tasks.append(loop.run_in_executor(pool, lambda item:self.process_account_sync(**item), {"account":account, "pool":pool}))

    finalized_results = await self.get_common().helper_parallel_processing().ensure_all_tasks_complete(
      done_function= self.process_done,
      done_function_params = {"pending_tasks": tasks, "account_progress": None, "timeout": None, "return_when": asyncio.ALL_COMPLETED, "loop": loop},
      total_tasks= len(accounts),
      current_running_total=0
    )

    for finalized_result in finalized_results["process_result_data"]:
      tasks_processed += (finalized_result["tasks_processed"])

    return_data = {}
    for task in tasks_processed:
      if task.result() is None or (task.result() is not None and len(task.result()) < 1):
        continue
      
      if task.result().get("account") is None:
        continue
      
      task.result()["data"]= self._process_data_filter(data= task.result()["data"])
      if self.get_runparam_key(data_key= "data_hideempty", default_value= False) is True and len(task.result()["data"]) < 1:
        continue

      
      if return_data.get(self.get_cloud_client().get_account_id(account= task.result()["account"])) is None:
        return_data[self.get_cloud_client().get_account_id(account= task.result()["account"])] = task.result()["data"]
        continue
      
      return_data[self.get_cloud_client().get_account_id(account= task.result()["account"])] += task.result()["data"]
      
    return return_data

  
  
    

  
  

