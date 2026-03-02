
#slack/journal

### 2024-08-05

Q2 EMR cost tuning
- Right-sizing EBS for all EMR master nodes ([PR](https://slack-github.com/slack/ops-go/pull/6277))
- Reduce waste from cluster startups as we frequently tear-down and start-up new clusters ([PR](https://slack-github.com/slack/ops-go/pull/6317), [PR](https://slack-github.com/slack/ops-go/pull/6338))
- Deprecated prod-security-emr6 cluster ([PR](https://slack-github.com/slack/ops-go/pull/6313)). It's workload are merged into larger clusters that only run on-demand instances, with higher reliability and lower cost.
- Future tuning of EC2 instance types. 
	- Continue removing undesirable instances from EMR clusters ([PR](https://slack-github.com/slack/ops-go/pull/6310/files), [PR](https://slack-github.com/slack/ops-go/pull/6308))
	- In this quarter, we further removed some EC2 instance types from our EMR clusters. We've removed all m6 and m7 families ([PR](https://slack-github.com/slack/ops-go/pull/6292/files), [PR](https://slack-github.com/slack/ops-go/pull/6307/files), [PR](https://slack-github.com/slack/ops-go/pull/6320), [PR](https://slack-github.com/slack/ops-go/pull/6329)) from our clusters because they have lower memory-to-cpu ratio than desired. We also further removed 
- Moved dma cluster to us-east-1b so it can share the same ODCR pool with data-platform cluster and reduce ODCR waste ([PR](https://slack-github.com/slack/ops-go/pull/6437), [PR](https://slack-github.com/slack/ops-go/pull/6441)).
- Tune dynamic allocation configs to reduce waste ([PR](https://slack-github.com/slack/ops-go/pull/6501))
- 


Offsite September 2024: https://slack.enterprise.slack.com/canvas/C07BXDC1VMY?focus_section_id=temp:C:XAR19906b9b69a44bad9eec7b4b9

- Recommend staying at Hayyat
- 

### 2024-08-01

Other remaining S3 permission issue not resolved: https://slack-pde.slack.com/archives/C01FB307Z7A/p1722358058434939




S3 Permissions (https://slack-pde.slack.com/archives/C01FB307Z7A/p1722361029371789)
The user created a new IAM role, but the DI team owns the bucket, so we will need to grant them the permission for this new role.
- What's this new role?
	- Looks like they created a new service account in kubernetes called dev-athena, and annotate this service account with a role = arn:aws:iam::047889250958:role/dev-athena. In EKS, you can map AWS IAM Roles to Kubernetes ServiceAccounts. This is known as IAM Roles for Service Accounts (IRSA), provides a secure and efficient way to grant your pods access to AWS services without managing credentials directly.
	- It appears that this number 047889250958, is the account ID of a child account (accnt-data-eng-and-arch-dev), and they may be asking the permission from a root account.
- The Terraform configs for Production data warehouse: chef-repo/terraform/accnt-datawarehouse-prod/. The account ID is **122735864621**.
- 


Apache Spark on Kubernetes: A Technical Deep DiveKubernetes: A Technical Deep Dive: https://youtu.be/5-4X3HylQQo?si=A3hThDm91LIkHnnT
- Why spark on kubernetes?
	- The container/kubernetes ecosystem.
	- multi-cloud and hybrid environment 
		- Workload portability
	- Resource sharing between batch, ser.
	- multi-cloud and hybrid environment 
		- Workload portability
	- Resource sharing between batch, serving, and stateful workloads
		- streamlined developer experiences
		- reduced operational costs
		- improved infrastructure utilization 
- 

### 2024-06-14
Channel Audit
- [Jigar's message on Slack 3 months ago](https://slack-pde.slack.com/archives/GH6JNTARX/p1711141879660199), referencing the [readme](https://slack-github.com/slack/data-airflow/tree/master/channel_audit).
- 
### 2024-06-12
Understand [chef for EMR](https://slack-github.com/slack/chef-repo/tree/master/emr/cookbooks/emr)
- Understand Chef
	- Once the EMR cluster is running, you can use Chef to manage configurations on the individual cluster nodes (i.e. master, core nodes)
	- You can install the chef client on the nodes and configure it to point to your Chef server.
	- This allows you to manage software installations, configuration files, and user management tasks on the cluster nodes using Chef recipes.
	- Chef uses ERB (Embedded Ruby) templates to dynamically generate static text files during node configuration. An ERB file is a text file with a .erb extension. It contains a mix of static content and Ruby code snippets enclosed within <% %> tags.
	- default[] is used to access and set default attributes with the current node. These are typically set in the attributes/default.rb file. It is primarily used for reading/accessing, not for setting/writing.
	- `recipes/default.rb` is the entry point for the cookbook. 


### 2024-05-30
[Apache Celeborn: Make Spark and Flink Faster](https://www.youtube.com/watch?v=JPTJe8p9Hv4&t=34s&ab_channel=TheASF)
- Why?
	- Make the compute nodes stateless, no local disk
	- Reorganize the shuffle data, make them more IO friendly, improving reliability.
-  Background
	- Challenges of current shuffle
		- Consumes 15% resources.
			- Writing at mapper side:
				- Ordering locally during writing, which consumes memory.
				- If more memory is needed, disk spill requires IO.
			- Reading at Reducer side
				- Thousands of concurrent requests to read small amount of data with random read, resulting low efficiency IO.
			- Number of shuffle files, M x R. The sheer number of shuffle files written is a major source of performance degradation.
		- Writing amplification.
- Celeborn
	- From Aliyun
	- Support HDFS and local disk.
- Celeborn is fast
	- Push style shuffle. At the beginning of shuffle, the master allocate 1 worker (or 2 for replication). Mapper will push the shuffle data to the workers. Because of the push based shuffle, there is no need for sorting.
	- Shuffle read phase, the reducer just need to read from one file. It's a sequential read pattern (not random read)
	- What if one partition generate too big shuffle file? Split happens, and splits are distributed across worker. The reducer will read splits from all these workers.
	- Async. At mapper side, the celeborn will not block the task thread. There is an async step to flush the data in memory to disk, through pipelining.
	- Columnar shuffle: shuffle size reduces by 40%. The shuffle client will transform the row layout into column layout. This may consume some resources for interpretation. In this case, we borrowed the Spark's code generation technique. As a result, instead of doing interpretation based execution, we are doing compilation based execution, avoiding the overhead of traditional interpreted exeution.
- Gluten + Celeborn: integration.
- Multi-layer storage: memory / local disk / DFS / Object Store
	- What if local disk is not big enough?
	- Choose 1-3 layers as you will
- Reliability
	- 2 replicas.
		- When a data push fails, Celeborn doesn't consider the worker failed. Instead, consider it a temporary failure, and push the data to a different worker. Only at the stage end, it will check if there are data loss.
	- Fast, rolling upgrades
		- When rebooting a worker, reports to master, stop pushing more files to this worker. Flush data to local disk (leveldb).
	- Traffic Control
		- protect memory pressure
		- credit based traffic control
	- Load Balancing
		- test disk's health, heartbeat to master
- Elasticity
	- Mixed: Work with HDFS/YARN/Celeborn
	- Standalone: not using HDFS
	- Total disaggregate from compute and storage.
	- Example:
		- 1000 worker
		- Celeborn on k8s, 500 worker, each with 20G memory.
		- 1000 worker, rolling upgrade, batch of 10, each batch takes 2 minutes.
- Benchmark
	- 


### 2024-05-15
Meeting with Amazon EMR support
- Improve decommission: 
	- yarn.resourcemanager.nodemanager-graceful-decommission-timeout-secs: This is the maximal time to wait for running containers and applications to complete before transition a DECOMMISSIONING node into DECOMMISSIONED.
	- spark.blacklist.decommissioning.timeout: This is the maximal time that Spark does not schedule new tasks on executors running on that node. Tasks already running are allowed to complete.
- Difference between Managed scaling and YARN scaling:
	- Managed Scaling, the signal comes in every 5 to 10 seconds. For manual scaling, the signal comes in 5-minutes interval.
- Best Practices
	- https://aws.github.io/aws-emr-best-practices/docs/bestpractices/Features/Managed%20Scaling/best_practices/

  

  

spark.blacklist.decommissioning.timeout: This is the maximal time that Spark does not schedule new tasks on executors running on that node. Tasks already running are allowed to complete.

### 2024-04-26

Understanding the main risks of running Spark on Kubernetes
- [Apple's talk in 2022](https://www.youtube.com/watch?v=LVlOv0snXog&t=75s&ab_channel=Databricks)
	- Decouple compute and storage, inorder to scale them independent to each other.
- [Ziverge talk in 2022](https://www.youtube.com/watch?v=8bRtqDfgEGI&ab_channel=Ziverge)
- [Spark on kubernetes with spot instances 2022](https://www.youtube.com/watch?v=te9PaxKIabA&t=12s&ab_channel=Databricks)
	- 

### 2024-03-06

This blog shares some ideas on how to debug YARN nodemanager out of disk space issue: https://laveenabachani.medium.com/aws-emr-memory-scaling-5f2b1a54549

### 2024-03-01

1:1 with Alex Bohr
- Alex was at Apple iCloud for two years. Tinder was his most productive employer.
- Alex's manager (Jonny Cao) was asked about the cost attribution, about their new project, if it is more expensive than the Secor. We have some top-down pressure about the cost of new project.
- We can't even tell how much resources our job is using. We run 90% fail, and the final retry succeed. We are wasting a lot of resources.
- Parker will start asking questions. He is the new CTO.

Figure out how to use r6g.16xlarge
- Looks like [this doc](https://docs.aws.amazon.com/cli/latest/reference/emr/create-cluster.html#) shows how to take the ODCR instances.
- Follow [EMR rollout strategy](https://docs.tinyspeck.com/data/runbooks/hadoop/emr_rollout_strategy/) with a test cluster.
	- Test cluster is launched using a Jenkins job.

### 2024-02-27

EBS Cost in EMR
- [EBS in EMR doc](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-storage.html)
	- Amazon EBS works differently within Amazon EMR than it does with regular Amazon EC2 instances. Amazon EBS volumes attached to Amazon EMR clusters are ephemeral: the volumes are deleted upon cluster and instance termination (for example, when shrinking instance groups), so you shouldn't expect data to persist. Although the data is ephemeral, it is possible that data in HDFS could be replicated depending on the number and specialization of nodes in the cluster. When you add Amazon EBS storage volumes, these are mounted as additional volumes. They are not a part of the boot volume. YARN is configured to use all the additional volumes, but you are responsible for allocating the additional volumes as local storage (for local log files, for example).
	- We split any increased storage across multiple volumes. This gives increased IOPS performance and, in turn, increased performance for some standardized workloads. If you want to use a different Amazon EBS instance storage configuration, you can specify this when you create an EMR cluster or add nodes to an existing cluster. You can use Amazon EBS gp2 or gp3 volumes as root volumes, and add gp2 or gp3 volumes as additional volumes. For more information, see [Specifying additional EBS storage volumes](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-storage.html#emr-plan-storage-additional-ebs-volumes).


How to configure EMR Instance Fleet?
- You can have one instance fleet, and only one, per node type (primary, core, task). You can specify up to five Amazon EC2 instance types for each fleet on the AWS Management Console (or a maximum of 30 types per instance fleet when you create a cluster using the AWS CLI or Amazon EMR API and an [Allocation strategy for instance fleets](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-instance-fleet.html#emr-instance-fleet-allocation-strategy)).
- For each fleet, you can specify one of the following allocation strategies for your Spot Instances: price-capacity optimized, capacity-optimized, lowest-price, or diversified across all pools.
- For each fleet, you can apply lowest-price allocation strategy for your On-Demand Instances; you can't customize the allocation strategy for On-Demand Instances.
- Amazon EMR chooses any combination of these EC2 instance types to fulfill your target capacities. Because Amazon EMR wants to fill target capacity completely, an overage might happen.
- [Use capacity reservations with instance fleets](https://docs.aws.amazon.com/emr/latest/ManagementGuide/on-demand-capacity-reservations.html)
	- To launch On-Demand Instance fleets with capacity reservations options, attach additional service role permissions which are required to use capacity reservation options.
	- Since capacity reservation options must be used together with On-Demand allocation strategy, you also have to include the permissions required for allocation strategy in your service role and managed policy. For more information, see [Allocation strategy permissions](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-instance-fleet.html#create-cluster-allocation-policy).
	- Use targeted capacity reservations first: `use-capacity-reservations-first`
		- you can choose to override the lowest-price allocation strategy and prioritize using available targeted capacity reservations first.
		- In this case, Amazon EMR evaluates all the instance pools with targeted capacity reservations specified in the launch request and picks the one with the lowest price that has sufficient capacity to launch all the requested core nodes. If none of the instance pools with targeted capacity reservations have sufficient capacity for core nodes, Amazon EMR falls back to the best-effort case
		- Once the core nodes are provisioned, the Availability Zone is selected and fixed. Amazon EMR provisions task nodes into instance pools with targeted capacity reservations, starting with the lowest-priced ones first, in the selected Availability Zone until all the task nodes are provisioned.


JoeyT 1:1
- Hourly job, its common to run more than an hour
- This chart may shows the hourly job run time: https://slack-airflow-prod.tinyspeck.com/dags/vitess_query_log_hourly_v1/duration?days=30
- Been at Slack for 3+ years, fresh out of college. Been at the data ingestion team the whole time, almost the longest in the team now.
- Many senior member of DI team left (adam hudson, deepak, Ash)
- Impression is that DI team has larger surface area.
- Spark log situation
	- Haven't thought about it much, assume it is difficult problem.
	- All actual application log goes to stderr.log in YARN.
	- Lots of netty logs that are not useful. The volume is large, so these noise makes it difficult to debug. 	
	- The number 1 problem, Spark history logs may be difficult to access, especially when the job is long running. An example, bootstrapping an iceberg table, 6TB, taking 8 hours to run, failed with an log aggregation error, can't debug because the log is not available.
	- The log can be so big that it will crash the browser (YARN's jobhistory UI)
- Spark metrics
	- We have had two attempts before to dump Spark metrics in data warehouse. We created a DAG that talks to Livy. Not sure if it is still working with EMR6 upgrade.
	- An intern project, aggregated Spark insights. 
	- For data ingestion team perspective, it will be very helpful. Many jobs fail with OOM error, and our default response is to increase memory instead of partition count.
	- ingestion and metrics foundation teams will be the biggest consumer of EMR resources. 

EMR Spot or Not
- We use "Instance Fleet" for EMR nodes. In this case, the capacity is measured by "weighted capacity units." These units aim to reflect the relative processing power of different instance types within the fleet. 
	- The "default unit": the number of vCPUs for each instance type is used as the weighted capacity unit.
	- Customization: you can customize the unit for each instance type within the fleet. This allows you to define a unit that best represents the processing power relevant to your application, regardless of vCPU count.
	- Capacity Target. You specify a target capacity in these weighted capacity units. This determines the overall processing power of the fleet.
- Note that for all CORE nodes, we have 200 units for the fleet of `r6g.2xlarge` instances, which translated to 100 physical nodes. So I guess it means each of these instance is 2 units of capacity.

### 2024-02-16
#### Understand our Spot usage
- For `data-platform-emr6` cluster, spot fleet is configured [here](https://slack-github.com/slack/ops-go/blob/dd2909fe235bb3e0963d101f1ac002842382607f/emradm/data/emr/data-platform-emr6.json).
	- For Core nodes, we are bidding for the following types:
		- rg.2xlarge
		- r6gd.2xlarge
		- r6g.4xlarge
		- r6gd.4xlarge
		- r6g.8xlarge
		- r6g.12xlarge
		- r7g.2xlarge
		- r7gd.2xlarge
		- r7g.4xlarge
		- r7g.8xlarge
		- r7g.12xlarge
		- m6g.4xlarge
		- m6g.8xlarge
		- m6g.12xlarge
		- c6g.8xlarge
		- c6gd.8xlarge
		- c6gn.8xlarge
		- c6g.12xlarge
		- c6g.16xlarge
		- c7g.8xlarge
		- c7gd.8xlarge
		- r7iz.8xlarge
		- r7iz.12xlarge
		- r7iz.16xlarge
		- i4g.4xlarge
		- i4g.8xlarge
		- i4g.16xlarge
		- 

### 2024-02-14

#### Samuel Bock
- Living in Minnesota
- 3y and 3m. Joined 2020. 
- Used to be in the data platform
- Quarry, developed in August 2021, deployed in Winter 2021. One of the motivation was GovSlack. It's basically a baby genie.
- Genie
	- We want to use MySQL for backend, Genie uses column names that are reserved.
	- 3 workers now, pods in kubernetes. What if we need more? We may need a leader node in Genie to spin up new worker nodes. Genie already have two ways: (1) run locally on worker node, and (2) use Netflix container system to spin up a new pod.
- Bedrocks
	- We have a lot of scaling challenges using k8s. kube get takes 6 seconds to respond. 
	- Bedrock at Slack: everything run in the default namespace. 
- PyGenie: Python client to interact with Genie.
	- We use that as the backbone for how Airflow (Python) talk to Genie.
- Project Cobbler (#proj-cobbler)
	- The goal is to collect all metrics across data engineering to tell the health of the system.
	- Nikhill is running this project


#### EMR Edge Node (Gateway Machines) Setup
- Installing the edge node is as easy as adding a node to the cluster. The only difference is that on the edge-node you will only deploy client software ONLY e.g SQOOP, PIG, HDFS, YARN, HBase, SPARK, ZK HIVE or HUE etc to enable you to for example to run HDFS commands on the edge-node.
- To enable communication between the outside network and the Hadoop cluster, edge nodes need to be multi-homed into the private subnet of the Hadoop cluster as well as into the corporate network.
- A multi-homed computer is one that has dedicated connections to multiple networks. This is a practical illustration of why edge nodes are perfectly suited for interaction with the world outside the Hadoop cluster. Keeping your Hadoop cluster in its own private subnet is an excellent practice, so these edge nodes serve as a controlled window inside the cluster
- Example on how to setup Edge Nodes for EMR 5.1: https://doc.dataiku.com/app-notes/5.1/emr-edge-node/
- 
#### Spark integration with Genie
- Clusters, commands, applications are all considered resources. Any files these resources depend on should be uploaded somewhere Genie can access (S3 etc)
	- Tagging of the resources, particularly Clusters and Commands, is important. Genie will use the tags in order to find a cluster/command combination to run a job.
	- Once resources are registered, they should be linked together.
		- Commands for a Cluster: means that this cluster can run a given set of commands. If a command is not linked to a cluster it cannot be used to run a job.
		- Applications for a Command: means that a command has a dependency on said applications. The order of the applications added is important because Genie will setup the applications in that order. Meaning if one application depends on another (e.g. Spark depends on Hadoop on classpath for YARN mode) Hadoop should be ordered first.
- Job Submission
	- cluster and command matching
	- All dependencies which aren't sent as attachments must already be uploaded somewhere Genie can access them (e.g. S3).
	- Users should familiarize themselves with whatever the executable for their desired command includes. It is possible that the admin has setup some default parameters they should know.
	- If a cluster/command combination is found Genie will then attempt to determine if the node can run the job. By this it means it will check the amount of client memory the job requires against the available memory in the Genie allocation. If there is enough the job will be accepted and will be run on this node and the jobs memory is subtracted from the available pool. If not it will be rejected with a 503 error message and user should retry later.
	- Once a job has been accepted to run on a Genie node, a workflow is executed in order to setup the job working directory and launch the job. 
- Cluster
	- Looks like this term usually means a physical cluster (a Hadoop cluster, or Presto cluster). It will include configuration files linked to `configs` property. Strangely, the `setupFile` is empty. Maybe that was delayed to the setupFile per application.
- Commands and Applications
	- At Netflix, they are static and managed by a git repo, published to S3 when deployed. 
	- 
- The setup file effectively is the installation script for the dependencies. The expectation is that after it is run the application is successfully configured in the job working directory.
	- For example, there is a Hadoop JSON file, which reference to a `setupFile` which points to a shell script living on S3. This shell script will set up the working directory and environment.
	- For Spark, there is a JSON file, which references a `setupFile`, and a `configs` which is also the `spark-env.sh` for the corresponding Spark version. The dependencies is the `spark-1.6.1.tgz`. Then, in the setup file shell script, it will download the dependency tgz (`spark-1.6.1.tgz`) and configure the working directory and environment variables. 
- commands for a cluster
	- when commands are added to a cluster they should be in priority order. If two commands both match a users tags for a job the one higher in the list will be used. This allows us to switch defaults quickly and transparently.
	- In API, a cluster may contain multiple commands. Example URL for a hadoop cluster: [https://genieHost/api/v3/clusters/bdp_h2query_20161108_204556/commands](https://geniehost/api/v3/clusters/bdp_h2query_20161108_204556/commands)
- Cluster
	- looks like a cluster can have different Spark version included. 
	- Example of clusters here are hadoop, and prosto.
- applications for a command
	- Looks like the concept of "application" in Genie means the application framework, like Spark, Presto, etc, similar to what application means for EMR, not the final individual Spark applications (which may correspond to the concept of jobs)
	- Linking applications to a command tells Genie that these applications need to be downloaded and setup in order to successfully run the command. The order of the applications will be the order of the download and setup is performed so dependencies between applications should be managed via this order.
	- URL example to show that a command (by ID) can contain multiple applications. [https://genieHost/api/v3/commands/presto0149/applications](https://geniehost/api/v3/commands/presto0149/applications)
	- Since we submit Spark jobs to YARN clusters in order to run the Spark submit commands we need both Spark and Hadoop applications installed and configured on the job classpath in order to run. 
- Job Submission Process
	- `clusterCriterias` will decide which cluster the job will be submitted to, filtering by tags. 

### 2024-02-13
#### Meeting with Tom Liao (@tliao)
- What bothers you when you use our Data Infrastructure?
	- At Data Tools team, our main consumption is not Spark, mainly Presto/Trino. It's query heavy, not pipeline heavy. 
	- We also own the notebook (jupyterhub). It's a hot potato that's been passed around. We are not subject matter. It's an old service. 
		- Data Scientists have a framework called SQLPen, a wrapper to build pipelines easily. Many of them use notebooks when they use SQLPen.
- What's your priority in your team?
	- Tableau
		- I was told Tableau will replace ATS dashboards. The more we know, less people are talking about that. I will be surprised to be able to shut down ATS in 3-4 years. 
		- Talked about Superset/Looker/Databricks, never had traction. Our customers are not pushing hard for it, so it is difficult to justify the priority.
	- Metrics Explorer.
- Data Tools are most software engineering focused inside DE.
	- We have to borrow designer and UX.
- Who I should meet?
	- Samuel Bock (data orchestration)
	- Metrics foundation: [@Nedra](https://slack-pde.slack.com/team/U02C8NYECDA) [@jcalvert](https://slack-pde.slack.com/team/U034CKBR1FF)

#### Meeting with Stan
- Park City, UT, 3 ski resorts.
- What's your opinion about our Spark infrastructure and EMR? 
- In your opinion, what's your main pain points when using Spark on EMR?
- What's the current plan for Netflix Genie for Spark?
	- Quarry will go away after Genie. 
	- One of the key contributor of Genie works at Salesforce.
	- Sam is a staff engineer in data orchestration team working on Genie.
	- Jigar is from DI working on k8s.
	- Spark Genie.
	- There is a [genie-dev](https://genie-dev.tinyspeck.com/jobs) that runs Trino. If you click on submit command, once configured, you should be able to see.
	- Stan: I encourage you to configure the spark-submit yourself. I can show you the docs. I can show you how Netflix configure Trino, and you can play with that. 
		- This is the [Netflix example](https://github.com/Netflix/genie/blob/master/genie-docs/src/docs/asciidoc/concepts/_netflixExample.adoc). Check other files in the same directory. 
		- I will do the lightning talk this Friday.
- What are the main technical challenges?
- What are the main non-technical resistance? 

#### Understanding Spark YARN logs
- Looks like we do have YARN container logs persisted onto S3. We launch EMR clusters to enable persisted logs, and the S3 location are specified as `s3://slack-ops-emr-us-east-1/emr-debug-logs/`. The cluster ID for  `prod-data-platform-emr6` today is `j-2CI6YUHOD683M`, so this is an example S3 location for an application: `s3://slack-ops-emr-us-east-1/emr-debug-logs/j-2CI6YUHOD683M/containers/application_1707853538088_0282/`
- So it's confirmed that we do have yarn logs in S3 that is served by the JobHistory Server. The question now is if there is a good way to serve them through the UI? Or do we have to figure out a way to proxy them? 

### 2024-02-12

#### How does Quarry work when it comes to submitting Spark jobs?
- Looks like it is just a wrapper around the Apache Livy

#### HMS Knowledge Transfer Notes
- [slack/data-hive-metastore](https://slack-github.com/slack/data-hive-metastore). 
	- This code base mainly serve trino traffic. This is a bedrock service. Why EMR is not included? It's because EMR has their own meta stores.
	- `scripts/entrypoint.sh` This is the entry point. We moved to open source HMS tarball. In the last quarter, upgraded the Presto HMS, and stopped using Hive fork, but now using the open-source version instead. The open source hive tarball is picked up directly from Hive releases website at apache.org . Referenced in `have_jar_name` in this entry point (`apache-hive-3.1.3-bin.tar.gz`). The reason to use open-source tarball instead of the folk is operational cost, as we receive a lot of security tickets.
	- Another change: copied all configs under the `/config/conf/` directory from the hive folk into our bedrock app. 
	- Deployment: currently deploy to commercial prod, commercial dev, and gov dev. We still need to push to gov prod (on EC2, not on bedrock). Somebody will need to pick this up. Need to talk to Amy, ask if it is OK to push to Gov Prod. 
	- How to test this HMS? There is a `presto-hive-metastore` Jenkins pipeline. 
- HMS DB upgrade
	- Backed by RDS for metadata DB. 
	- EMR and Trino all share the same DB (even though the HMS thrift services are separate)
	- Upgrading is pretty involved. See Google doc with title `Hive Catalog Migration Prod Rollout runbook`
		- Mainly 4 things to take care of: pre-work, upgrade procedures, revert.
		- On upgrade day, we know exactly what commands we need to run, and if something happens, what commands to run to revert.
	- We just did the upgrade from 2 to 3 last year (we didn't upgrade for 5+ years). Most likely we don't have to do this for a while. Although we are talking about more frequent upgrades. The whole process took 4-5 hours. The meat of the process is the schemaTool itself (`sudo hive --service schemaTool --upgradeSchema` command). It depends on the number of rows in the database. An idea is to do some clean up, pruning, to reduce the number of rows and reduce the upgrade time.
	- We could try out blue-green deployment AWS provides. We don't want the data to diverge 
- Main operational changes?
	- heap memory issues. We saw that a couple of weeks ago.
	- HMS itself. We have seen bugs, jobs failing.
	- We have not seen incidents with users dropping large tables.
- Do we use HMS Hook and publish some metrics to data warehouse?
	- From ATS, we can query Hive DB directly via Presto.
	- We sqoop Hive RDS, and the data should be available in the data warehouse.


#### Livy Logs
- Livy UI has two blocks, one for interaction sessions, and one for batch sessions.
- There are two logs that's accessible per Spark application, one is called session logs, and another one is called Driver Log.
- Click on session log of a running interactive session, it shows only in the `stderr` output for a running application (not sure why). These log output appears to be extracted from `/mnt/var/log/livy/livy-livy-server.out` on the master node. This log file contains session log from all applications so it is not clear how the Livy server is able to separate the application-specific log out.
- The Driver log is the YARN container log for the driver. When click on this URL on Livy UI, it will be redirected to the YARN JobHistory UI showing the container log of the driver.


#### YARN Logs
- Aggregated YARN logs are stored in the location specified by `yarn.nodemanager.remote-app-log-dir` config. Each user submitting applications will have their own dedicated directory. There is no known intuitive tools to analyze these logs besides common CLI tooling and ELK stack. 
- This [article](https://community.cloudera.com/t5/Community-Articles/Deep-dive-into-YARN-Log-Aggregation-Deep-dive-into-managing/ta-p/331399) explains how YARN log aggregation evolved, with key JIRA tickets.
	- Sometimes when an AM fails too fast, little or no logs get aggregated by YARN. Use the yarn.nodemanager.log-container-debug-info.enabled to receive more information around the launch of the container. This will include the launch script and the contents of the working directory. This should point to misconfigurations or common errors like missing jar or wrong environment variables.
- The root logger of Log4j uses ConsoleOutput appender, which displays the log entries in stdout/stderr. YARN automatically redirects this stream into two files (stdout and stderr). So these two files are always created. Removing them from disk can have unexpected consequences due to how Unix OS works. For example, loss of data. 
- Even if the files produced by the application are human-readable, the aggregated log file may contain arbitrary binary parts and could be compressed in a complex way so that end users can not consume it as regular text files. Instead, one should use the YARN CLI to read the logs.


What YARN logs we care about in EMR?
- Logs that are served by YARN jobhistory server.  There is a YARN JobHistoryServer process running on the EMR master node. 
	- The process cli: `mapred    7354  0.1  0.3 9455564 804216 ?      Sl   Feb07   4:20 /etc/alternatives/jre/bin/java -Dproc_historyserver -Djava.net.preferIPv4Stack=true -server -XX:OnOutOfMemoryError=kill -9 %p -Dhttp.proxyHost=whitecastle-proxy-prod-iad-emr.tinyspeck.com -Dhttp.proxyPort=3128 -Dhttps.proxyHost=whitecastle-proxy-prod-iad-emr.tinyspeck.com -Dhttps.proxyPort=3128 -Dhttp.nonProxyHosts=127.0.0.1|*.internal|*.consul|localhost|169.254.169.254|*.slack-sec.com|*.tinyspeck.com|*.emr.tinyspeck.com|ssm.us-east-1.amazonaws.com|172.20.*|172.17.0.1|10.*|*.s3.us-east-1.amazonaws.com|sts.us-east-1.amazonaws.com|ec2.us-east-1.amazonaws.com|*.s3.amazonaws.com -Dmapred.jobsummary.logger=INFO,DRFA -Dyarn.log.dir=/var/log/hadoop-mapreduce -Dyarn.log.file=hadoop-mapred-historyserver-ip-10-61-57-95.log -Dyarn.home.dir=/usr/lib/hadoop-yarn -Dyarn.root.logger=INFO,console -Djava.library.path=:/usr/lib/hadoop-lzo/lib/native:/usr/lib/hadoop/lib/native -Xmx7086m -Dhadoop.log.dir=/var/log/hadoop-mapreduce -Dhadoop.log.file=hadoop-mapred-historyserver-ip-10-61-57-95.log -Dhadoop.home.dir=/usr/lib/hadoop -Dhadoop.id.str=mapred -Dhadoop.root.logger=INFO,DRFA -Dhadoop.policy.file=hadoop-policy.xml -Dhadoop.security.logger=INFO,NullAppender -Dsun.net.inetaddr.ttl=30 org.apache.hadoop.mapreduce.v2.hs.JobHistoryServer`
	- Log file for the JobHistoryServer is stored on the EMR master node at the location `/var/log/hadoop-mapreduce`
- When viewing YARN logs from YARN JobHistoryServer, it appears that sometimes it just act as a proxy, and it will actually pull logs from remote NodeManager nodes. For example, this URL `https://ip-10-61-59-90.emr.tinyspeck.com:19888/jobhistory/logs/ip-10-61-63-221.emr.tinyspeck.com:8041/container_1707441684084_1882_01_000001/container_1707441684084_1882_01_000001/airflow-prod/directory.info/?start=0&start.time=0&end.time=9223372036854775807` seems to imply that the JobHistory Server is proxying a driver container log running on the NodeManager on a different host.
- Note that since EMR 5.x and later, the default value for `yarn.log.aggregation.enable` is set to **true**. Container logs are automatically aggregated to a central location (HDFS or S3) after the application completes. The value can be overwritten in `yarn-site.xml`.
- Looks like with EMR 6.8.0 or earlier, we need to configure `yarn.log.aggregation.s3.bucket` in `yarn-site.xml` if we want to aggregate YARN logs in S3. After EMR 6.9.0, logs automatically archive to S3. We are using EMR 6.11.1. This means that YARN logs are already archived in S3. What is that location?
- The S3 bucket for aggregated logs: `s3://emr-logs-<region>-<account-id>_<cluster-id>`. Logs are organized within the bucket by year, month, and day for easy access.
	- aws s3 ls s3://emr-logs-us-east-1-data-engineering-prod_j-JJK8VMJVUKKN

### 2024-02-06
- Look at EMR Cost from AWS Cost Explorer
	- Only $336k/month? That is much smaller than I thought. Need to figure out what I am missing.
- Look at the cluster rotation cost by looking at last week's rotation and come up with some data.
	- Reverse ordered by instance hours
		- prod-data-platform3-emr6
		- prod-data-platform2-emr6
		- prod-data-platform-emr6
		- prod-etl-emr6
		- prod-dma-emr6
		- prod-dma2-emr6
	- How long it takes for the last rotation to drain workloads?
		- 
		- prod-data-platform-emr6
- Meet Susanna
	- Share insights about the team.
	- Share my strength

### 2024-02-01
- Mahendran Vasagam
	- Beginner insights: gap you noticed that you can contribute. memory profiler you did at Stripe has high value.
	- How do we come up with roadmap? We don't have a product manager. Just staff engineer and manager decide the roadmap. (1) DRI bring up project ideas, in the OKR sandbox. (2) discover roadmap from escal user requests, (3) slack data innovation. 
	- What are you working on? Mahendran is working on Trino. Mostly upgrade version since he joined, but usage has increased a lot, and we want to adopt Trino Gateway. 
	- Recommend following escal-data channel to learn how things are done. Search within this channel can be very helpful, on how things are done, operational.
	- Deepak is the most senior person from DI team, moved to search infra. 

### 2024-01-31
- Spark history logs. Here is a related JIRA: https://jira.tinyspeck.com/browse/DI-5551 : EMR local spark history logs not available across cluster reprovisions
	- [Related slack discussion](https://slack-pde.slack.com/archives/CJFHE7AR3/p1691445331170369?thread_ts=1691443875.627279&cid=CJFHE7AR3)
- Looks like I already have UI access for EMR services. An example [URL](https://emr-prod-etl-emr6.tinyspeck.com/cluster/app/application_1691438150246_0017) The format is: http://{emr-cluster-name}.tinyspeck.com/cluster


### 2024-01-29
- Look at the support channel, get a sense of urgency in operations and KTLO
- Learn about OKR, to build context to meet with people I will work with.

### 2024-01-16
Onboarding Salesforce. 
- Presenter: Madison Rosen, Global Onboarding Team
- 103 attendees in the meeting.
- A Culture grounded on gratitude.
	- Graham Hardt: marking, worked at Oracle. Senior director of global search. 20 years in marketing. Living in DC. Wife and 3 boys.
	- Jean-Francois (JF) Vinet. Montreal Canada. Accounting executive, marketing cloud product. In SaaS for a decade. Enjoy winter sports, hockey, 
	- Meagan, from DocuSign. Also based on Bellevue, WA. Enjoy 
- TODO:
	- Within 72-hour make I-9 verification. Truescreen notification is missing.
	- What is `#help-distribution-onboarding`?
	- Trail Map has the onboarding checklist.
	- 



## 2024-01-11
Self Intro

Hi folks! I'm Yi Chen and I recently joined the data platform team at Slack, working remotely from the Seattle area.

Previously, I spent time at Stripe as part of the Batch Compute Team, where my team built and maintained Hadoop/Spark clusters using EC2 machines. Prior to that, I worked at the Data Warehouse Infrastructure team, which is responsible for Spark, Hive, Trino, Hadoop/HDFS. Beyond Airbnb, I also worked at companies like LinkedIn and Microsoft. 

In my free time, you might find me hiking and camping throughout the Pacific Northwest. I also have a passion for photography and Salsa dancing, and I enjoy integrating these hobbies into my travels. One memorable experience was dancing Salsa in a cabin near Machu Picchu during one of my journeys. 

I'm thrilled to be at Slack, and really looking forward to working together!