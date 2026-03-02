
#slack/spark

Spark job tuning with JVM Profiler
- Pain Points
	- We don't have observability on resource consumption characteristics for Spark jobs, so tuning Spark applications is mostly guess-work.
- Solution:
	- Adopt JVM Profiler from Uber.
	- Estimate: 2 months
- Risks
	- The engineering effort to adopt JMV Profiler on EMR as there may be limited control on the infrastructure.
		- Mitigation:
			- Do a proof-of-concept in a test cluster.
	- Lack of infrastructure support to make the data easily useful for users. For example, do we ingest the data into Iceberg and use ATS to visualize the data from Trino? Do we ingest the data into Pinot and use what tool to visualize it?

Spark Application Metrics in Data Warehouse
- Pain Points
	- Users only have unreliable access to the currently running Spark applications metrics (those data that get shown in Spark UI, generated from Spark event logs).
	- The unreliable here means that those data are not accessible after the cluster is rotated.
	- Without the historical Spark metrics, it is difficult to debug performance and resource characterists of particular Spark applications, their change over time. This makes debugging incidents difficult. 
	- Without the historical Spark metrics, it is difficult to do any reliable performance tuning.
- Solution
	- Persist Spark metrics (from event log) in the data warehouse (Iceberg and Trino).

Global Spark application UI
- Pain Points
	- The Spark developer experience starts with Airflow UI, discovering Spark UI URL, YARN app URL, and Spark logs from Airflow logs.
	- Logs get lost frequently from two major infrastructure issues: (1) lost spot instances, and (2) EMR clusters are frequently rotated.
- Solution
	- Create a global service to unify the access to Spark UI and Spark logs. This service provide a search interface, to allow users to find their application using DAG id, task ID, try_number. Because these information are available from Airflow, we can provide a canonical URL that can be linked directly from Airflow UI, so that users can just click the button to find the application.
	- After finding (discovering) the Spark application, this service will show links to Spark UI for the application, and related Livy logs and YARN logs.
- Risks
	- There is no clear solution to how to show aggregated YARN logs assuming the NodeManager are gone because of the spot instances are gone.
		- Mitigation: considering the size of YARN logs may be too big to analyze using ELK stack, consider the following options:
			- Provide a link and instruction to allow the users to download the aggregated log to their laptop to analyze.
			- Long term: build a Spark service to automatically analyze the logs, extract important error and stack trace and help point the users to the right direction.