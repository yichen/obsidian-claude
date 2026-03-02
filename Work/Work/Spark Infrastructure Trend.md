#spark

* What projects each companies have been working on for Apache Spark?
	* Looks like most companies are improving the bottleneck of shuffle (either external shuffle service, or using bucketing to remove shuffle), security, improving joins (skew), running on k8s.
	* source: [Data+AI Summit 2021](https://databricks.com/dataaisummit/north-america-2021/sessions)
	* Databricks Youtube channel

	* LinkedIn
		* 2021: [Best Practices for enabling speculative execution on large scale platforms](https://databricks.com/session_na21/best-practices-for-enabling-speculative-execution-on-large-scale-platforms)
			* [slides](https://www.iteblog.com/ppt/data-ai-summit-2021/best-practices-for-enabling-speculative-execution-on-large-scale-platforms_iteblog.com.pdf)
		* 2021: [Magnet Shuffle Service](https://databricks.com/session_na21/magnet-shuffle-service-push-based-shuffle-at-linkedin)
		* 2020: [Tackling scaling challenges of Spark at LinkedIn](https://databricks.com/session_na20/tackling-scaling-challenges-of-apache-spark-at-linkedin)
		* [Spark at LinkedIn](https://www.linkedin.com/pulse/apache-spark-linkedin-sunitha-beeram/)
		* [Magnet: push shuffle service](https://engineering.linkedin.com/blog/2020/introducing-magnet)
		* 2020: [Schema management at scale](https://engineering.linkedin.com/blog/2020/advanced-schema-management-for-spark)
		* 2019: [# Optimizing Apache Spark SQL at LinkedIn](https://www.youtube.com/watch?v=Rok5wwUx-XI)
		* 2019: [Feature transformation engine for TensorFlow](https://engineering.linkedin.com/blog/2019/04/avro2tf--an-open-source-feature-transformation-engine-for-tensor)
		* 2016: [Dr. Elephant](https://engineering.linkedin.com/blog/2017/03/a-checkup-with-dr--elephant--one-year-later)
	* Netflix
		* 2019: [Open-sourcing Polynote: an IDE-inspired polyglot notebook](https://netflixtechblog.com/open-sourcing-polynote-an-ide-inspired-polyglot-notebook-7f929d3f447)
		* 2019: [Migrating to Spark at Netflix](https://www.youtube.com/watch?v=RVNud7tO2hA)
		* 2018: [Spark at Netflix](https://netflixtechblog.com/netflix-at-spark-ai-summit-2018-5304749ed7fa)
		* [Integrating Spark at Petabyte Scale](https://events.static.linuxfound.org/sites/events/files/slides/Netflix%20Integrating%20Spark%20at%20Petabyte%20Scale.pdf)
	* Yelp
		* 2019: [Smart Join Algorithms for Fighting Skew at Scale](https://docs.google.com/presentation/d/1AC6yqKjj-hfMYZxGb6mnJ4gn6tv_KscSHG_W7y1Py3A/edit#slide=id.p)
	* Facebook
		* 2021: [Skew mitigation for Facebook PetabyteScale Joins](https://databricks.com/session_eu20/skew-mitigation-for-facebook-petabytescale-joins)
		* 2020: [Securing Spark applications at Facebook](https://databricks.com/session_na20/securing-apache-spark-applications-at-facebook)
		* 2020: [Presto on Spark](https://databricks.com/session_na20/presto-on-apache-spark-a-tale-of-two-computation-engines)
		* 2020: [Cosco: Spark External shuffle service](https://databricks.com/session/cosco-an-efficient-facebook-scale-shuffle-service)
		* 2020: [Hive Bucketing in Apache Spark](https://databricks.com/session/hive-bucketing-in-apache-spark)
		* 2016: [Spark vs. Hive](https://engineering.fb.com/2016/08/31/core-data/apache-spark-scale-a-60-tb-production-use-case/)
		* 2017: [Use Spark for language model training](https://engineering.fb.com/2017/02/07/core-data/using-apache-spark-for-large-scale-language-model-training/)
	* NVidia
		* 2021: [Stage level scheduling improving big data and AI integration](https://databricks.com/session_na21/stage-level-scheduling-improving-big-data-and-ai-integration)
		* 2021: [Modernize Your Analytics Workloads for Spark 3.0](https://databricks.com/session_na21/modernize-your-analytics-workloads-for-apache-spark-3-0-and-beyond)
	* Workday
		* 2021: [Optimizing the Catalyst Optimizer](https://databricks.com/session_na21/optimizing-the-catalyst-optimizer-for-complex-plans)
		* 2020: [Improving broadcast joins](https://databricks.com/session_na20/on-improving-broadcast-joins-in-apache-spark-sql)
	* VMware
		* 2020: [Spark 3 Deployment with Hypervisor-Native Kubernetes](https://databricks.com/session_na20/simplify-and-boost-spark-3-deployments-with-hypervisor-native-kubernetes)
	* Google
		* 2021: [Scaling Spark on Kubernetes](https://databricks.com/session_na21/scaling-your-data-pipelines-with-apache-spark-on-kubernetes)
	* Uber
		* 2021: [Tale of scaling Zeus to Petabytes](https://databricks.com/session_na21/tale-of-scaling-zeus-to-petabytes-of-shuffle-data-uber)
		* 2020: [How to perf-tune Spark apps in large clusters](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
		* 2020: [Zeus: Uber's shuffle as a service](https://databricks.com/session_na20/zeus-ubers-highly-scalable-and-distributed-shuffle-as-a-service)
		* 2019: [Uber Spark Compute Service (uSCS)](https://eng.uber.com/uscs-apache-spark/)
	* ByteDance
		* 2020:[Bucketing 2.0: improve Spark SQL perf by removing shuffle](https://databricks.com/session_na20/bucketing-2-0-improve-spark-sql-performance-by-removing-shuffle)
	* IBM
		* 2021: [Enabling Vectorized Engine in Spark](https://databricks.com/session_na21/enabling-vectorized-engine-in-apache-spark)
		* 2020: [Fine tuning Spark jobs](https://databricks.com/session_na20/fine-tuning-and-enhancing-performance-of-apache-spark-jobs)
		* 2020: [SQL Perf improvements in Spark 3](https://databricks.com/session_na20/sql-performance-improvements-at-a-glance-in-apache-spark-3-0)
	* Adobe
		* 2021: [Redis + Spark](https://databricks.com/session_na21/redis-apache-spark-swiss-army-knife-meets-kitchen-sink)
		* 2020: [Enforcing GDPR and CCPA with Spark](https://databricks.com/session_na20/taming-the-search-a-practical-way-of-enforcing-gdpr-and-ccpa-in-very-large-datasets-with-apache-spark)
	* Apple
		* 2021: [Improving Spark for Dynamic Allocation and Spot instances](https://databricks.com/session_na21/improving-apache-spark-for-dynamic-allocation-and-spot-instances)
		* 2021: [The Rise of ZStandard: spark/parquet/orc/avro](https://databricks.com/session_na21/the-rise-of-zstandard-apache-spark-parquet-orc-avro)
		* 2021: [Structured Streaming at Apple](https://databricks.com/session_na21/structured-streaming-use-cases-at-apple)
		* 2021: [Data distribution and Ordering for efficient Data Source V2](https://databricks.com/session_na21/data-distribution-and-ordering-for-efficient-data-source-v2)
		* 2020: [Getting started contributing to Spark](https://databricks.com/session_na20/getting-started-contributing-to-apache-spark-from-pr-cr-jira-and-beyond)
		* 2020: [Native support of Prometheus Monitoring in Spark 3](https://databricks.com/session_na20/native-support-of-prometheus-monitoring-in-apache-spark-3-0)
		* 2020: [Patterns and operational insights from Delta Lake](https://databricks.com/session_na20/patterns-and-operational-insights-from-the-first-users-of-delta-lake)
	* Databriks
		* 2020: [Best practices of Spark with Delta](https://databricks.com/session_na20/best-practices-for-building-robust-data-platform-with-apache-spark-and-delta)
		* 2020: [Koalas: Pandas on Spark NA](https://databricks.com/session_na20/koalas-pandas-on-apache-spark)
	* Pinterest
		* 2020: [Migrate Spark from HDFS to S3](https://databricks.com/session_na20/from-hdfs-to-s3-migrate-pinterest-apache-spark-clusters)
	* Airbnb
		* 2020: [Zipline](https://databricks.com/session_na20/zipline-a-declarative-feature-engineering-framework)
		* 2020: [Sputnik](https://databricks.com/session_na20/sputnik-airbnbs-apache-spark-framework-for-data-engineering)
	* Zillow
		* 2020: [Next-gen data pipeline with Spark](https://databricks.com/session_na20/designing-the-next-generation-of-data-pipelines-at-zillow-with-apache-spark)
	* Lyft
		* 2021: [Hybrid Spark architecture with YARN and Kubernetes](https://databricks.com/session_na21/hybrid-apache-spark-architecture-with-yarn-and-kubernetes)
		* 2020:[Cloud-native Spark scheduling with YuniKorn Scheduler](https://databricks.com/session_na20/cloud-native-apache-spark-scheduling-with-yunikorn-scheduler)
		* 2020: [Fugue: unifying Spark and non-spark ecosystems for Data Analytics](https://databricks.com/session_na20/fugue-unifying-spark-and-non-spark-ecosystems-for-big-data-analytics)
	* Microsoft
		* 2020: [SparkCruise: automatic computation reuse in Spark](https://databricks.com/session_na20/sparkcruise-automatic-computation-reuse-in-apache-spark)
	* Intel
		* 2020: [Accelerating Spark SQL with Apache Arrow](https://databricks.com/session_na20/accelerating-spark-sql-workloads-to-50x-performance-with-apache-arrow-based-fpga-accelerators)
		* 2020: [Accelerating Spark shuffle with remote persistent memory pools](https://databricks.com/session_na20/accelerating-apache-spark-shuffle-for-data-analytics-on-the-cloud-with-remote-persistent-memory-pools)
	* Alibaba
		* 2020: [Simplify CDC Pipeline with Spark streaming](https://databricks.com/session_na20/simplify-cdc-pipeline-with-spark-streaming-sql-and-delta-lake)
	* Zillow
		* 2021: [Zillow's self-service ETL](https://databricks.com/session_na21/empowering-zillows-developers-with-self-service-etl)
	* Databricks
		* 2021: [# Cost Efficiency Strategies for Managed Apache Spark Service](https://www.youtube.com/watch?v=KdnJJFlo7vI)
		* 2021: [Comprehensive View on Internals in Spark 3.2](https://databricks.com/session_na21/comprehensive-view-on-intervals-in-apache-spark-3-2)
		* 2021: [Deep dive into the new features of Spark 3.1](https://databricks.com/session_na21/deep-dive-into-the-new-features-of-apache-spark-3-1)
		* 2021: [Koalas: how well does it work](https://databricks.com/session_na21/koalas-does-koalas-work-well-or-not)
		* 2020: [Spark workload diagnostics](https://databricks.com/session_na20/tracing-the-breadcrumbs-apache-spark-workload-diagnostics)
		* 2020: [# Adaptive Query Execution: Speeding Up Spark SQL at Runtime](https://www.youtube.com/watch?v=jzrEc4r90N8)
		* 2020: [Deep dive new features of Spark 3](https://databricks.com/session_na20/deep-dive-into-the-new-features-of-apache-spark-3-0)
		* 2019: [# A Deep Dive into Query Execution Engine of Spark SQL](https://www.youtube.com/watch?v=ywPuZ_WrHT0)
		* 2019: [Accelerating Spark by orders of magnitude with GPUs](https://www.youtube.com/watch?v=Qw-TB6EHmR8)
		* 2019: [# The Apache Spark™ Cost-Based Optimizer](https://www.youtube.com/watch?v=W8rDdl-d5UY)
		* 2018: [# Deep Dive into the Apache Spark Scheduler (Xingbo Jiang)](https://www.youtube.com/watch?v=rpKjcMoega0)
	* Performance Tuning
		* 2020: [# How to Performance-Tune Apache Spark Applications in Large Clusters](https://www.youtube.com/watch?v=uVZ0fc1dVFY)
		* 2020: [# Top Tuning Tips for Spark 3.0 and Delta Lake on Databricks](https://www.youtube.com/watch?v=hcoMHnTcvmg)
		* 2020: [# Common Strategies for Improving Performance on Your Delta Lakehouse](https://www.youtube.com/watch?v=lhlPqHlZdN0)
		* 2019: [# Apache Spark Core—Deep Dive—Proper Optimization Daniel Tomes Databricks](https://www.youtube.com/watch?v=daXEp4HmS-E)
		* 2019: [# How to Automate Performance Tuning for Apache Spark -Jean Yves Stephan (Data Mechanics)](https://www.youtube.com/watch?v=ph_2xwVjCGs)
		* 2018: [# Using Apache Spark to Tune Spark](https://www.youtube.com/watch?v=r0x0G5G3mAY)
		* 2017: [# Tuning Apache Spark for Large Scale Workloads](https://www.youtube.com/watch?v=5dga0UT4RI8)
	* Security
		* 2021: [Scaling privacy](https://databricks.com/session_na21/scaling-privacy-in-a-spark-ecosystem)
		* 2020: [Case study and automation strategies to protect sensitive data](https://databricks.com/session_na20/case-study-and-automation-strategies-to-protect-sensitive-data)
		* 2020: [find and protect your data in databricks with privacera and apache ranger](https://databricks.com/session_na20/find-and-protect-your-crown-jewels-in-databricks-with-privacera-and-apache-ranger)
	* Monitoring
		* 2021: [Monitor Spark 3 on k8s using metrics and plugins](https://databricks.com/session_na21/monitor-apache-spark-3-on-kubernetes-using-metrics-and-plugins)
	* Use Cases
		* 2017: [How Apache Spark and AI Powers UberEats](https://databricks.com/session/how-apache-spark-and-ai-powers-ubereats)