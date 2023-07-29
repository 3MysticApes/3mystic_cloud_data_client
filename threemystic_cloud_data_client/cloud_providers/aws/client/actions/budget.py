"""The AWS database Action. This will pull the AWS rds"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from decimal import Decimal, ROUND_HALF_UP

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="budget",
      logger_name= "cloud_data_client_aws_client_action_budget",
      *args, **kwargs)
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    pass
  
  def __get_costdata_total_key(self, forecast_metric, *args, **kwargs):
    if self.get_common().helper_type().string().set_case(string_value= forecast_metric, case= "upper") == "NET_UNBLENDED_COST":
      return "NetUnblendedCost"

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
  
  async def __process_get_cost_data_process_year_data(self, year_data, client, account, start_date, end_date, fiscal_start, fiscal_end, forecast_metric = ["NET_UNBLENDED_COST"], *args, **kwargs):

    results_by_time = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda: client.get_cost_and_usage_with_resources(
        TimePeriod={
          'Start': start_date.strftime("%Y-%m-%d"),
          'End': end_date.strftime("%Y-%m-%d"),
        },
        Granularity='DAILY',
        Metrics=forecast_metric,
        Filter={
          "Dimensions":{
            "Key":"LINKED_ACCOUNT",
            "Values":[self.get_cloud_client().get_account_id(account= account)]
          }
        },
        GroupBy= [
          {
            "Type": "DIMENSION",
            "Key": "SERVICE"
          }
        ]
      ),
      boto_params= None,
      boto_nextkey = "NextPageToken",
      boto_nextkey_param = "NextPageToken",
      boto_key="ResultsByTime"
    )
    return results_by_time
     
    for cost_data in results_by_time:
      data_dt = self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(cost_data["TimePeriod"]["Start"]), dt_format= "%Y-%m-%d")
      by_month_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m", dt= data_dt)

      day_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m%d", dt= data_dt)
      if year_data.get(by_month_key) is None:
        year_data[by_month_key] = self.__init_costdata_month(data_dt= data_dt)
      
      if year_data[by_month_key]["days"].get(day_key) is None:
        year_data[by_month_key]["days"][day_key] = self.__init_costdata_month_day(data_dt= data_dt, currency= cost_data["Total"][self.__get_costdata_total_key(forecast_metric= forecast_metric)]["Unit"])
      


  async def __process_get_cost_data(self, account, client, fiscal_year_start, loop, *args, **kwargs):
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
    return await self.__process_get_cost_data_process_year_data(
      year_data= year_data,
      client= client,
      account= account,
      start_date= start_date,
      end_date= self.get_data_start() if forecast_end > self.get_data_start() else forecast_end,
      fiscal_start= fiscal_year_start_date, 
      fiscal_end= fiscal_year_end
    )

    return year_data


  async def _process_account_data(self, account, loop, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= kwargs.get("fiscal_year_start")):
      kwargs["fiscal_year_start"] = self.get_cloud_data_client().get_default_fiscal_year_start()
    
    client = self.get_cloud_client().get_boto_client(client= 'ce',  account=account)

    return {
      "account": account,
      "data": await self.__process_get_cost_data(account= account, client= client, loop= loop, *args, **kwargs)
    }
  
    return {
      "account": account,
      "data": [ self.get_common().helper_type().dictionary().merge_dictionary([
        {},
        await self.get_base_return_data(
          account= account,
          resource_id =  f'{self.get_cloud_client().get_account_prefix()}{self.get_cloud_client().get_account_id(account= account)}',
        ),
        await self.__process_get_cost_data(account= account, client= client, loop= loop, *args, **kwargs)
      ])]
    }

  
