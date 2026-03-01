

## Summary

The goal of this doc is to propose a solution and a roadmap that helps users to debug Spark jobs. This is a [long running challenge for the team](https://paper.dropbox.com/doc/Spark-Developer-Productivity--BnevCjCcdKBWgxGqZf7TxkjtAg-aclIHsnyq3TRDsMevj0fT). It is also a common challenge among big data infrastructure teams in the industry. For example, Apple, LinkedIn, etc 
- [2020: Tackling Scaling Challenges of Apache Spark at LinkedIn](https://www.databricks.com/session_na20/tackling-scaling-challenges-of-apache-spark-at-linkedin)
- [2022: Auto-diagnosis and remediation in netflix data platform](https://netflixtechblog.com/auto-diagnosis-and-remediation-in-netflix-data-platform-5bcc52d853d1)

The following is a few concrete examples of user requests that we want to eliminate (that is, build tools to help users to solve this problem themselves.)

-   [https://jira.corp.stripe.com/browse/RUN_BATCOM-41](https://jira.corp.stripe.com/browse/RUN_BATCOM-41)
	- A task with no issue for 6 months start to fail with direct memory issue.
	- The owner tried a few permutations of configuration changes and documented them.
	- Somebody recommended the fix was to change spark.reducer.maxBlocksInFlightPerAddress = 10
	
-   [https://jira.corp.stripe.com/browse/RUN_DATALIB-2714](https://jira.corp.stripe.com/browse/RUN_DATALIB-2714)
	- FetchFailedException.
	- xton suggested rerun the job, and it worked.

What to avoid?
- fragmentation of toolings: we don't want to provide multiple UIs that our users need to start from. All user questions should be able to start from the same entry point, ideally directly linked to the Airflow job UI (ask DO team for support)


## Related

- [go/spark-observability](http://go/spark-observability)
- [go/data-catalog](http://go/data-catalog) : Stripe's adoption of DataHub
	- Timeliness - Users can see how a dataset's landing times match up to its SLAs historically
	- Lineage - Users can explore lineage of datasets produced as part of scheduled Airflow tasks.
- [Yahoo sherlock](https://github.com/yahoo/sherlock) can detect anomaly for scheduled batch jobs (hourly, daily, weekly, monthly)
- [Auto Spark Perf Tuning](https://youtu.be/ph_2xwVjCGs)
- 


## Roadmap
### MVP
- ability to quickly find everything we already have regarding an spark application.
	- the queue name, capacity, and usage at the time of the app running.
	- the app's config.
	- 
- ability to grep logs and quickly surface the exception stack.

### V1
- Ability to detect recent code changes from git or related event logs for a pipeline, and the infra code change (config change or patching)
- For an app, we can quickly ansswer the question if there is any recent code change on the infra side and the user app side.
- For an app, we can automatically show the history run of the same app in a chart. Stretch goal is to detect and alert anomaly (e.g. the app is suddenly running slower)

## Long-Term Roadmap
- SLA tracking: Able to track SLA (anticipated landing time), so engineers can decide if they need to intervene
- Able to automatically understand common infra failure scenarios and act accordingly.
- Auto Perf Tuning (see)


### How much toil we can reduce with this tool?
In 2022 H1, the main toils for the team is capacity management, incidents, debugging critical infra issues, and patching hadoop and spark.

### Scoping Questions
- Should we provide data pipeline SLO monitoring? For example, if an upstream data pipeline is delayed, we could notify the downstream in case human intervention is needed


### What data can we collect?
- Can we collect github code changes so we know if there are any recent code change for a data pipeline?
- Can we collect Spark event logs 
- Can we stream container logs somewhere and analyze them in real-time? Or should we start an offline analysis after the job is finished if the log is stored somewhere?
- 

## Tasks

- [ ] How about we just extend data-job-srv instead of building a new service?
	- [ ] Can DJS figure out the application name and DAG information?
	- [ ] data-job-srv is on the critical path, the observability is not.
- [ ] We need an app search feature. How to ingest? 
	- [ ] For application record, we can use RM real-time change events.
	- [ ] For DAG-to-app mapping, do we have that somewhere in real-time? 
- [ ] Can I use MySQL?
	- looks like data-job-srv is a Golang service running on PostgreSQL
- [ ] Hadoop cluster discovery: how to know what clusters are added more more removed? Maybe we can just parse the URL to extract the cluster information?
- [ ] How to surface infra-level issues to the service so they user don't have to request further help from infra team?

- [ ] With an app page:
	- [ ] Link to SHS page



