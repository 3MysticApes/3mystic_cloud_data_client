from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from decimal import Decimal, ROUND_HALF_UP
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import GranularityType,ForecastDefinition,ForecastType,ForecastTimeframe,ForecastTimePeriod,QueryDefinition,TimeframeType,ExportType,QueryTimePeriod


class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="budget", 
      logger_name= "cloud_data_client_azure_client_action_budget", 
      uniqueid_lambda = lambda: True
      *args, **kwargs)
  
  def __process_get_cost_generate_data(self, account, client, filter, is_forcast = False, *args, **kwargs):
    if not is_forcast:
      return client.query.usage(
            scope= f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
            parameters= QueryDefinition(**filter)
          )

    return client.forecast.usage(
      scope= f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
      parameters= ForecastDefinition(**filter)
    )    
  async def __process_get_cost_generate_total(self, account, client, filter, is_forcast = False, *args, **kwargs):
    account_total = Decimal(0)
    try:
      account_usage = self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: self.__process_get_cost_generate_data(account= account, client= client, filter= filter, is_forcast= is_forcast)  
      )
      
      print(account_usage)
      for row in account_usage.rows:
        print(row)
        account_total += Decimal(row[0])
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return None
    finally:
      return account_total.quantize(Decimal('.01'), ROUND_HALF_UP) if self.get_common().helper_type().general().is_type(obj=account_total, type_check= Decimal) else account_total
  
  async def __process_get_cost_data_last_month(self, total_by_month, *args, **kwargs):
    last_month_year = self.get_data_start().year
    last_month_month = self.get_data_start().month - 1
    if last_month_month < 1:
      last_month_month = 12
      last_month_year -= 1
    
    if total_by_month is not None and total_by_month.get(f'{last_month_month}') is not None:
      return total_by_month.get(f'{last_month_month}')
    
    filter = {
      'type': ExportType.AMORTIZED_COST,
      'timeframe': TimeframeType.CUSTOM,
      'time_period': QueryTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{last_month_year}-{self.get_common().helper_type().datetime().get_month_as_2digits(month= last_month_month)}-01T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{last_month_year}-{self.get_common().helper_type().datetime().get_month_as_2digits(month=last_month_month)}-{self.get_common().helper_type().datetime().get_day_as_2digits(day=self.get_common().helper_type().datetime().last_day_month_day(month= last_month_month))}T23:59:59+00:00")      
      ),      
      'dataset': {
        'aggregation': {
          'totalCost': {
            'name': 'Cost',
            'function': 'Sum'
          }
        },
        'grouping': [
          {
            'type': 'Dimension',
            'name': 'SubscriptionId'
          }
        ]
      }
    }
    return await self.__process_get_cost_generate_total(filter= filter, *args, **kwargs)
  
  async def __process_get_cost_data_forcast_year(self, account, fiscal_year_start, *args, **kwargs):
    fiscal_year_end = self.get_common().helper_type().datetime().yesterday(dt= fiscal_year_start)
    fiscal_year_end = self.get_common().helper_type().datetime().datetime_from_string(
      dt_string= f"{fiscal_year_end.year+1}/{self.get_common().helper_type().datetime().get_month_as_2digits(month=fiscal_year_end.month)}/{self.get_common().helper_type().datetime().get_day_as_2digits(day=fiscal_year_end.day)}",
      dt_format= "%Y/%m/%d"
    )
    filter = {
      'type': ForecastType.AMORTIZED_COST,
      'timeframe': ForecastTimeframe.CUSTOM,
      'time_period': ForecastTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_data_start().year}-{self.get_common().helper_type().datetime().get_month_as_2digits(month=self.get_data_start().month)}-01T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{fiscal_year_end.year}-{self.get_common().helper_type().datetime().get_month_as_2digits(month=fiscal_year_end.month)}-{self.get_common().helper_type().datetime().get_day_as_2digits(day=fiscal_year_end.day)}T23:59:59+00:00")      
      ),      
      'dataset': {
        'granularity': GranularityType.DAILY,
        'aggregation': {
          'totalCost': {
            'name': 'Cost',
            'function': 'Sum'
          }
        },
        'grouping': [
          {
            'type': 'Dimension',
            'name': 'SubscriptionId'
          }
        ]
      }
    }

    try:
      usage = self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: self.__process_get_cost_generate_data(account= account, filter= filter, is_forcast= True, *args, **kwargs)  
      )
      if usage is None:
        return usage

      return await self.__process_get_cost_data_daily_data(usage= usage)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return None
    
  async def __process_get_cost_data_ytd(self, account, fiscal_year_start, *args, **kwargs):
    yesterday = self.get_common().helper_type().datetime().yesterday()
    if yesterday.month != self.get_data_start().month:
      return None
    if yesterday < fiscal_year_start:
      fiscal_year_start = self.get_common().helper_type().datetime().datetime_from_string(
        dt_string= f"{self.get_data_start().year-1}/{fiscal_year_start}",
        dt_format= "%Y/%m/%d"
      )
      
    filter = {
      'type': ExportType.AMORTIZED_COST,
      'timeframe': TimeframeType.CUSTOM,
      'time_period': QueryTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_data_start().year}-{self.get_common().helper_type().datetime().get_month_as_2digits(month= fiscal_year_start.month)}-{self.get_common().helper_type().datetime().get_day_as_2digits(day= fiscal_year_start.day)}T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_data_start().year}-{self.get_common().helper_type().datetime().get_month_as_2digits(month= yesterday.month)}-{self.get_common().helper_type().datetime().get_day_as_2digits(day= yesterday.day)}T23:59:59+00:00")      
      ),
      'dataset': {
        'granularity': GranularityType.DAILY,
        'aggregation': {
          'totalCost': {
            'name': 'Cost',
            'function': 'Sum'
          }
        },
        'grouping': [
          {
            'type': 'Dimension',
            'name': 'SubscriptionId'
          }
        ]
      }
    }
    try:
      usage = self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: self.__process_get_cost_generate_data(account= account, filter= filter, is_forcast= False, *args, **kwargs)  
      )

      if usage is None:
        return {}

      return await self.__process_get_cost_data_daily_data(usage= usage)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return None
  
  async def __process_get_cost_data_daily_data(self, usage, *args, **kwargs):
    total = Decimal(0)
    by_month = { f"{month}":None for month in range(1, 13)}
    by_day = { }
    max_date = 0
    for cost_data in usage.rows:
      month = f'{self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(cost_data[1]), dt_format= "%Y%m%d").month}'
      if by_month.get(month) is None:
        by_month[month] = 0
      by_month[month] += Decimal(cost_data[0])
      total += Decimal(cost_data[0])
      by_day[str(cost_data[1])] = Decimal(cost_data[0])
      if cost_data[1] > max_date:
        max_date = cost_data[1]
    
    last_seven_day_total = Decimal(0)
    seven_days_ago = self.get_common().helper_type().datetime().time_delta(
      dt= self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(max_date), dt_format= "%Y%m%d"),
      days= -6)
    for day in range(0,7):
      date_string = self.get_common().helper_type().datetime().datetime_as_string(
        dt= self.get_common().helper_type().datetime().time_delta(dt= seven_days_ago, days= day),
        dt_format= "%Y%m%d"
      )
      if by_day.get(date_string) is not None:
        last_seven_day_total += by_day.get(date_string)

    return {
      "total": total.quantize(Decimal('.01'), ROUND_HALF_UP),
      "by_month": {month:value.quantize(Decimal('.01'), ROUND_HALF_UP) for month, value in by_month.items() if value is not None},
      "last_seven_days": last_seven_day_total.quantize(Decimal('.01'), ROUND_HALF_UP),
    }

  def __process_get_cost_calculate_forecast_total(self, current_total, forecast_total, *args, **kwargs):
    if current_total is None and forecast_total is None:
      return None
    
    return forecast_total if current_total is None else current_total

  async def __process_get_cost_data(self, loop, fiscal_year_start, *args, **kwargs):
    fiscal_year_start_date = self.get_common().helper_type().datetime().datetime_from_string(
      dt_string= f"{self.get_data_start().year}/{fiscal_year_start}",
      dt_format= "%Y/%m/%d"
    )

    processed_ytd_data = await self.__process_get_cost_data_ytd(fiscal_year_start= fiscal_year_start_date, *args, **kwargs )
    processed_year_forecast = await self.__process_get_cost_data_forcast_year(fiscal_year_start= fiscal_year_start_date, *args, **kwargs )

    if processed_ytd_data is None and processed_year_forecast is None:
      return {
      "year_to_date": None,  
      "year_forecast": None,
      "month_to_date": None,  
      "month_forecast": None,
      "last_seven_days": None,
      "last_month": None,
    }
    return_data = {
      "year_to_date": processed_ytd_data.get("total") if processed_ytd_data is not None else None,      
      "year_forecast": self.__process_get_cost_calculate_forecast_total(
        current_total= processed_ytd_data.get("total") if processed_ytd_data is not None else None,
        forecast_total= processed_year_forecast.get("total") if processed_year_forecast is not None else None),
      "month_to_date": processed_ytd_data.get("by_month").get(f'{self.get_data_start().month}') if processed_ytd_data is not None and processed_ytd_data.get("by_month") else None,      
      "month_forecast": self.__process_get_cost_calculate_forecast_total(
        current_total= processed_ytd_data.get("by_month").get(f'{self.get_data_start().month}') if processed_ytd_data is not None and processed_ytd_data.get("by_month") else None,
        forecast_total= processed_year_forecast.get("by_month").get(f'{self.get_data_start().month}') if processed_year_forecast is not None and processed_year_forecast.get("by_month") else None),
      "last_seven_days": processed_ytd_data.get("last_seven_days") if processed_ytd_data is not None else None,  
    }
    pending_tasks = {
      "last_month": loop.create_task(self.__process_get_cost_data_last_month(
      total_by_month= processed_ytd_data.get("by_month") if processed_ytd_data is not None else None, 
      *args, **kwargs ))
    }    

    await asyncio.wait(pending_tasks.values())
    for key, task in pending_tasks.items():
      return_data[key] = task.result()
  
    return return_data

  async def _process_account_data(self, account, loop, *args, **kwargs):
    

    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= kwargs.get("fiscal_year_start")):
      kwargs["fiscal_year_start"] = self.get_cloud_data_client().get_default_fiscal_year_start()
    
    costmanagement_client = CostManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
  
    cost_data = {
      key:value for key,value in (await self.__process_get_cost_data(account= account, client= costmanagement_client, loop= loop, *args, **kwargs)).items()
    }

    return {
      "account": account,
      "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        self.get_base_return_data(
          account= self.get_cloud_client().serialize_azresource(resource= account),
          resource_id =  f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
        ),
        cost_data
      ])]
    }