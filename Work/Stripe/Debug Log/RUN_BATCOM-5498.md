https://jira.corp.stripe.com/browse/RUN_BATCOM-5498


User reported in https://jira.corp.stripe.com/browse/RUN_BATCOM-5498 that after `spark-submit` is called, there are no log output in airflow for 7 hours. This is a small job that usually finishes very quickly. It appears that the AM was launched but cannot obtain enough resources until 7 hours later to do meaningful work. Right around the time the application was submitted to the queue, the queue reached its peak for both `running_apps` and `pending_apps` metrics. The fact that this application was still stuck for 7 hours suggests that we have a live-lock scenario. Disabling `maxAMShare` feature so that the jobs are not throttled by the number of AMs. Also setting the max number of application to 70 based on the peak value of the past 4 weeks.


- The application that shows a large gap (!7h) after spark-submit call is application_1660666390274_39746. That is, the application is already in RUNNING state for 7 hours.
- This application is accepted by YARN, and AM is launched in time before the large delay.
- the queue is root.encode_event_data.medium
- The application name is events.EncodeEventData.capabilitypolicy_evaluation_execution_events
- [Spark UI](https://hadoop-strawberry-spark-history.corp.stripe.com/history/application_1660666390274_235367)



When the application was submitted, the number of running applications for the queue reached its daily peak (from baseline of 40 to 55) . See https://stripe.signalfx.com/classic/#/temp/chart/Fa2id27AgAM

The application is stuck in the queue for 7 hours. The exact reason is unknown because the app is not in the RM anymore due to retention policy. Based on experience it is most likely a live-lock scenario when there are too many AM launced in this queue and not enough containers avaiable to do meaningful work.

-----


[Airflow Log:application_1660666390274_253504](https://airflow.corp.stripe.com/admin/airflow/log?task_id=events.EncodeEventData.capabilitypolicy_evaluation_execution_events&dag_id=hourlycron&execution_date=2022-08-25T10%3A00%3A00%2B00%3A00&format=json)
- 
- but ACCEPT->RUNNING in less than 3 minutes.


- https://hadoop-strawberry-resourcemanager.corp.stripe.com/cluster/app/application_1660666390274_253504
	- Application is added to the scheduler and is not yet activated.  (Resource request: <memory:27136, vCores:4> "exceeds maximum AM resource allowed").
	- Started: Thu Aug 25 10:09:56 +0000 2022
	- Launched:Thu Aug 25 10:11:57 +0000 2022
	- Finished:Thu Aug 25 19:37:17 +0000 2022
	- Elapsed:9hrs, 27mins, 21sec
	- Total number of Non-AM Containers preempted:32
	- Number of Non-AM Containers Preempted from current attempt: 32
	- Total Resource Preempted: <memory:2002944, vCores:320>
	- [Spark UI](https://hadoop-strawberry-spark-history.corp.stripe.com/history/application_1660666390274_253504/1/executors/)


https://hadoop-strawberry-resourcemanager.corp.stripe.com/cluster/app/application_1660666390274_255034
	- Application is added to the scheduler and is not yet activated.  (Resource request: <memory:27136, vCores:4> exceeds maximum AM resource allowed).
	- Total number of Non-AM Containers Preempted: 43
	- Number of Non-AM Containers Preempted from Current Attempt: 43
	- Total Resource Preempted: <memory:2691456, vCores:430>




https://hadoop-strawberry-resourcemanager.northwest.corp.stripe.com/proxy/application_1660666390274_266714/executors/
- This task is still running. Live Spark UI: https://hadoop-strawberry-resourcemanager.northwest.corp.stripe.com/proxy/application_1660666390274_266714/executors/
- As of now (2:17pm), it has 4 executors as it said it would want, but 1 of them is already dead.
	- The ratio of GC time is pretty high: per executor metrics:[26/4.5, 22/6.7, 48/5.1, 35/13]
	- The dead executor #2 was removed because it has been idle for 60 seconds: `22/08/25 20:24:18 {} INFO org.apache.spark.ExecutorAllocationManager: Removing executor 2 because it has been idle for 60 seconds (new desired total will be 3)`
	- Looks like ExecutorAllocationManager has requested to remove the remaining exuectors since `22/08/25 20:36:37`, which is the last log in Driver, which is 48 minutes ago. Why the Spark UI still shows the executors active?
	- `22/08/25 20:23:01 {executorId=2, partitionId=93, taskAttemptId=93} INFO org.apache.spark.executor.Executor: Finished task 93.0 in stage 0.0 (TID 93). 1822 bytes result sent to driver` Why the taskAttemptId=93 is so high?

-----

This is being further tracked by RUN_DATAINGEST