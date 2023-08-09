"""The AWS database Action. This will pull the AWS rds"""
from threemystic_cloud_data_client.cloud_providers.aws.client.actions.base_class.base import cloud_data_client_aws_client_action_base as base
import asyncio
from decimal import Decimal, ROUND_HALF_UP
from random import randint

class cloud_data_client_aws_client_action(base):
  def __init__(self, *args, **kwargs):
    super().__init__(
      data_action="budget",
      logger_name= "cloud_data_client_aws_client_action_budget",
      *args, **kwargs)
  
  async def _process_account_data_region(self, account, region, resource_groups, loop, *args, **kwargs):
    pass

  def __init_costdata_month(self, data_dt, *args, **kwargs):
    return {
      "currency": self.get_common().helper_type().string().set_case(string_value= self.get_cloud_data_client().get_default_currency(), case= "upper"),
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
      "currency": self.get_common().helper_type().string().set_case(string_value= self.get_cloud_data_client().get_default_currency(), case= "upper"),
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
  
  def __convert_costmetric_forecast_metric(self, cost_metric, *args, **kwargs):
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "netunblendedcost":
      return "NET_UNBLENDED_COST"
    
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "blendedcost":
      return "BLENDED_COST"
    
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "unblendedcost":
      return "UNBLENDED_COST"
    
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "amortizedcost":
      return "AMORTIZED_COST"
    
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "netamortizedcost":
      return "NET_AMORTIZED_COST"
    
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "usagequantity":
      return "USAGE_QUANTITY"
    
    if self.get_common().helper_type().string().set_case(string_value= cost_metric, case= "lower") == "normalizedusageamount":
      return "NORMALIZED_USAGE_AMOUNT"
    
    return cost_metric

  def __process_get_cost_data_process_forcast_process_day(self, cost_metric, year_data, data_dt, fiscal_start, fiscal_end, raw_data_cost, currency, total_key, *args, **kwargs):
    by_month_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m", dt= data_dt)
    day_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m%d", dt= data_dt)

    if year_data.get(by_month_key) is None:
      year_data[by_month_key] = self.__init_costdata_month(data_dt= data_dt)
    
    if year_data[by_month_key]["days"].get(day_key) is None:
      year_data[by_month_key]["days"][day_key] = self.__init_costdata_month_day(data_dt= data_dt, currency= currency)
    
    raw_row_data_cost = raw_data_cost
    row_data_cost = raw_data_cost
    
    if year_data[by_month_key]["days"][day_key]["currency"] != year_data[by_month_key]["days"][day_key]["origional_currency"]:
      row_data_cost = self.get_common().helper_currency().convert(
        ammount= row_data_cost,
        currency_from= currency,
        currency_to= year_data[by_month_key]["days"][day_key]["currency"],
        conversion_date= self.get_common().helper_type().datetime().yesterday(dt=self.get_common().helper_type().datetime().datetime_from_string(
          dt_string= self.get_common().helper_type().datetime().datetime_as_string(
            dt= data_dt,
            dt_format= "%Y%m01"
          ),
          dt_format= "%Y%m%d"
        )).date()
      )

    year_data[by_month_key]["days"][day_key][f'origional_currency_{total_key}'] += Decimal(raw_row_data_cost)
    year_data[by_month_key]["days"][day_key][f'{total_key}'] += Decimal(row_data_cost)
    year_data[by_month_key]["totals"][f'{total_key}'] += Decimal(row_data_cost)
    
    if data_dt >= fiscal_start and data_dt <= fiscal_end:
      year_data[by_month_key]["totals"][f'fiscal_{total_key}'] += Decimal(row_data_cost)
  
  async def __process_get_cost_data_process_forcast(self, year_data, client, account, start_date, end_date, fiscal_start, fiscal_end, cost_metrics, *args, **kwargs):
    
    adjusted_enddated = (start_date
                 + self.get_common().helper_type().datetime().time_delta(months= 4, dt= start_date))
    for cost_metric in cost_metrics:
      
      adjusted_enddated = (start_date + self.get_common().helper_type().datetime().time_delta(months= 4, dt= start_date))
      adjusted_enddated = self.get_common().helper_type().datetime().datetime_from_string(adjusted_enddated.strftime("%Y-%m-01"), dt_format="%Y-%m-%d")
      if end_date < adjusted_enddated:
       adjusted_enddated =  end_date
      
      results_by_time_forcast = self.get_cloud_client().general_boto_call_single(
        boto_call=lambda: client.get_cost_forecast(
          TimePeriod={
            'Start': start_date.strftime("%Y-%m-%d"),
            'End': adjusted_enddated.strftime("%Y-%m-%d"),
          },
          Granularity='DAILY',
          Metric=self.__convert_costmetric_forecast_metric(cost_metric= cost_metric),
          Filter={
            "Dimensions":{
              "Key":"LINKED_ACCOUNT",
              "Values":[self.get_cloud_client().get_account_id(account= account)]
            }
          },
        ),
        boto_params= None,
        boto_nextkey = None,
        boto_key= None
      )
      
      total_key = "forcast_total"
      currency = results_by_time_forcast["Total"]["Unit"]
    
      if year_data.get(cost_metric) is None:
        year_data[cost_metric] = {}

      data_dt = None
      for cost_data in results_by_time_forcast["ForecastResultsByTime"]:
        data_dt = self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(cost_data["TimePeriod"]["Start"]), dt_format= "%Y-%m-%d")

        self.__process_get_cost_data_process_forcast_process_day(
          cost_metric= cost_metric,
          year_data= year_data[cost_metric],
          data_dt= data_dt,
          fiscal_start= fiscal_start,
          fiscal_end= fiscal_end,
          raw_data_cost = (cost_data["MeanValue"]),
          currency= currency,
          total_key= total_key
        )

      if data_dt is not None:
        by_month_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m", dt= data_dt)
        day_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m%d", dt= data_dt)
        cost_data = year_data[cost_metric][by_month_key]["days"][day_key]

        while data_dt < end_date:
          data_dt += (self.get_common().helper_type().datetime().time_delta(days= 1, dt= data_dt))         

          self.__process_get_cost_data_process_forcast_process_day(
            cost_metric= cost_metric,
            year_data= year_data[cost_metric],
            data_dt= data_dt,
            fiscal_start= fiscal_start,
            fiscal_end= fiscal_end,
            raw_data_cost = (cost_data[total_key] * ((randint(90,120)/Decimal(100)))),
            currency= (cost_data["currency"]),
            total_key= total_key
          )


  def get_total_cost_data(self, cost_data, cost_metric, *args, **kwargs):
    if cost_data["Total"].get(cost_metric) is not None:
      if cost_data["Total"][cost_metric].get("Amount") is not None:
        return Decimal(cost_data["Total"][cost_metric]["Amount"])
    
    return Decimal(0)
      
  def get_currency_cost_data(self, cost_data, cost_metric, *args, **kwargs):
    if cost_data["Total"].get(cost_metric) is not None:
      if cost_data["Total"][cost_metric].get("Unit") is not None:
        return cost_data["Total"][cost_metric]["Unit"]
    
    if len(cost_data["Groups"]) > 0:
      if cost_data["Groups"][0]["Metrics"].get(cost_metric) is not None:
        if cost_data["Groups"][0]["Metrics"][cost_metric].get("Unit") is not None:
          return cost_data["Groups"][0]["Metrics"][cost_metric]["Unit"]
        
    return self.get_cloud_data_client().get_default_currency()
      
  async def __process_get_cost_data_process_year_data(self, year_data, client, account, granularity, start_date, end_date, fiscal_start, fiscal_end, cost_metrics, *args, **kwargs):

    results_by_time = self.get_cloud_client().general_boto_call_array(
      boto_call=lambda item: client.get_cost_and_usage(
        TimePeriod={
          'Start': start_date.strftime("%Y-%m-%d"),
          'End': end_date.strftime("%Y-%m-%d"),
        },
        Granularity= granularity,
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
        ],
        **item
      ),
      boto_params= {
        "Metrics": cost_metrics
      },
      boto_nextkey = "NextPageToken",
      boto_nextkey_param = "NextPageToken",
      boto_key="ResultsByTime"
    )
    
    total_key = "total"
    for cost_metric in cost_metrics:
      if year_data.get(cost_metric) is None:
        year_data[cost_metric] = {}
        
      for cost_data in results_by_time:
        data_dt = self.get_common().helper_type().datetime().datetime_from_string(dt_string= str(cost_data["TimePeriod"]["Start"]), dt_format= "%Y-%m-%d")
        by_month_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m", dt= data_dt)

        day_key = self.get_common().helper_type().datetime().datetime_as_string(dt_format= "%Y%m%d", dt= data_dt)
        if year_data[cost_metric].get(by_month_key) is None:
          year_data[cost_metric][by_month_key] = self.__init_costdata_month(data_dt= data_dt)
        
        if year_data[cost_metric][by_month_key]["days"].get(day_key) is None:
          year_data[cost_metric][by_month_key]["days"][day_key] = self.__init_costdata_month_day(data_dt= data_dt, currency= self.get_currency_cost_data(cost_data= cost_data, cost_metric= cost_metric))

        raw_row_data_cost = self.get_total_cost_data(cost_data= cost_data, cost_metric= cost_metric)
        total_attribute_empty = False if raw_row_data_cost > 0 else True

        for cost_data_group in cost_data["Groups"]:
          raw_row_data_cost_group = Decimal(cost_data_group["Metrics"][cost_metric]["Amount"])
          row_data_cost_group = raw_row_data_cost_group

          if total_attribute_empty:
            raw_row_data_cost += raw_row_data_cost_group
          
          if year_data[cost_metric][by_month_key]["days"][day_key]["currency"] != cost_data_group["Metrics"][cost_metric]["Unit"]:
            row_data_cost_group = self.get_common().helper_currency().convert(
              ammount= row_data_cost_group,
              currency_from= cost_data_group["Metrics"][cost_metric]["Unit"],
              currency_to= year_data[cost_metric][by_month_key]["days"][day_key]["currency"],
              conversion_date= self.get_common().helper_type().datetime().yesterday(dt=self.get_common().helper_type().datetime().datetime_from_string(
                dt_string= self.get_common().helper_type().datetime().datetime_as_string(
                  dt= data_dt,
                  dt_format= "%Y%m01"
                ),
                dt_format= "%Y%m%d"
              )).date()
            )
          for cost_data_group_key in cost_data_group["Keys"]:
            if (year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'{total_key}'].get(cost_data_group_key) is None or
                year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'].get(cost_data_group_key) is None):
              year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'][cost_data_group_key] = Decimal(0)
              year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'{total_key}'][cost_data_group_key] = Decimal(0)
            
            if (year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'{total_key}'].get(cost_data_group_key) is None or
                year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'].get(cost_data_group_key) is None):
              year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'][cost_data_group_key] = Decimal(0)
              year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'{total_key}'][cost_data_group_key] = Decimal(0)

            year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'origional_currency_{total_key}'][cost_data_group_key] += Decimal(raw_row_data_cost_group)
            year_data[cost_metric][by_month_key]["days"][day_key]["resource_type"][f'{total_key}'][cost_data_group_key] += Decimal(row_data_cost_group)
            year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'origional_currency_{total_key}'][cost_data_group_key] += Decimal(raw_row_data_cost_group)
            year_data[cost_metric][by_month_key]["totals"]["resource_type"][f'{total_key}'][cost_data_group_key] += Decimal(row_data_cost_group)
        
        row_data_cost = raw_row_data_cost
        
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
    cost_metric = "NetUnblendedCost"
    await self.__process_get_cost_data_process_year_data(
      year_data= year_data,
      client= client,
      account= account,
      granularity= 'DAILY',
      start_date= start_date,
      end_date= self.get_data_start() if forecast_end > self.get_data_start() else forecast_end,
      fiscal_start= fiscal_year_start_date, 
      fiscal_end= fiscal_year_end,
      cost_metrics = [cost_metric]
    )

    if forecast_end > self.get_data_start():
      await self.__process_get_cost_data_process_forcast(
        year_data= year_data,
        client= client,
        account= account,
        start_date= self.get_data_start(),
        end_date= forecast_end,
        fiscal_start= fiscal_year_start_date, 
        fiscal_end= fiscal_year_end,
        cost_metrics = [cost_metric]
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

    last_14_days_data = {}
    await self.__process_get_cost_data_process_year_data(
      year_data= last_14_days_data,
      client= client,
      account= account,
      granularity= 'DAILY',
      start_date= (self.get_data_start() + self.get_common().helper_type().datetime().time_delta(days= -15, dt= self.get_data_start())),
      end_date= self.get_data_start() if forecast_end > self.get_data_start() else forecast_end,
      fiscal_start= fiscal_year_start_date,
      fiscal_end= fiscal_year_end,
      cost_metrics = [cost_metric]
    )

    day_count = 0
    for i in range(0,14):     
      month_key_last14 = self.get_common().helper_type().datetime().datetime_as_string(
        dt= (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(days= i)),
        dt_format= "%Y%m"
      )
      day_key = self.get_common().helper_type().datetime().datetime_as_string(
        dt= (self.get_data_start() - self.get_common().helper_type().datetime().time_delta(days= i)),
        dt_format= "%Y%m%d"
      )

      if last_14_days_data[cost_metric][month_key_last14]["days"].get(day_key) is None:
        continue
      
      return_data["raw_last_14_days"][day_key] = last_14_days_data[cost_metric][month_key_last14]["days"].get(day_key)

      if day_count >= 7:
        continue

      day_count += 1
      return_data["last_seven_days"] += year_data[cost_metric][month_key_last14]["days"][day_key]["total"]
      
    for data in year_data[cost_metric].values():
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
      return_data["last_month_days"] = list(year_data[cost_metric][last_month_key]["days"].keys())
  
    return return_data


  async def _process_account_data(self, account, loop, *args, **kwargs):
    if self.get_common().helper_type().string().is_null_or_whitespace(string_value= kwargs.get("fiscal_year_start")):
      kwargs["fiscal_year_start"] = self.get_cloud_data_client().get_default_fiscal_year_start()
    
    client = self.get_cloud_client().get_boto_client(client= 'ce',  account=account)
  
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

  
