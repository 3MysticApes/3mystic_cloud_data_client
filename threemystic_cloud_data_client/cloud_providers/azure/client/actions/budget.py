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
          parameters= ForecastDefinition(**cost_filter),
        )
      )
   
  async def __process_get_cost_data_forcast_time_range(self, account, start_date, end_date, fiscal_start, fiscal_end, query_grouping = [], *args, **kwargs):
    
    cost_filter = {
      'type': ForecastType.AMORTIZED_COST,
      'timeframe': ForecastTimeframe.CUSTOM,
      'time_period': ForecastTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= start_date)}T00:00:00+00:00"),
        to= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= end_date)}T23:59:59+00:00")
      ),
      'dataset': {
        'granularity': GranularityType.DAILY,
        'aggregation': {
          f'totalCost{self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= "upper")}': {
            'name': f'Cost{self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= "upper")}',
            'function': 'Sum'
          }
        },
        'grouping': [ 
          {"type": "Dimension", "name": dimension} for dimension in query_grouping
        ],
      }
    }

    try:
      usage = self.__process_get_cost_generate_data(account= account, cost_filter= cost_filter, is_forcast= True, *args, **kwargs)

      if usage is None:
        return usage

      return await self.__process_get_cost_data_daily_data(usage= usage, fiscal_start= fiscal_start, fiscal_end= fiscal_end,  is_forcast= True, query_grouping= query_grouping)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return {}

    
  async def __process_get_cost_data_time_range(self, account, start_date, end_date, fiscal_start, fiscal_end, query_grouping = [], *args, **kwargs):
    
    cost_filter = {
      'type': ExportType.AMORTIZED_COST,
      'timeframe': TimeframeType.CUSTOM,
      'time_period': QueryTimePeriod(
        from_property= self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= start_date)}T00:00:00+00:00"),
        to=  self.get_common().helper_type().datetime().parse_iso(iso_datetime_str= f"{self.get_common().helper_type().datetime().datetime_as_string(dt_format='%Y-%m-%d', dt= end_date)}T23:59:59+00:00")
      ),
      'dataset': {
        'granularity': GranularityType.DAILY,
        'aggregation': {
          f'totalCost': {
            'name': f'Cost',
            'function': 'Sum'
          }
        },
        'grouping': [ 
          {"type": "Dimension", "name": dimension} for dimension in query_grouping
        ]        
      }
    }
    
    try:
      usage = self.__process_get_cost_generate_data(account= account, cost_filter= cost_filter, is_forcast= False, *args, **kwargs)

      if usage is None:
        return {}

      return await self.__process_get_cost_data_daily_data(account= account, usage= usage, fiscal_start= fiscal_start, fiscal_end= fiscal_end, is_forcast= False, query_grouping= query_grouping)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return {}
    
  
  async def __process_get_cost_data_daily_data(self, usage, fiscal_start, fiscal_end, query_grouping, is_forcast = False, *args, **kwargs):
    by_month = { }

    column_indexs = {
      self.get_common().helper_type().string().set_case(string_value= dimension, case= "lower"):-1 for dimension in query_grouping
    }
    if column_indexs.get("resourcegroup") is None:
      column_indexs["resourcegroup"] = -1
    if column_indexs.get("resourcetype") is None:
      column_indexs["resourcetype"] = -1

    column_indexs["cost"] = -1
    column_indexs[f"cost{self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= 'lower')}"] = -1
    column_indexs["usagedate"] = -1
    column_indexs["currency"] = -1

    total_key = "total" if not is_forcast else "forcast_total"
    

    for index, data in enumerate(usage.columns):
      
      if column_indexs.get(self.get_common().helper_type().string().set_case(string_value= data.name , case= "lower")) is None:
        continue
      column_indexs[self.get_common().helper_type().string().set_case(string_value= data.name, case= "lower")] = index
    
    cost_key = "cost"

    if column_indexs[cost_key] < 0:
      cost_key = f"cost{self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= 'lower')}"

    for cost_data in usage.rows:
      data_dt = self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(cost_data[column_indexs["usagedate"]]), dt_format= "%Y%m%d")
      by_month_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m", dt= data_dt)
        
      day_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m%d", dt= data_dt)
      if by_month.get(by_month_key) is None:
        by_month[by_month_key] = {
          "currency": self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= "upper"),
          "month": data_dt.month,
          "year": data_dt.year,
          "totals":{
            "total": Decimal(0),
            "fiscal_total": Decimal(0),
            "forcast_total": Decimal(0),
            "fiscal_forcast_total": Decimal(0),
            "resource_group": {
              "total":{},
              "forcast_total":{},
              "origional_currency_total":{},
              "origional_currency_forcast_total":{},
            },
            "resource_type": {
              "total":{},
              "forcast_total":{},
              "origional_currency_total":{},
              "origional_currency_forcast_total":{},
            }
          },
          "days":{}
        }
      
      if by_month[by_month_key]["days"].get(day_key) is None:
        by_month[by_month_key]["days"][day_key] = {
          "currency": self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= "upper"),
          "origional_currency": self.get_common().helper_type().string().set_case(string_value= cost_data[column_indexs["currency"]], case= "upper"),
          "date": data_dt,
          "total": Decimal(0),
          "forcast_total": Decimal(0),
          "origional_currency_total": Decimal(0),
          "origional_currency_forcast_total": Decimal(0),
          "resource_group": {
            "total":{},
            "forcast_total":{},
            "origional_currency_total":{},
            "origional_currency_forcast_total":{},
          },
          "resource_type": {
            "total":{},
            "forcast_total":{},
            "origional_currency_total":{},
            "origional_currency_forcast_total":{},
          }
        }

      
      raw_row_data_cost = (cost_data[column_indexs[cost_key]])
      row_data_cost = (cost_data[column_indexs[cost_key]])
      
      if by_month[by_month_key]["days"][day_key]["currency"] != by_month[by_month_key]["days"][day_key]["origional_currency"]:
        row_data_cost = self.get_common().helper_currency().convert(
          ammount= row_data_cost,
          currency_from= by_month[by_month_key]["days"][day_key]["origional_currency"],
          currency_to= by_month[by_month_key]["days"][day_key]["currency"],
          conversion_date= self.get_common().helper_type().datetime().yesterday(dt=self.get_common().helper_type().datetime().datetime_from_string(
            dt_string= self.get_common().helper_type().datetime().datetime_as_string(
              dt= data_dt,
              dt_format= "%Y%m01"
            ),
            dt_format= "%Y%m%d"
          )).date()
        )

      by_month[by_month_key]["days"][day_key][f'origional_currency_{total_key}'] += Decimal(raw_row_data_cost)
      by_month[by_month_key]["days"][day_key][f'{total_key}'] += Decimal(row_data_cost)
      by_month[by_month_key]["totals"][f'{total_key}'] += Decimal(row_data_cost)
      if data_dt >= fiscal_start and data_dt <= fiscal_end:
        by_month[by_month_key]["totals"][f'fiscal_{total_key}'] += Decimal(row_data_cost)

      if column_indexs["resourcegroup"] > -1:
        if (by_month[by_month_key]["days"][day_key]["resource_group"][f'{total_key}'].get(cost_data[column_indexs["resourcegroup"]]) is None or
            by_month[by_month_key]["days"][day_key]["resource_group"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcegroup"]]) is None):
          by_month[by_month_key]["days"][day_key]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcegroup"]]] = Decimal(0)
          by_month[by_month_key]["days"][day_key]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcegroup"]]] = Decimal(0)
        
        if (by_month[by_month_key]["totals"]["resource_group"][f'{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None or
            by_month[by_month_key]["totals"]["resource_group"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None):
          by_month[by_month_key]["totals"]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
          by_month[by_month_key]["totals"]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)

        by_month[by_month_key]["days"][day_key]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcegroup"]]] += Decimal(raw_row_data_cost)
        by_month[by_month_key]["days"][day_key]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcegroup"]]] += Decimal(row_data_cost)
        by_month[by_month_key]["totals"]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(raw_row_data_cost)
        by_month[by_month_key]["totals"]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(row_data_cost)

      if column_indexs["resourcetype"] > -1:
        if (by_month[by_month_key]["days"][day_key]["resource_type"][f'{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None or
            by_month[by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None):
          by_month[by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
          by_month[by_month_key]["days"][day_key]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
        
        if (by_month[by_month_key]["totals"]["resource_type"][f'{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None or
            by_month[by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None):
          by_month[by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
          by_month[by_month_key]["totals"]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)


        by_month[by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(raw_row_data_cost)
        by_month[by_month_key]["days"][day_key]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(row_data_cost)
        by_month[by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(raw_row_data_cost)
        by_month[by_month_key]["totals"]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(row_data_cost)


    return by_month

  async def __process_get_cost_data_sum_year_forcast_data(self, year_month_data, forcast_month_data, *args, **kwargs):
    key_list = self.get_common().helper_type().list().unique_list(data= list(year_month_data.keys()) + list(forcast_month_data.keys()))

    for key in key_list:
      year_month_key_data = year_month_data.get(key)
      forcast_month_key_data = forcast_month_data.get(key)

      if (self.get_common().helper_type().general().is_type(obj=year_month_key_data, type_check= dict) or
        self.get_common().helper_type().general().is_type(obj=forcast_month_key_data, type_check= dict)):
        return await self.__process_get_cost_data_sum_year_forcast_data(
          year_month_data= year_month_key_data,
          forcast_month_data= forcast_month_key_data
        )
      
      if self.get_common().helper_type().general().is_numeric(year_month_key_data) and forcast_month_key_data is None:
        forcast_month_key_data = Decimal(0)
      
      if self.get_common().helper_type().general().is_numeric(year_month_key_data) and year_month_key_data is None:
        year_month_key_data = Decimal(0)
      
      year_month_data[key] = (year_month_key_data + forcast_month_key_data)
        
      

  async def __process_get_cost_data_process_year_data_range_data(self, year_data, processed_time_range_data, *args, **kwargs):
    
    while len(processed_time_range_data.keys()) > 0:
        month_key, month_data = processed_time_range_data.popitem()
        if year_data.get(month_key) is None:
          year_data[month_key] = month_data
          continue
        
        await self.__process_get_cost_data_sum_year_forcast_data(
          year_month_data= year_data[month_key],
          forcast_month_data= month_data
        )

  async def __process_get_cost_data_process_forcast_year_data(self, year_data, start_date, end_date, fiscal_start, fiscal_end, *args, **kwargs):
     end_date += self.get_common().helper_type().datetime().time_delta(months= 1, dt= end_date)
     while start_date < end_date:
      await self.__process_get_cost_data_process_year_data_range_data(
        year_data= year_data,
        processed_time_range_data= await self.__process_get_cost_data_forcast_time_range(
          start_date= start_date,
          end_date= self.get_common().helper_type().datetime().yesterday(dt=(start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date))),
          fiscal_start= fiscal_start, fiscal_end= fiscal_end, 
          query_grouping= ["SubscriptionId"],
          *args, **kwargs )
      )

      start_date = start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date)

  async def __process_get_cost_data_process_year_data(self, year_data, start_date, end_date, fiscal_start, fiscal_end, *args, **kwargs):
     end_date += self.get_common().helper_type().datetime().time_delta(months= 1, dt= end_date)
     while start_date < end_date:
      
      await self.__process_get_cost_data_process_year_data_range_data(
        year_data= year_data,
        processed_time_range_data= await self.__process_get_cost_data_time_range(
          start_date= start_date,
          end_date= self.get_common().helper_type().datetime().yesterday(dt=(start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date))),
          fiscal_start= fiscal_start, fiscal_end= fiscal_end, 
          query_grouping= ["SubscriptionId"],
          *args, **kwargs )
      )

      start_date = start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date)

      

  async def __process_get_cost_data(self, loop, fiscal_year_start, *args, **kwargs):
    fiscal_year_start_date = self.get_common().helper_type().datetime().datetime_from_string(
      dt_string= f"{self.get_data_start().year}/{fiscal_year_start}",
      dt_format= "%Y/%m/%d"
    )
    
    if fiscal_year_start_date > self.get_data_start():
      fiscal_year_start_date = fiscal_year_start_date + self.get_common().helper_type().datetime().time_delta(years= -1)

    
    fiscal_year_end = self.get_common().helper_type().datetime().yesterday(dt= (fiscal_year_start_date
                 + self.get_common().helper_type().datetime().time_delta(years= 1, dt= fiscal_year_start_date)))
    
    # yesterday = self.get_common().helper_type().datetime().yesterday(dt= self.get_data_start())
    # last_year = (self.get_common().helper_type().datetime().yesterday(dt= self.get_data_start())
    #              + self.get_common().helper_type().datetime().time_delta(years= -1))
    start_date = (fiscal_year_start_date
                 + self.get_common().helper_type().datetime().time_delta(months= -1, dt= fiscal_year_start_date))
    
    forecast_end = (fiscal_year_end
                 + self.get_common().helper_type().datetime().time_delta(months= 3, dt= fiscal_year_end))
    year_data = {}
    #__process_get_cost_data_forcast_time_range
    await self.__process_get_cost_data_process_year_data(
      year_data= year_data,
      start_date= start_date,
      end_date= self.get_data_start(),
      fiscal_start= fiscal_year_start_date,
      fiscal_end= fiscal_year_end, *args, **kwargs
    )
    
    await self.__process_get_cost_data_process_forcast_year_data(
      year_data= year_data,
      start_date= self.get_data_start(),
      end_date= forecast_end,
      fiscal_start= fiscal_year_start_date,
      fiscal_end= fiscal_year_end, *args, **kwargs
    )
    
    month_key = self.get_common().helper_type().datetime().datetime_as_string(
      dt= self.get_data_start(),
      dt_format= "%Y%m"
    )
    last_month_key = self.get_common().helper_type().datetime().datetime_as_string(
      dt= (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(days= (self.get_data_start().day + 1))),
      dt_format= "%Y%m"
    )
    return_data = {
      "year_to_date": Decimal(0),  
      "year_forecast": Decimal(0),
      "fiscal_year_to_date": Decimal(0),  
      "fiscal_year_forecast": Decimal(0),
      "month_to_date": Decimal(0),  
      "month_forecast": Decimal(0),
      "last_seven_days": Decimal(0),
      "last_month": Decimal(0),
    }

    last14_days = {}
    await self.__process_get_cost_data_process_year_data_range_data(
      year_data= last14_days,
      processed_time_range_data= await self.__process_get_cost_data_time_range(
        start_date= (self.get_data_start() + self.get_common().helper_type().datetime().time_delta(days= -14)),
        end_date= self.get_data_start(),
        fiscal_start= fiscal_year_start_date, fiscal_end= fiscal_year_start_date, 
        query_grouping= ["SubscriptionId", "ResourceGroup", "ResourceType"],
        *args, **kwargs )
    )

    day_count = 0
    if last14_days.get(month_key) is not None:
      for i in range(0,9):
        if day_count >= 7:
          break
        day_key = self.get_common().helper_type().datetime().datetime_as_string(
          dt= (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(days= i)),
          dt_format= "%Y%m%d"
        )
        

        if last14_days[month_key]["days"].get(day_key) is None:
          continue
        
        day_count += 1
        return_data["last_seven_days"] += last14_days[month_key]["days"][day_key]["total"]
    
    return_data["raw_last_14_days"] = last14_days
    

    

    for data in year_data.values():
      return_data["fiscal_year_to_date"] += data["totals"].get("fiscal_total")
      return_data["fiscal_year_forecast"] += (data["totals"].get("fiscal_total") + data["totals"].get("fiscal_forcast_total"))
      if data["year"] == self.get_data_start().year:
        return_data["year_to_date"] += data["totals"].get("total")
        return_data["year_forecast"] += (data["totals"].get("total") + data["totals"].get("forcast_total"))

    
    if year_data.get(month_key) is not None:
      return_data["month_to_date"] = year_data[month_key]["totals"]["total"]
      return_data["month_forecast"] = year_data[month_key]["totals"]["total"] + year_data[month_key]["totals"]["forcast_total"]
    
    if year_data.get(last_month_key) is not None:
      return_data["last_month"] = year_data[last_month_key]["totals"]["total"]


    return return_data

  async def _process_account_data(self, account, loop, *args, **kwargs):
    
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= kwargs.get("fiscal_year_start")):
      kwargs["fiscal_year_start"] = self.get_cloud_data_client().get_default_fiscal_year_start()
    
    costmanagement_client = CostManagementClient(credential= self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)), subscription_id= self.get_cloud_client().get_account_id(account= account))
  
    return {
      "account": account,
      "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        await self.get_base_return_data(
          account= self.get_cloud_client().serialize_resource(resource= account),
          resource_id =  f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
        ),
        await self.__process_get_cost_data(account= account, client= costmanagement_client, loop= loop, *args, **kwargs)
      ])]
    }