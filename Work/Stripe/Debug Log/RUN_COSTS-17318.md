JIRA: https://jira.corp.stripe.com/browse/RUN_COSTS-17318


Incident: [knee-dialect](https://incident-reporting.corp.stripe.com/wf/incidents/knee-dialect?tab=remediations)
- created on August 19.
- Job Failed due to the following error:
- `spark-submit log: Caused by: org.apache.spark.SparkException: Job aborted due to stage failure: Task 618 in stage 39.3 failed 4 times, most recent failure: Lost task 618.3 in stage 39.3 (TID 2035264,` `[hadoopdatanodeicp--0fd2922263943b2b5.northwest.stripe.io](http://hadoopdatanodeicp--0fd2922263943b2b5.northwest.stripe.io/)``, executor 64136): ExecutorLostFailure (executor 64136 exited caused by one of the running tasks) Reason: Executor heartbeat timed out after 130665 ms
- First error was `Application application_1660666385723_13773 failed 1 times (global limit =2; local limit is =1) due to ApplicationMaster for attempt appattempt_1660666385723_13773_000001 timed out. Failing the application.`
- `ERROR org.apache.spark.network.client.TransportClient: Failed to send RPC RPC 6924391594653431619 to /10.68.101.82:37738: java.nio.channels.ClosedChannelException java.nio.channels.ClosedChannelException`
- Gaurav: this app is insane. 65k executors, maybe too much metadata stored on the driver, millions of tasks, and 20k partitions. Current driver memory is 24g
- viveky: this is still a concern https://jira.corp.stripe.com/browse/BATCOM-1793
	- Gaurav asked Josh to prioritize this for timeline workstream.
	- After resolution, Viveky still think this is the root cause
- Executor sized up to 100G to see if it fixes the issue.
- jmhertlein found signalfx showing memory bottlenecked.
- jmhertlein asked viveky to turn on GC logging for the driver with an example PR.
- Incident resolution.
	- increased driver memory
	-  spark.locality.wait=0s, looks like it is helpful.




