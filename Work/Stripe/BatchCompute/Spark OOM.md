# Spark OutOfMemoryError

#sparkoom




## TODO
- 9/13: Renewed S3 permission ([access-s3-logs](https://ldapmanager.corp.stripe.com/groups/access-s3-logs)) for batcom taem. Wait for the approval.
- 

## Related Work
- [Spark OOM case studies](https://github.com/JerryLead/MyNotes/blob/master/Cases/OOM-Cases-Spark-User-Nabble-EmpiricalStudy.md)
- [Spark Out of Memory](https://labs.criteo.com/2018/01/spark-out-of-memory/)
- [Profiling Spark jobs](https://medium.com/@Iqbalkhattra85/profiling-spark-jobs-in-production-b569ab45d84e)

## High-Level Plan
Do an analysis of critical users and critical data pipelines, and figure out the OOM and GC related issues. Figure out a way to help users proactively detect such issues to speed up investigation and resolution, instead of reactive diagnosis.



## Issue Analysis
What type of issues we have been experiencing in the past pager duty and run? 


- #arctic-frigid ([doc](https://docs.google.com/document/d/1rb_65ljFPtl7v9RiCHKCZDVzpoRMxnOP9zk_3JaE2Bw/edit#heading=h.yfot0wyrnp85)): 
	- Likely driver OOM. The path forward is bump driver memory by 20%, and add GC logging to know what's causing ApplicationMaster timeout. Current driver memory is 60G.
	- @yuan ask: do we have record/metric for how memory change?
	- https://jira.corp.stripe.com/browse/BATCOM-1703: Report aggregated driver GC stats to Hubble.
	

## Driver OOM

- Cause: collect data to the driver: _df.collect()_
	- Solution: _spark.driver.maxResultSize_ or _repartition_.
- Cause: broadcast join
	- Solution: increase driver memory, or reduce _spark.sql.autoBroadcastJoinThreshold_.


## Executor OOM
- Inefficient queries. e.g. Select all columns from a Parquet/ORC table.  (See [link](https://blog.clairvoyantsoft.com/apache-spark-out-of-memory-issue-b63c7987fff))
	- Solution: filter data. Use *partition pruning*, increase _spark.sql.shuffle.partition_.
- high concurrency
	- Solution: configure *spark.default.parallelism* and *spark.executor.cores*. 
- incorrect configuration (Yarn memory overhead ). This is to give more off-heap space for the Yarn container's needs (Otherwise the yarn container will be killed for OOM)
	- Solution:  increase **spark.yarn.executor.memoryOverhead**. The max should be 25% of the executor memory. Also make sure that the sum of driver/executor memory plus the overhead memory is less than the value of **yarn.nodemanager.resource.memory-mb**.
- Watch out for **memory leaks**. The way to diagnose is to look out for the "task serialized as XXX bytes" in the logs, if XXX is larger than a few k or more than an MB, you may have a memory leak. See [https://stackoverflow.com/a/25270600/1586965](https://stackoverflow.com/a/25270600/1586965)
- Related to above, avoid `String` and heavily nested structures (like `Map` and nested case classes). If possible try to only use primitive types and index all non-primitives especially if you expect a lot of duplicates. Choose `WrappedArray` over nested structures whenever possible. Or even roll out your own serialisation - YOU will have the most information regarding how to efficiently back your data into bytes, **USE IT**!
- Again when caching, consider using a `Dataset` to cache your structure as it will use more efficient serialisation. This should be regarded as a hack when compared to the previous bullet point. Building your domain knowledge into your algo/serialisation can minimise memory/cache-space by 100x or 1000x, whereas all a `Dataset` will likely give is 2x - 5x in memory and 10x compressed (parquet) on disk.
- Use huge Java objects will consume too much memory. Avoid Java or Scala collections (e.g. HashMap). Avoid nested structures with a lot of small objects and pointers. Use numeric IDs or enumeration objects instead of strings for keys.
- BroadcastNestedLoopJoin can easily cause OOM.
- Check **withColumn** calls to make sure not making multiple copies of same fields especially nested.
- Executor memory should be 2GB-6GB per core (avoid too much core oversubscribing)
- If less than 32GB memory, make pointers be four bytes instead of eight by setting **-XX:+UseCompressedOops**. (looks like this reduce the need of overhead memory)
- Partition size is too big. Big partition may result from file decompression or metadata overhead of file format (exploding Parquet file). To fix this, change **spark.sql.shuffle.partitions**.
- **FetchFailedException** -> increase executor memory or shuffle partitions.
- (see [link](https://stackoverflow.com/questions/21138751/spark-java-lang-outofmemoryerror-java-heap-space))You should configure offHeap memory settings as shown below:

```
val spark = SparkSession
     .builder()
     .master("local[*]")
     .config("spark.executor.memory", "70g")
     .config("spark.driver.memory", "50g")
     .config("spark.memory.offHeap.enabled",true)
     .config("spark.memory.offHeap.size","16g")   
     .appName("sampleCodeForReference")
     .getOrCreate()
```

Give the driver memory and executor memory as per your machines RAM availability. **You can increase the offHeap size if you are still facing the OutofMemory issue**.


Spark Notebook

```
%%spark

import org.apache.hadoop.fs._
val path = new Path("/var/log/hadoop-yarn/apps/")
val iter = FileSystem.get(sc.hadoopConfiguration).listFiles(path, true)

```

## FAQ


## Possible instrumentations
- log query plans for each SparkSQL job? This allows users to compare the difference between runs. It may also help the situation to auto detect inefficient queries, eg. detect broadcast join is being used.
- 


### What job metadata we have today?
We have the following tables:
- **iceberg.spark.iceberg_application_history** This table contains very limited data, it only include the following columns: app_id, user, app_name, submit_date, finish_date, driver_host, executor_memory, airflow_task, airflow_dag, airflow_team_name
- **iceberg.spark.iceberg_task_history**. This is essentially the Spark task record from the Spark event logs.
	- app_id
	- task_id
	- stage_id
	- task_type
	- task_status
	- task_failed_message
	- task_failed_description
	- host
	- launch_date
	- finish_date
	- task_duration_ms
	- deserialized_cpu_duration_ms
	- serialize_duration_ms
	- input_bytes
	- input_records
	- output_bytes
	- output_records
- **iceberg.yarn_iceberg.app_history**. This is basically the ResourceManager's data dump for applications.
	- app_id
	- app_name
	- app_type
	- elapsed_time_millis
	- started_time
	- user
	- queue
	- final_status
	- vcore_seconds
	- memory_seconds
	- am_host_http_address
	- application_tags
	- state
	- launch_time
	- failed_reason
	- preempted_resource_mb
	- preempted_resource_vcores
	- preempted_memory_seconds
	- preempted_vcore_seconds
	- cluster
	- day
	- hour
	- day_hour



### Where to find the Yarn container log?
- The [raw container logs are in S3](https://jira.corp.stripe.com/browse/RUN_OBS-56727) in the `s3://stripe-logs.us-west-2/` bucket.
- Looks like according to [Spark observability](https://confluence.corp.stripe.com/display/DATALIB/Spark+Observability), the container logs are at least temporiraly in HDFS and accessible via the mydata machine. 
- I wonder if I should just start a scheduled job in each cluster to process the container logs in each cluster?

### What heuristics can I come up with now that's related to OOM and GC?
