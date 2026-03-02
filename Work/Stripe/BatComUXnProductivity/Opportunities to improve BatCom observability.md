### Principles
- Avoid fragmented UI/UX. Use one UI.
- Push instead of pull: user only need to see what's relavent to their task at hand.
- goldilocks principle: clear about the goals and non-goals
- prescriptive
- future proof (EMR-S, Spark on K8s)


### Opportunities

- Are we using Parquet compression with sorting (sort records with increasing cardinality to get better compression)
- link important data for each job to improve self-service
	- link data pipeline (or tasks) directly to the cost. looks like users need to jump through hoops to calculate it themselves.
	- link job SLA and expected landing time (and estimated landing time/actual landing time) based on upstream landing time. Alert if necessory.
	- link historical run duration, and show percentile of this current run, to detect slowness anomaly.
	- link some magic explaination (how smaller executor calculator changes/override user's executor config)
	- provide a canonical link to this job page when the user ask a question in Slack.
	- provide preemption stats.
- create concept of paved path for debugging batch compute
- create a tool to compare two runs to detect the differences.
	- discover all code changes between these two runs
	- discover the job config changes.
	- discover the difference in the number of tasks, partitions, executors, preemptions.
- create the standards of detecting infra issues and user issues. [This is a crude proxy](https://hubble.corp.stripe.com/viz/dashboards/21034--data-platform-ops-review?subTab=Charter+Metrics&tab=Batch+Compute) today for Hadoop reliablity.
- anomaly detection, measuring outliers using standard deviation (sigmas)
	- application clock time
	- number of tasks, stages, jobs, failures from historical runs.
- create the process of detecting infra issues and user issues
- create a detector for data freshness/staleness.
- create a dtector for data volume deviation.
- create an alerting framework.
	- alert downstream for possible human intervension if upstream is failing/slowing.
	- alert recent code change.
	- alert recent infra change.
	- alert schema change
	- detect and alert wide-spread infra issues
	- detect large data skew ([example](https://jira.corp.stripe.com/browse/RUN_BATCOM-5499))
	- detect and suggest modifications ([example](https://jira.corp.stripe.com/browse/RUN_BATCOM-5487))
- create a SLO real-time monitor, and alert downstream SLO miss when upstream is slow.
- Improve spark-profiler speed with Druid
