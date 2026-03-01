#jvm

### TODO
- figure out how to tag an application with jvm-profiler
- figure out the schema in iceberg.
- figure out the dashboard, how it would look like, will it be an extension of go/spark-profiler?
- Read Spark vision and figure out what we can do in 2023?
	- pre-joining?
	- bucketing?


## 2022-09-28


## 2022-09-27
`Spark job failed due to: Error opening zip file or JAR manifest missing : jvm-profiler-1.0.0.jar`

How does `spark-submit` works with the extraJavaOptions?

## 2022-09-26

Looks like I already have the bazel rule for the jar uploaded earlier:
```
Bazel rule for version 261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb of com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar:
http_archive(
    name = "com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar",
    sha256 = "261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb",
    urls = [
        "https://artifactory-content.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar",
    ],
)
```

But I still don't know how to reference this in Bazel.
If I do `@jvm_profiler//jvm_profiler:jar` as rumtime_deps, I am getting:
```
ERROR: /Users/yichen/stripe/zoolander/data_common/src/scala/com/stripe/spark/BUILD:28:14: no such package '@jvm_profiler//jvm_profiler': BUILD file not found in directory 'jvm_profiler' of external repository @jvm_profiler. Add a BUILD file to a directory to mark it as a package. and referenced by '//data_common/src/scala/com/stripe/spark:spark'
ERROR: Analysis of target '//data_common/src/scala/com/stripe/spark:spark' failed; build aborted: no such package '@jvm_profiler//jvm_profiler': BUILD file not found in directory 'jvm_profiler' of external repository @jvm_profiler. Add a BUILD file to a directory to mark it as a package.
```

Why? What does `http_archive` do? It downloads a bazel repository as a compressed archive file, decompress it, and makets its target available for binding. Turns out I should not use the recommended `http_archive`, instead use `http_jar`.

Now how do I test it? mydata box will automatically sync my branch. Run a job with usm and test it out:
```
DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar=reporter=com.uber.profiling.reporters.ConsoleOutputReporter,metricInterval=1000' ./bin/airflow-local run airflow_functional_tests.MinutelySparkTask --use-dag-cache --usm
```

Failed!

So now I added the repositories config `--conf spark.jars.repositories` and the application runs and finishes! I did not however see the console output though.  Why? The testing command is below:

```
DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.jars.repositories=https://artifactory-content.stripe.build/artifactory/thirdparty-managed --conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar=reporter=com.uber.profiling.reporters.ConsoleOutputReporter,metricInterval=1000' ./bin/airflow-local run airflow_functional_tests.MinutelySparkTask --use-dag-cache --usm
```

Now let me try again but add 
`--conf spark.jars.packages= this time.`

```

DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.jars.repositories=https://artifactory-content.stripe.build/artifactory/thirdparty-managed --conf spark.jars.packages=com.uber:jvm-profiler:1.0.0 --conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar=reporter=com.uber.profiling.reporters.ConsoleOutputReporter,metricInterval=100' ./bin/airflow-local run airflow_functional_tests.MinutelySparkTask --use-dag-cache --usm
```

Failed with `org.apache.oro.text.regex.MalformedPatternException`

## 2022-09-19



- [How to monitor JVM metrics](https://www.stubbornjava.com/posts/monitoring-your-jvm-with-dropwizard-metrics)?
	- Register built in metric sets. Set up metrics reporters where we can report and graph metrics to various systems such as grafana, graphite, prometheus.
- What are the typical Dropwizard metrics reporters?
	- ConsoleReporter
	- CsvReporter
	- GangliaReporter
	- GraphiteReporter
	- JmxReporter
	- **InstrumentedAppender**: monitor your logging level over time, help track if you have increasing/decreasing errors over time or notice any bursts in one specific level.
- Can I publish Spark [metrics to Kafka](https://richardstartin.github.io/posts/publishing-dropwizard-metrics-to-kafka)? If so, can I publish to Kafka and also report to grafana at the same time?
	- To do this, we need to extend the Dropwizard Reporter mechanism to use Kafka as a destination. 
	- To implement that, extend ScheduledReporter. 
	- That is, if we were to publish the metrics to Kafka, we need to replace the metric system jar dependency with our implementation of Kafka reporter, which doesn't come included. Here is [KafkaSink](https://github.com/erikerlandson/spark-kafka-sink/blob/master/src/main/scala/org/apache/spark/metrics/sink/KafkaSink.scala).
- What [JVM metrics](https://www.stubbornjava.com/posts/monitoring-your-jvm-with-dropwizard-metrics) we can have?
	- **GarbageCollectorMetricSet**: tell us how frequently we mark and sweep or scavenge as well as how long they take to run. Monitoring these over time can help identify unecessary object creation or anytime you introduce new code that incurs much higher garbage collection costs.
	- **CachedThreadStatesGaugeSet** provides us with snapshots of how many threads we have in which states. It's best to use the cached version since this requires traversing all threads and can be a little more expensive than some other metrics.
	- **MemoryUsageGaugeSet** gives you memory internals, including heap.committed, heap.max, heap.usage, heap.used, non-heap.*, etc
- How do I actually configure the Spark's MetricSystem? Using spark-shell or spark-sql as an example.
	- There are two ways to configure: (1) use $SPARK_HOME/conf/metrics.properties.template, or (2) command-line parameters.
	- To pass the parameter to spark-shell, use --conf and extraJavaOptions: `spark-shell --conf 'spark.driver.extraJavaOptions=-Dspark.metrics.conf=/Users/yichen/work/metrics.properties'`
	- Example with ConsoleReporter:
	- Example CsvReporter:
- For **GraphiteReporter**, can I use grafana to dashboard the data? What's the relationship between Graphite and Grafana?
	- Graphite is a monitoring tool. It does two things: (1) store numeric time-series data, and (2) render graphs of this data on demand.
	- Graphite is not a collection agent, but it can get your measurements into a time-series database. 
	- **Grafana is a general purpose graphite dashboard replacement with feature rich graph editing and dashboard creation interface. Grafana does not store any data itself.**
	- Graphite itself does not collect any metrics, it requires metrics to be sent to it in a Graphite format. Dropwizard can send metrics in such format using the GraphiteReporter. That is, Graphite is push based (while Prometheus is pull based), that the client (GraphiteReporter in this case) needs to send the data to the Graphite endpoint.
	- Grafana Cloud [currently supports the continue development of Graphite](https://grafana.com/oss/graphite/). 
- Describe the differences of the metric systems across Spark versions.
	- Spark 2.3: [add Spark executor metrics to Dropwizard merics.](https://issues.apache.org/jira/browse/SPARK-22190)
	- Spark 2.4: [add executor CPU time metric](https://issues.apache.org/jira/browse/SPARK-25228)
	- Spark 3.0: [executor metrics and memory usage instrumentation to the metrics system](https://issues.apache.org/jira/browse/SPARK-27189)
- Can Uber's [JVM Profiler](https://www.uber.com/blog/jvm-profiler/) also profile drivers? [Yes, it collects data from drivers, executors, and any JVM](https://www.infoq.com/articles/spark-application-monitoring-influxdb-grafana/).
- How to dashboard metrics using Uber's JVM Profiler?
- What's the difference between Spark metrics system and Uber's JVM Profiler?
	- According to [this article](https://www.infoq.com/articles/spark-application-monitoring-influxdb-grafana/), Uber's JVM Profiler is an alternative to dashboarding with the existing Spark's meetrics system.
	- JVM Profiler: We should able to get detailed metrics about CPU, Memory, Storage, Disk I/O for local file and HDFS, stack traces etc. The monitoring system should provide code level metrics for applications (e.g. execution time, arguments used by different methods) running on spark.
- Why can Uber's JVM Profiler provide more data (execution time, call stack, hdfs, io) than Spark 3's metrics?
- What's the main difference of Spark metrics system between Spark 2.x and Spark 3?
	- [Spark 3 has native support for Prometheus](https://www.youtube.com/watch?v=FDzm3MiSfiE). Stripe appears to have Prometheus infrastructure and Grafana. This means that we need a lot of extra work to make it work with Spark 2.4.4 while for Spark 3 we may get most of everything free.
- What's the architecture difference between the Spark real-time metrics and the event log system?
	- Event log system flow everything through the driver. The MetricSystem send the metrics directly from the source (driver, or each executor) to the sink, without having to go through the driver.
- What about [OpenTelemetry's Java Agent](https://github.com/open-telemetry/opentelemetry-java-instrumentation)?
- What about [SignalFX's collectd for Spark](https://github.com/signalfx/collectd-spark)?
	- How does SignalFx work? SignalFx agent collects metrics and send them to their servers. That is, SignalFx is agent-based system (while Graphite is agentless)
	- This is actually the [Splunk distribution of OpenTelemetry collector](https://docs.splunk.com/Observability/gdi/spark/spark.html). Here is a list of [Spark metrics](https://docs.splunk.com/Observability/gdi/spark/spark.html) it can monitor. 
	- This is Stripe's internal instructions on [how to use SignalFx](https://confluence.corp.stripe.com/display/OBS/SignalFx+Quickstart). It turns out that Stripe's internal signalfx instrumentation client will forward the metrics to Veneur, which then (probably) goes to signalfx.
	- Looks like [Stripe does support SignalFx API](https://confluence.corp.stripe.com/display/OBS/SignalFx+Quickstart#SignalFxQuickstart-SignalFXAPIIntegrations). This means that we could do some alerting in real-time using a service.
- What about [Veneur](https://github.com/stripe/veneur)? See [intro blog](https://stripe.com/blog/introducing-veneur-high-performance-and-global-aggregation-for-datadog).
- If we have to support real-time metrics for Spark 2.4, what are our options?
	- We can use the JVM Profiler's built-in KafkaOutputReporter, and send the data to Kafka, and land them in Hubble.
	- We can develop a new way to land the data to Prometheus, and then dashboard them in Grafana. This is an [article](https://www.infoq.com/articles/spark-application-monitoring-influxdb-grafana/) showing how to develop an InfluxDB reporter for JVM Profiler for dashboarding with Grafana. It won't help us because we don't have InfluxDB. Can we develop a reporter for Prometheus?
	- Looks like Prometheus has a [push gateway](https://github.com/prometheus/pushgateway), which may allow us to push the JVM Profiler data to Prometheus and Grafana by developing a new Prometheus reporter, although the doc says don't use this push gateway to turn Prometheus into a push based system.
- If we start with Spark 3, what's the shortest path?
	- Spark 3 has native support for Prometheus, which Stripe has.
- How to actually monitor Spark metrics?
	- [Monitor Sparkwith Grafana and Graphite](https://www.metricfire.com/blog/spark-performance-monitoring-using-graphite-and-grafana/) and also [Grafana Spark dashboards](https://github.com/hammerlab/grafana-spark-dashboards). Essentailly this company provides a hosted version of Graphite with an endpoint. Point your Spark metrics system to this sink, and then use Grafana to dashboard the metrics. We don't seem to use Graphite at Stripe.
	- [2019 Spark perf dashboard](https://db-blog.web.cern.ch/blog/luca-canali/2019-02-performance-dashboard-apache-spark) Interesting note here is that Influx DB has a Graphite-compactible endpoint, which means that if Spark can send metrics to Graphite, it can send metrics to InfluxDB. Unfortunately, I don't think Stripe has a graphite or an influxdb infrastructure.
- What other dataset we already have today?
	- [Add peak_execution_memory to spark.task_history and spark.stage_history tables.](https://git.corp.stripe.com/stripe-internal/zoolander/pull/63259). 
- How about I create a dashboard now with what we have and see if it helps?
- Upload jar to artifactory:
yichen@st-yichen1:~/stripe/jvm-profiler/target|master ⇒  pay artifact:upload /Users/yichen/stripe/jvm-profiler/target/jvm-profiler-1.0.0.jar \
--name com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar \
--owner batch-compute \
--source "https://github.com/uber-common/jvm-profiler" \
> --description "Uber's JVM Profiler"
{
  "repo": "thirdparty-managed",
  "path": "/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar",
  "created": "2022-09-22T18:39:16.799Z",
  "createdBy": "yichen",
  "downloadUri": "https://artifactory.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar",
  "mimeType": "application/java-archive",
  "size": "7220071",
  "checksums": {
    "sha1": "777bd25fb2dcb7a3433b5d96cc382cbd4037b617",
    "md5": "693a463d8851e06440ff46aa6e685c96",
    "sha256": "261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb"
  },
  "originalChecksums": {
    "sha1": "777bd25fb2dcb7a3433b5d96cc382cbd4037b617",
    "sha256": "261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb"
  },
  "uri": "https://artifactory.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar"
}
Successfully uploaded file.
Bazel rule for version 261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb of com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar:
http_archive(
    name = "com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar",
    sha256 = "261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb",
    urls = [
        "https://artifactory-content.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar",
    ],
)



- Where to upload jvm-profiler jar to in S3?
	- s3 is accessible from mydata.
	- How do I upload jar from laptop to s3? Through Mydata?
	- Looks like I can find the mydata server and use scp to copy files. See [example](https://confluence.corp.stripe.com/pages/viewpage.action?pageId=185601333)
	- Uploading failed because I don't have write permission. The message redirects me to https://go/s3-policy. 
- Upload jvm-profiler to S3
	- Using s3 under my user name (on mydata, or airflow-local) uses my personal access token via s3-authz-srv. 
- POC with airflow_local: 
	- `DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.jars=https://artifactory-content.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar --conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar`
```
DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.jars=https://artifactory-content.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar --conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar=reporter=com.uber.profiling.reporters.ConsoleOutputReporter,metricInterval=1000' ./bin/airflow-local run canary.SparkCanary --usm --hadoop-cluster hadoop-test --hadoop-queue canaries --usm-path-prefix "s3://qa-stripe-data/user/yichen/tmp2"



DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.jars=https://artifactory-content.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar --conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar=reporter=com.uber.profiling.reporters.ConsoleOutputReporter,metricInterval=1000' ./bin/airflow-local run airflow_functional_tests.MinutelySparkTask --use-dag-cache --usm 
```

However, looks like I cannot reference remote jar using http:
```
spark-submit log: 22/09/23 13:04:44 {} WARN org.apache.spark.deploy.DependencyUtils: Skip remote jar https://artifactory-content.stripe.build/artifactory/thirdparty-managed/com/uber/jvm-profiler/1.0.0/jvm-profiler-1.0.0.jar/261836cd6d415805ddb65c357209b8525d6f7c7a67d91f266c8ae8ed0c8795bb/jvm-profiler-1.0.0.jar
```

Now let me try using the artifactory instead:
```
DEPLOY_SPARK_SUBMIT_OPTIONS='--conf spark.jars.repositories=https://artifactory-content.stripe.build/artifactory/thirdparty-managed --conf spark.jars.packages=com.uber:jvm-profiler:1.0.0 --conf spark.driver.extraJavaOptions=-javaagent:jvm-profiler-1.0.0.jar=reporter=com.uber.profiling.reporters.ConsoleOutputReporter,metricInterval=1000' ./bin/airflow-local run airflow_functional_tests.MinutelySparkTask --use-dag-cache --usm 
```


As an example, how do we deploy async-profiler with our build system?
- Firstly, looks like the pre-compile build is packaged as a tar ball and uploaded to `https://artifactory-content.stripe.build/artifactory/github-releases/jvm-profiling-tools/async-profiler/releases/download/v2.7/async-profiler-2.7-linux-x64.tar.gz`
- Then, creaet a new `http_archive` rule, that can download the tarball, and then call a `java_import` rule, to make the jar file contained in the tarball available for import under the name `async_profiler`.


As an example, how do we deploy SparkMetricsPublisher?
- The `event_uploader` is packaged as a jar file, by using the `scala_library` rule. Looks like the `name="SparkMetricsPublisher"` means the target of the build for event_uploader.
- This target is then declared as part of `runtime_deps` for the `spark` library. That is, we have a `scala_library` named `spark`, which will build a jar, that will depend on the event_uploader jar in runtime.  This `runtime_deps` appears to be deployed with the Spark application together, aka `vendered`. Specifically, in the Spark environment we can see it under `System Classpath` : `/pay/hadoop/yarn/local/usercache/root/appcache/application_1664054358960_8274/container_e65_1664054358960_8274_01_000001/__spark_libs__/bkbdsscsseS_0.SparkMetricsPublisher.jar`
- Note that our hadoop configuration has `yarn.nodemanager.local-dirs=/pay/hadoop/yarn/local`. This means that the SparkMetricPublisher jar is deployed to each nodemanager.
- looks like this `spark` jar is not individually referenced, but instead all targets in this package including this jar target, are referenced as a whole, mostly in tests, but also in other related infrastructure code like zoolander/zoolander-archival/BUILD. What is `zoolander-archival`? 
- The `zoolander-archival` will call `scala_library` rule to generate a jar named `zoolander-archival-with-thrift`, which is a dependency of `encode_event_data_app`.

How does the SparkMetricsPublisher [dependency](https://livegrep.corp.stripe.com/view/stripe-internal/zoolander/data_common/src/scala/com/stripe/spark/BUILD#L47) work?
- it is declared as `scala_library` runtime_deps section, from the root of the repo.

How to build the jvm-profiler repo?
- See https://confluence.corp.stripe.com/display/DND/Jenkins+Configuration+User+Guide

