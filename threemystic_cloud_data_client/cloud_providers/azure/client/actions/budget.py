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
      uniqueid_lambda = lambda: True,
      *args, **kwargs)
    
    self._cost_dimension = ["SubscriptionId", "ResourceGroup", "ResourceType"]
  
  def __process_get_cost_generate_data(self, account, client, cost_filter, is_forcast = False, *args, **kwargs):
    if not is_forcast:
      return self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.query.usage(
          scope= f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
          parameters= QueryDefinition(**cost_filter)
        )
      )

    return self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.forecast.usage(
          scope= f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
          parameters= ForecastDefinition(**cost_filter)
        )
      )
   
  async def __process_get_cost_generate_total(self, account, client, cost_filter, is_forcast = False, *args, **kwargs):
    account_total = Decimal(0)
    try:
      account_usage = self.__process_get_cost_generate_data(account= account, client= client, cost_filter= cost_filter, is_forcast= is_forcast)
      print(account_usage.serialize())
      
      for row in account_usage.rows:
        account_total += Decimal(row[0])
      
      return account_total.quantize(Decimal('.0000'), ROUND_HALF_UP) if self.get_common().helper_type().general().is_type(obj=account_total, type_check= Decimal) else account_total
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return None
      
  
  async def __process_get_cost_data_last_month(self, total_by_month, *args, **kwargs):    
    last_month = (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(months= 1))
    if total_by_month is not None and total_by_month.get(f'{last_month.month}') is not None:
      return total_by_month.get(f'{last_month.month}')
    
    cost_filter = {
      'type': ExportType.AMORTIZED_COST,
      'timeframe': TimeframeType.CUSTOM,
      'time_period': QueryTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m', dt= last_month)}-01T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m', dt= last_month)}-{self.get_common().helper_type().datetime().get_day_as_2digits(day=self.get_common().helper_type().datetime().last_day_month_day(month= last_month.month))}T23:59:59+00:00")      
      ),      
      'dataset': {
        'aggregation': {
          'totalCost': {
            'name': 'Cost',
            'function': 'Sum'
          }
        },
        'grouping': [ 
          {"type": "Dimension", "name": dimension} for dimension in self._cost_dimension
        ]
      }
    }
    return await self.__process_get_cost_generate_total(cost_filter= cost_filter, *args, **kwargs)
  
  async def __process_get_cost_data_forcast_year(self, account, fiscal_year_start, *args, **kwargs):
    fiscal_year_end = (self.get_common().helper_type().datetime().yesterday(dt= fiscal_year_start) 
                       + self.get_common().helper_type().datetime().time_delta(years= 1, months= 1))
    
    cost_filter = {
      'type': ForecastType.AMORTIZED_COST,
      'timeframe': ForecastTimeframe.CUSTOM,
      'time_period': ForecastTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= self.get_data_start())}T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= fiscal_year_end)}T23:59:59+00:00")  
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
          {"type": "Dimension", "name": dimension} for dimension in self._cost_dimension
        ]
      }
    }

    try:
      usage = self.__process_get_cost_generate_data(account= account, cost_filter= cost_filter, is_forcast= True, *args, **kwargs)
      print(usage.serialize())

      if usage is None:
        return usage

      return await self.__process_get_cost_data_daily_data(usage= usage)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return None
    
  async def __process_get_cost_data_last_year(self, account, *args, **kwargs):
    yesterday = self.get_common().helper_type().datetime().yesterday()
    
    last_year = (self.get_common().helper_type().datetime().get()
                 + self.get_common().helper_type().datetime().time_delta(years= -1))
      
    cost_filter = {
      'type': ExportType.AMORTIZED_COST,
      'timeframe': TimeframeType.CUSTOM,
      'time_period': QueryTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= last_year)}T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= yesterday)}T23:59:59+00:00")    
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
          {"type": "Dimension", "name": dimension} for dimension in self._cost_dimension
        ]
      }
    }
    try:
      usage = self.__process_get_cost_generate_data(account= account, cost_filter= cost_filter, is_forcast= False, *args, **kwargs)

      if usage is None:
        return {}

      return await self.__process_get_cost_data_daily_data(usage= usage)
    except Exception as err:
      print(err)
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return None
  
  async def __process_get_cost_data_daily_data(self, usage, *args, **kwargs):
    by_month = { }

    column_indexs = {
      self.get_common().helper_type().string().set_case(string_value= dimension, case= "lower"):-1 for dimension in self._cost_dimension
    }
    column_indexs["cost"] = -1
    column_indexs["usagedate"] = -1
    column_indexs["currency"] = -1

    for index, data in enumerate(usage.columns[0]):
      if column_indexs.get(self.get_common().helper_type().string().set_case(string_value= data.get("name") , case= "lower")) is None:
        continue
      column_indexs[self.get_common().helper_type().string().set_case(string_value= data.get("name") , case= "lower")] = index

    for cost_data in usage.rows:
      data_dt = self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(column_indexs["usagedate"]), dt_format= "%Y%m%d")
      by_month_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m", dt= data_dt)
      day_key = self.get_common().helper_type().datetime().get_from_timestamp(dt= data_dt)
      if by_month.get(by_month_key) is None:
        by_month[by_month_key] = {
          "currency": cost_data[column_indexs["currency"]],
          "totals":{
            "total": Decimal(0),
            "resource_group": {},
            "resource_type": {}
          },
          "days":{}
        }
      
      if by_month[by_month_key]["totals"]["resource_group"].get(cost_data[column_indexs["ResourceGroup"]]) is None:
        by_month[by_month_key]["totals"]["resource_group"][cost_data[column_indexs["ResourceGroup"]]] = Decimal(0)
      
      if by_month[by_month_key]["totals"]["resource_type"].get(cost_data[column_indexs["ResourceType"]]) is None:
        by_month[by_month_key]["totals"]["resource_type"][cost_data[column_indexs["ResourceType"]]] = Decimal(0)
      
      if by_month[by_month_key]["days"].get(day_key) is None:
        by_month[by_month_key]["days"][day_key] = {
          "date": data_dt,
          "total": Decimal(0),
          "resource_group": {},
          "resource_type": {}
        }

      by_month[by_month_key]["totals"]["total"] += Decimal(cost_data[column_indexs["cost"]])
      by_month[by_month_key]["totals"]["resource_group"][cost_data[column_indexs["ResourceGroup"]]] += Decimal(cost_data[column_indexs["cost"]])
      by_month[by_month_key]["totals"]["resource_type"][cost_data[column_indexs["ResourceType"]]] += Decimal(cost_data[column_indexs["cost"]])

      
      by_month[by_month_key]["days"][day_key]["total"] += Decimal(cost_data[column_indexs["cost"]])
      by_month[by_month_key]["days"][day_key]["resource_group"][cost_data[column_indexs["ResourceGroup"]]] += Decimal(cost_data[column_indexs["cost"]])
      by_month[by_month_key]["days"][day_key]["resource_type"][cost_data[column_indexs["ResourceType"]]] += Decimal(cost_data[column_indexs["cost"]])
      
    
    return by_month

  def __process_get_cost_calculate_forecast_total(self, current_total, forecast_total, *args, **kwargs):
    if current_total is None and forecast_total is None:
      return None
    
    return forecast_total if current_total is None else current_total

  async def __process_get_cost_data(self, loop, fiscal_year_start, *args, **kwargs):
    fiscal_year_start_date = self.get_common().helper_type().datetime().datetime_from_string(
      dt_string= f"{self.get_data_start().year}/{fiscal_year_start}",
      dt_format= "%Y/%m/%d"
    )
    
    if fiscal_year_start_date > self.get_data_start():
      fiscal_year_start_date = fiscal_year_start_date + self.get_common().helper_type().datetime().time_delta(years= -1)

    

    processed_last_year_data = await self.__process_get_cost_data_last_year(fiscal_start= fiscal_year_start_date, *args, **kwargs )
    processed_year_forecast = await self.__process_get_cost_data_forcast_year(fiscal_year_start= fiscal_year_start_date, *args, **kwargs )


    return {}
    

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

    # Update this to return all days for the last year.
    # break the subscription up into resource groups.
    # ie:
    #{
    #   "Last7Days":...,
    #   "MonthToDate": ...,
    #   "MonthTotalForcast": ...,
    # 	"YearToDate": ...,
    # 	"YearTotalForcast": ...,
    #   "raw_data": {
    #     # This is done so if I wanted to have another group like resource type I could.
    #     "resource_group": [
    #       {
    #         "date": ..,
    #         "group_name": ...
    #         "amount": ...,
    #       }
    #     ]
    #   }
    # }
    return {
      "account": account,
      "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        await self.get_base_return_data(
          account= self.get_cloud_client().serialize_resource(resource= account),
          resource_id =  f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
        ),
        cost_data
      ])]
    }