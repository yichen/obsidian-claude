
#runbook

To see the YARN schedule delay (for SLA)
- See [habble chart](https://hubble.corp.stripe.com/queries/borovsky/1fa9e528/linechart).

Scale up and scale down
- after merging PR, wait until the code is in master and passed all tests, using this link: https://git.corp.stripe.com/stripe-internal/puppet-config/commits/master-passing-tests
- to scale up, sync first, puppet later. Run the following command from the /stripe/puppet-config path (ICP also includes concord):
```
sc-asg sync hadoopdatanodeicp.northwest.prod.stripe.io/strawberry --scaling-reason CAPACITY-26444
sc-puppet --host-set strawberry -Spt "hadoopresourcepri hadoopresourcesec" --ssh
```
- to scale down, puppet first, sync later.

Note that indigo is not an ICP cluster (this includes indigo, qos, and ADD_OTHERS_HERE), the command looks different:

```
sc-asg sync hadoopdatanodei.northwest.prod.stripe.io/indigo --scaling-reason CAPACITY-26401
sc-puppet --host-set indigo -Spt "hadoopresourcepri hadoopresourcesec" --ssh
```

Also note that apricot is also different:
```
sc-asg sync hadoopdnadhoc.northwest.prod.stripe.io/apricot
```


sc-asg get hadoopresourcepri.northwest.qa.stripe.io/test



HDFS BlockMissingException
```
for-servers -Spt "hadoopnamenodepri" -H concord "sudo hdfs fsck -showprogress -delete /"
```

Spark History Server
#sparkhistoryserver
ssh to SHS instance:
`sc-asg ssh sparkhistory.northwest.prod.stripe.io/strawberry`

Check event log directory:
`ls /pay/spark/history-server/apps`

How to search splunk for namenode logs for concord?
- use the following search expression, to search for case sensitive ERROR log lines
```

host=hadoopnamenode* host_set=concord source=/pay/log/hadoop-namenode.log CASE(ERROR)

host=hadoopnamenode* host_set=concord source=/pay/log/hadoop-namenode.log ERROR namenode.NameNode: RECEIVED SIGNAL 15
```


Start to build Hadoop:
```pay ci:build --prod --branch yichen/ir-cornered-concise stripe-private-oss-forks-hadoop
```


Rolling out Hadoop Patch:
https://confluence.corp.stripe.com/display/BATCOM/Rolling+out+a+Hadoop+patch

List of Hadoop Clusters:
https://confluence.corp.stripe.com/display/BATCOM/List+Of+Hadoop+Clusters

Deploy FF:
In QA, see  https://amp.qa.corp.stripe.com/services/zoolander-flags


- How to run PySpark job today? 

```
SPARK_VERSION="3.1" DISABLED_UNSCOPED_TASK="False" bin/run-spark src/python/data_productivity/pyspark_example:oranges --app-name pyspark.data_platform.PySparkPackageTest
```




https://amp.corp.stripe.com/host-types/hadoopdatanodei

https://amp.corp.stripe.com/services/zoolander


How to clean up and restart failed Airflow tasks?
- See https://confluence.corp.stripe.com/display/DATAPLAT/%5Brunbook%5D+Airflow#id-%5Brunbook%5DAirflow-Clearingallfailedtaskswithinawindow
- Example: `airflow clear_for_time_range -f -d -t '.*' -s "2023-04-07T11:00:00+00:00" -e "2023-04-07T12:00:00+00:00" -dx ".*"`



How to run USM job for Pinot's Spark ingestion job? According to @lrao:
```
pay -t mydata-standard job:run bin/airflow-local run --usm --no-confirm pinot.segment.CreatePinotSegments.prod.sandbox.SandboxChargeCountBySuccess.northwest --usm-path-prefix=[s3://stripe-data/tmp/](s3://stripe-data/tmp/)<YOUR_USER_NAME> --date 2023-02-15
```


Run IcebergCanary job
```
airflow-local run canary.IcebergCanary --usm --hadoop-cluster hadoop-foley --hadoop-queue canaries --usm-path-prefix "s3://qa-stripe-data/iceberg_warehouse/user/yichen/foley/202304190815"
```

To change Spark Configs, add the following:
```
`DEPLOY_SPARK_SUBMIT_OPTIONS=``' --conf "spark.driver.maxResultSize=4g"'` `bin``/airflow-local` `<SPARK_DEPLOY_TARGET>`
```


Using a qa-mydata host for testing
`pay --host-type qa-mydata-standard up`
`pay --host-type qa-mydata-standard ssh`

Setting Spark configs using airflow-local

For a task that submits a Spark application, you can override a number of additional Spark configs with the `--spark-conf` flag, which takes a comma separate list of key=value pairs.

The allowed configs are: 'spark.driver.memory', 'spark.driver.memoryOverhead', 'spark.executor.memory', 'spark.executor.memoryOverhead', 'spark.network.timeout', spark.sql.shuffle.partitions', 'spark.sql.autoBroadcastJoinThreshold', 'spark.sql.broadcastTimeout', and 'spark.driver.maxResultSize'


SignalFX alert and detectors. See example:
- terraform/stripe.io/signalfx/batch-compute/detectors/namenode_average_rpc_response_time.tf
- https://git.corp.stripe.com/stripe-internal/puppet-config/pull/107061/files



Q:How to monitor the ResourceManager restarts?
A: we have signalfx like [this](https://stripe.signalfx.com/#/temp/chart/v2/Fvx8NL2AgAA?sources%5B%5D=host_set:indigo&startTimeUTC=1683663937000&endTimeUTC=1683678179000&density=4).
![[Screenshot 2023-05-10 at 10.16.09 AM.png]]




### No space left on device: Hadoop may be suffering from disk space issues
- Follow the runbook [here](https://confluence.corp.stripe.com/display/BATCOM/%5Brunbook%5D+Local+Disk+Space+Quota+Management)
- If multiple job failed in the same cluster, I need to identify the one that is triggering the issue (affecting other jobs), and create an incident. Othrwise, if the job is failing but not affecting others, directly ping their runner and determine if an incident is needed.


# Decomission

Search splunk for `DECOMMISSIONED source="/pay/log/terminator.log"`  to look for logs about decomissioned hosts.

Finding the ResourceManager nodes:
`sc-asg get hadoopresourcepri.northwest.prod.stripe.io/apricot`