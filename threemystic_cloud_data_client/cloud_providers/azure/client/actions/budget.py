from threemystic_cloud_data_client.cloud_providers.azure.client.actions.base_class.base import cloud_data_client_azure_client_action_base as base
import asyncio
from requests import post as request_post
from decimal import Decimal, ROUND_HALF_UP
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import GranularityType,ForecastDefinition,ForecastType,ForecastTimeframe,ForecastTimePeriod,QueryDefinition,TimeframeType,ExportType,QueryTimePeriod,QueryResult

class cloud_data_client_azure_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="budget", 
      logger_name= "cloud_data_client_azure_client_action_budget",
      *args, **kwargs)
  
  def __process_get_cost_generate_data(self, account, client, cost_filter, is_forcast = False, *args, **kwargs):
    if not is_forcast:
      cost_filter = QueryDefinition(**cost_filter)
      cost_response = self.get_cloud_client().sdk_request(
        tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True), 
        lambda_sdk_command=lambda: client.query.usage(
          scope= f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
          parameters= cost_filter
        )
      )
    else:
      cost_filter = ForecastDefinition(**cost_filter)
      cost_response = self.get_cloud_client().sdk_request(
          tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True),
          lambda_sdk_command=lambda: client.forecast.usage(
            scope= f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
            parameters= ForecastDefinition(**cost_filter),
          )
        )
    
    
    next_link = getattr(cost_response, "next_link", None)
    
    next_cost_page = 1
    cost_filter = cost_filter.serialize()
    if self.get_common().helper_type().general().is_type(obj= cost_filter, type_check= dict):
      cost_filter = self.get_common().helper_json().dumps(data= cost_filter)

    while not self.get_common().helper_type().string().is_null_or_whitespace(string_value= next_link):
      cost_api_resquest = request_post(
        url= next_link,
        headers= {
          "Authorization": f"Bearer {self.get_cloud_client().get_tenant_credential(tenant= self.get_cloud_client().get_tenant_id(tenant= account, is_account= True)).get_token('https://management.azure.com/.default').token}",
          "Content-Type": "application/json"
        },
        data= cost_filter,
        timeout= 10,
      )

      if cost_api_resquest.status_code == 429:
        self.get_common().helper_type().requests().expodential_backoff_wait(attempt= next_cost_page, auto_sleep= True)
        next_cost_page += 1
        continue

      cost_api_response = cost_api_resquest.json()
      next_link = cost_api_response["properties"].get("nextLink")
      next_cost_page = 1

      cost_response.rows += cost_api_response["properties"].get("rows")

    return cost_response
   
  async def __process_get_cost_data_forcast_time_range(self, account, year_data, cost_metric, start_date, end_date, fiscal_start, fiscal_end, query_grouping = [], *args, **kwargs):
    
    cost_filter = {
      'type': getattr(ForecastType, cost_metric),
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

      return await self.__process_get_cost_data_daily_data(usage= usage, year_data= year_data, cost_metric= cost_metric, fiscal_start= fiscal_start, fiscal_end= fiscal_end,  is_forcast= True, query_grouping= query_grouping)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return {}

    
  async def __process_get_cost_data_time_range(self, account, year_data, cost_metric, start_date, end_date, fiscal_start, fiscal_end, query_grouping = [], *args, **kwargs):
    
    cost_filter = {
      'type': getattr(ExportType, cost_metric),
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

      return await self.__process_get_cost_data_daily_data(account= account, year_data= year_data, cost_metric= cost_metric, usage= usage, fiscal_start= fiscal_start, fiscal_end= fiscal_end, is_forcast= False, query_grouping= query_grouping)
    except Exception as err:
      self.get_common().get_logger().exception(msg= f"{self.get_cloud_client().get_account_id(account= account)} - {str(err)}", extra={"exception": err})
      return {}
    
  def __init_costdata_month(self, data_dt, *args, **kwargs):
    return {
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
  
  def __init_costdata_month_day(self, data_dt, currency, *args, **kwargs):
    return {
      "currency": self.get_common().helper_type().string().set_case(self.get_cloud_data_client().get_default_currency(), case= "upper"),
      "origional_currency": self.get_common().helper_type().string().set_case(string_value= currency, case= "upper"),
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
    
  async def __process_get_cost_data_daily_data(self, usage, year_data, cost_metric, fiscal_start, fiscal_end, query_grouping, is_forcast = False, *args, **kwargs):
    
    if year_data is None:
      year_data = {}
    if year_data.get(cost_metric) is None:
      year_data[cost_metric] = {}

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
      if year_data[cost_metric].get(by_month_key) is None:
        year_data[cost_metric][by_month_key] = self.__init_costdata_month(data_dt= data_dt)
      
      if year_data[cost_metric][by_month_key]["days"].get(day_key) is None:
        year_data[cost_metric][by_month_key]["days"][day_key] = self.__init_costdata_month_day(data_dt= data_dt, currency= cost_data[column_indexs["currency"]])

      
      raw_row_data_cost = (cost_data[column_indexs[cost_key]])
      row_data_cost = (cost_data[column_indexs[cost_key]])
      
      if year_data[cost_metric][by_month_key]["days"][day_key]["currency"] != year_data[cost_metric][by_month_key]["days"][day_key]["origional_currency"]:
        row_data_cost = self.get_common().helper_currency().convert(
          ammount= row_data_cost,
          currency_from= year_data[cost_metric][by_month_key]["days"][day_key]["origional_currency"],
          currency_to= year_data[cost_metric][by_month_key]["days"][day_key]["currency"],
          conversion_date= self.get_common().helper_type().datetime().yesterday(dt=self.get_common().helper_type().datetime().datetime_from_string(
            dt_string= self.get_common().helper_type().datetime().datetime_as_string(
              dt= data_dt,
              dt_format= "%Y%m01"
            ),
            dt_format= "%Y%m%d"
          )).date()
        )

      year_data[cost_metric][by_month_key]["days"][day_key][f'origional_currency_{total_key}'] += Decimal(raw_row_data_cost)
      year_data[cost_metric][by_month_key]["days"][day_key][f'{total_key}'] += Decimal(row_data_cost)
      year_data[cost_metric][by_month_key]["totals"][f'{total_key}'] += Decimal(row_data_cost)
      if data_dt >= fiscal_start and data_dt <= fiscal_end:
        year_data[cost_metric][by_month_key]["totals"][f'fiscal_{total_key}'] += Decimal(row_data_cost)

      if column_indexs["resourcegroup"] > -1:
        if (year_data[cost_metric][by_month_key]["days"][day_key]["resource_group"][f'{total_key}'].get(cost_data[column_indexs["resourcegroup"]]) is None or
            year_data[cost_metric][by_month_key]["days"][day_key]["resource_group"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcegroup"]]) is None):
          year_data[cost_metric][by_month_key]["days"][day_key]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcegroup"]]] = Decimal(0)
          year_data[cost_metric][by_month_key]["days"][day_key]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcegroup"]]] = Decimal(0)
        
        if (year_data[cost_metric][by_month_key]["totals"]["resource_group"][f'{total_key}'].get(cost_data[column_indexs["resourcegroup"]]) is None or
            year_data[cost_metric][by_month_key]["totals"]["resource_group"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcegroup"]]) is None):
          year_data[cost_metric][by_month_key]["totals"]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcegroup"]]] = Decimal(0)
          year_data[cost_metric][by_month_key]["totals"]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcegroup"]]] = Decimal(0)

        year_data[cost_metric][by_month_key]["days"][day_key]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcegroup"]]] += Decimal(raw_row_data_cost)
        year_data[cost_metric][by_month_key]["days"][day_key]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcegroup"]]] += Decimal(row_data_cost)
        year_data[cost_metric][by_month_key]["totals"]["resource_group"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcegroup"]]] += Decimal(raw_row_data_cost)
        year_data[cost_metric][by_month_key]["totals"]["resource_group"][f'{total_key}'][cost_data[column_indexs["resourcegroup"]]] += Decimal(row_data_cost)

      if column_indexs["resourcetype"] > -1:
        if (year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None or
            year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None):
          year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
          year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
        
        if (year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None or
            year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'].get(cost_data[column_indexs["resourcetype"]]) is None):
          year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)
          year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] = Decimal(0)


        year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(raw_row_data_cost)
        year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(row_data_cost)
        year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(raw_row_data_cost)
        year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'{total_key}'][cost_data[column_indexs["resourcetype"]]] += Decimal(row_data_cost)

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
        

  async def __process_get_cost_data_process_forcast_year_data(self, year_data, cost_metric, start_date, end_date, fiscal_start, fiscal_end, *args, **kwargs):
     end_date += self.get_common().helper_type().datetime().time_delta(months= 1, dt= end_date)
     while start_date < end_date:
      await self.__process_get_cost_data_forcast_time_range(
          year_data= year_data,
          cost_metric= cost_metric,
          start_date= start_date,
          end_date= self.get_common().helper_type().datetime().yesterday(dt=(start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date))),
          fiscal_start= fiscal_start, fiscal_end= fiscal_end, 
          query_grouping= ["SubscriptionId"],
          *args, **kwargs )

      start_date = start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date)

  async def __process_get_cost_data_process_year_data(self, year_data, cost_metric, start_date, end_date, fiscal_start, fiscal_end, *args, **kwargs):
     end_date += self.get_common().helper_type().datetime().time_delta(months= 1, dt= end_date)
     while start_date < end_date and start_date <  self.get_data_start():
      adjusted_enddate = self.get_common().helper_type().datetime().yesterday(dt=(start_date + self.get_common().helper_type().datetime().time_delta(months= 3, dt= start_date)))
      if adjusted_enddate > self.get_data_start():
        adjusted_enddate = self.get_data_start()

      await self.__process_get_cost_data_time_range(
        year_data= year_data,
        cost_metric= cost_metric,
        start_date= start_date,
        end_date= adjusted_enddate,
        fiscal_start= fiscal_start, fiscal_end= fiscal_end, 
        query_grouping= ["SubscriptionId"],
        *args, **kwargs )
      

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
    
    start_date = (fiscal_year_start_date
                 + self.get_common().helper_type().datetime().time_delta(months= -1, dt= fiscal_year_start_date))
    
    forecast_end = (fiscal_year_end
                 + self.get_common().helper_type().datetime().time_delta(months= 3, dt= fiscal_year_end))
    year_data = {}
    cost_metric = "AMORTIZED_COST"

    await self.__process_get_cost_data_process_year_data(
      year_data= year_data,
      cost_metric= cost_metric,
      start_date= start_date,
      end_date= self.get_data_start(),
      fiscal_start= fiscal_year_start_date,
      fiscal_end= fiscal_year_end, *args, **kwargs
    )

    
    await self.__process_get_cost_data_process_forcast_year_data(
      year_data= year_data,
      cost_metric= cost_metric,
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
      "cost_metric": cost_metric,
      "year_to_date": Decimal(0),  
      "year_forecast": Decimal(0),
      "fiscal_year_to_date": Decimal(0),  
      "fiscal_year_forecast": Decimal(0),
      "month_to_date": Decimal(0),  
      "month_forecast": Decimal(0),
      "last_seven_days": Decimal(0),
      "raw_last_14_days": {},
      "last_month": Decimal(0),
    }

    last14_days = {}
    await self.__process_get_cost_data_time_range(
      year_data= last14_days,
      cost_metric= cost_metric,
      start_date= (self.get_data_start() + self.get_common().helper_type().datetime().time_delta(days= -14)),
      end_date= self.get_data_start(),
      fiscal_start= fiscal_year_start_date, fiscal_end= fiscal_year_start_date, 
      query_grouping= ["SubscriptionId", "ResourceGroup", "ResourceType"],
      *args, **kwargs )

    day_count = 0
    if last14_days.get(cost_metric) is not None:

      for i in range(0,9):
        if day_count >= 7:
          break
        
        month_key_last14 = self.get_common().helper_type().datetime().datetime_as_string(
          dt= (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(days= i)),
          dt_format= "%Y%m"
        )
        day_key = self.get_common().helper_type().datetime().datetime_as_string(
          dt= (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(days= i)),
          dt_format= "%Y%m%d"
        )
        
        if last14_days[cost_metric].get(month_key_last14) is None:
          continue
        if last14_days[cost_metric][month_key_last14]["days"].get(day_key) is None:
          continue
        
        day_count += 1
        return_data["last_seven_days"] += last14_days[cost_metric][month_key_last14]["days"][day_key]["total"]

      return_data["raw_last_14_days"] = {}
      for month_key in last14_days[cost_metric].keys():
        for day_key, day_data in last14_days[cost_metric][month_key]["days"].items():
          return_data["raw_last_14_days"][day_key]= day_data
    

    
    if year_data.get(cost_metric) is not None:
      for data in year_data.get(cost_metric).values():
        return_data["fiscal_year_to_date"] += data["totals"].get("fiscal_total")
        return_data["fiscal_year_forecast"] += (data["totals"].get("fiscal_total") + data["totals"].get("fiscal_forcast_total"))
        if data["year"] == self.get_data_start().year:
          return_data["year_to_date"] += data["totals"].get("total")
          return_data["year_forecast"] += (data["totals"].get("total") + data["totals"].get("forcast_total"))

      
      if year_data[cost_metric].get(month_key) is not None:
        return_data["month_to_date"] = year_data[cost_metric][month_key]["totals"]["total"]
        return_data["month_forecast"] = year_data[cost_metric][month_key]["totals"]["total"] + year_data[cost_metric][month_key]["totals"]["forcast_total"]
      
      if year_data[cost_metric].get(last_month_key) is not None:
        return_data["last_month"] = year_data[cost_metric][last_month_key]["totals"]["total"]


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