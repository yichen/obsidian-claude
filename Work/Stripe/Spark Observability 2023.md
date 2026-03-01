#stripe/spark-observability-2023

According to Dmitry, use cases ordered by priority:
1. Able to send some notifications to users to warn them.
2. How to build alerting at scale for ourselves.
3. How we find in-progress applications follow a certain behavior
4. start with a distinct use case.

----

### Able to send notifications to warn users
- Follow go/spark-oom, and see if any use cases can be tracked with a pattern. The most important one is driver OOM


How to predict driver OOM?
- Try this query and see if I can find failed apps caused by Driver OOM: ```
```
select
  report.appid, report.airflowTaskId, max(1.0 * heapMemoryTotalUsed/heapMemoryMax) as max_heap_ratio
from
  events.spark_jvm_profiler_report_v2 report
  join iceberg.yarn_iceberg.app_history apphist
  on report.appid = apphist.app_id 
where
  locality_zone = 'DEFAULT'
  and report.day >= date_format(current_date - interval '2' day, '%Y%m%d%H')
  and apphist.day_hour >= date_format(current_date - interval '2' day, '%Y%m%d%H')
  and role = 'driver'
  and apphist.final_status = 'FAILED'
group by 1,2  
order by 3 desc  
limit 100
```


Case Studies:
1. [iceberg.DataFilesJobReconcilation](https://docs.google.com/document/d/1FhvfO3E4FBAyxwgduLki38OlZamvynfUN4siwdKB_p4/edit?usp=sharing)
2. [iceberg.DataFilesJobEverythingElse](https://docs.google.com/document/d/1slim908TEMBrqPdedq4RisVkShx3kRvKp9wJ1DQ-dCQ/edit?usp=sharing)
3. [iceberg.DataFilesJobRDPExpress](https://docs.google.com/document/d/1NSD1T_Q83aG3OBOMA69MiE-RAYeMtia6SFOM13e2Dws/edit?usp=sharing)
4. Driver GC: [presto.Import-revenue_engine.fee_record](https://docs.google.com/document/d/12WlZhJXio1MW5eS8IkYoULvodSr77vN_sc2Hh0ytpa0/edit)
5. Driver GC: [communia_sales.AggSalesProductReporting](https://docs.google.com/document/d/1deo33-K2q1rYgYLIC4xukjx7JCCCPxtMUsJ1uF3TYxQ/edit?usp=sharing)
6. [payment_flows.ConversionFlows](https://docs.google.com/document/d/1WDAxADzQ1EhzIoX9MH1I5uZSiNQj83CmenBaHQUkPqc/edit?usp=sharing)



