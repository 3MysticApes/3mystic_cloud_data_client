from threemystic_common.base_class.base_provider import base
import abc
import asyncio, concurrent.futures, math
from tqdm.asyncio import tqdm

class cloud_data_client_provider_base_data(base):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    
    
    self._set_cloud_client(*args, **kwargs)
    self._set_client_name(*args, **kwargs)
    self._set_resource_uniqueid_lambda(*args, **kwargs)
    self._set_max_process_pool(*args, **kwargs)
    self._set_max_thread_pool(*args, **kwargs)
    self._set_data_start(*args, **kwargs)

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
    return self._cloud_client
  
  def _set_cloud_client(self, cloud_client, *args, **kwargs):
    self._cloud_client = cloud_client

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
  
  @abc.abstractmethod
  def get_accounts(self):
    pass

  async def __main_poolexecutor(self, *args, **kwargs):   
    with concurrent.futures.ThreadPoolExecutor(self.get_max_thread_pool()) as pool:
        return await self.main_process(
          pool= pool,
          **kwargs
        )

  async def main(self, pool= None, *args, **kwargs):   
    if pool == None:
      return await self.__main_poolexecutor(*args, **kwargs)
    
    return await self.main_process(
          pool= pool,
          **kwargs
        )
  
  async def main_process(self, pool, loop= None, *args, **kwargs):    
    
    print(f"Running: {self.get_client_name()} - {self.get_data_start()}")

    await self._pre_load_main_process(pool= pool)

    accounts = self.get_accounts()

    print("accounts")
    for account in accounts:
      print(f"{self.get_cloud_client().get_account_name(account= account)} - {self.get_cloud_client().get_account_id(account= account)}")

    
    # tasks = []
    # progressbar_tasks = []
    # tasks_processed = []
    # last_time = datetime.utcnow()
    # running_done_count = 0

    # account_progress = None
    # account_queprogress = None

    # if self._show_output("main"):
    #   account_queprogress = tqdm(range(len(accounts)), desc=f"{self.client_name} - qued (Accounts)     ")
    #   account_progress = tqdm(range(len(accounts)), desc=f"{self.client_name} - processed (Accounts)")
    
    # if loop is None:
    #   loop = asyncio.get_event_loop()

    # for account in accounts:
    #   if self._show_output("verbose"):
    #     print(f'Account {account["Name"]} ({account["Id"]}) has been queued', flush= True)

    #   tasks.append(loop.run_in_executor(pool, lambda item:self.process_account_sync(**item), {"account":account, "pool":pool}))
    #   if not self._show_output("verbose"):
    #     progressbar_tasks.append(loop.create_task(self.progressbar_update(progressbar= account_queprogress, update_count= 1)))

    #   if (datetime.utcnow() - last_time).total_seconds() > 60 or (len(tasks) > 0 and len(tasks) >= self.get_asyncio_max_concurrent() ):

    #     if self._show_output("verbose"):
    #       print("Running Time Main group: {}".format((datetime.utcnow() - self.data_start)), flush= True)
    #       print("Accounts Processed {} / {}".format(running_done_count, len(accounts)), flush= True)
        
    #     if len(tasks) < 1:
    #       last_time = datetime.utcnow()
    #       continue

    #     while (datetime.utcnow() - last_time).total_seconds() > 60 or len(tasks) >= (self.get_asyncio_max_concurrent() - 1):
    #       last_time = datetime.utcnow()
    #       if len(tasks) > 0:
    #         await asyncio.sleep(.5)

    #       process_result = (await self.process_done(pending_tasks= tasks, account_progress= account_progress, loop= loop))
    #       running_done_count += process_result["done_count"]
    #       tasks = process_result["tasks"]
    #       tasks_processed += process_result["tasks_processed"]
    
    # if len(progressbar_tasks) > 0:
    #   await asyncio.wait(progressbar_tasks)
    # if self._show_output("verbose"):
    #     print("All accounts queued")

    # finalized_results = (await self.common.ensure_all_tasks_complete(
    #     done_function= self.process_done,
    #     done_function_params = {"pending_tasks": tasks, "account_progress": account_progress, "timeout": None, "return_when": asyncio.ALL_COMPLETED, "loop": loop},
    #     total_tasks= len(accounts),
    #     current_running_total=running_done_count,
    #     verbose= self._show_output("verbose")))  
    
    # if not self._show_output("verbose"):
    #     close_progressbar_tasks = {
    #       "que": loop.create_task(self.progressbar_close(progressbar= account_queprogress)),
    #       "processed": loop.create_task(self.progressbar_close(progressbar= account_progress)),
    #     }
    #     await asyncio.wait(close_progressbar_tasks.values())
          

    # for finalized_result in finalized_results["process_result_data"]:
    #   tasks_processed += (finalized_result["tasks_processed"])

    # return_data = {}
    # for task in tasks_processed:
    #   if task.result() is None or (task.result() is not None and len(task.result()) < 1):
    #     continue
      
    #   for result in task.result():
    #     if return_data.get(self.get_account_id(result["account"])) is None:
    #       return_data[self.get_account_id(result["account"])] = result["data"]
    #       continue
        
    #     return_data[self.get_account_id(result["account"])] += result["data"]
      
    # return return_data
  
  
    

  
  

