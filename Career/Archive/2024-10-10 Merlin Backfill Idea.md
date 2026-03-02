# **Merlin Backfill Idea**

Status: *Under review*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Oct 10, 2024  Last Updated: Oct 14, 2024

# Intuition

During the discussion around the Merlin backfill reliability risks (see [doc](https://docs.google.com/document/d/121mbhx08qjmLgo-rbYIXqroUAeyRhugwJnRHYUb4sjM/edit?tab=t.0)), it occurred to me that the main reason the merlin backfill design was to satisfy a few requirements: (1) it can auto-healing, and (2) the user experience is still reasonable with Airflow. 

My intuition is that Merlin, as a sophisticated framework, may have a solution that preserves much of its existing logic while addressing reliability, scalability, and future auto-tuning projects. Based on Merlin's ability to handle daily runs and submit jobs to different clusters (like backfill-emr6), I propose a high-level approach:

Instead of creating a single Spark job and feeding it multiple batches of data, we could generate a batch of parallel Merlin jobs, each handling a daily input. To simplify the relationship between the daily Merlin job and the backfill job, we might consider removing the batch data feeding logic and instead simply "forking" the Merlin job with a specified daily time range for each forked job.

# High Level Proposal

The fundamental idea of this proposal is based on Linux's `fork()` system call. In Linux, the `fork()` system call creates a new process that is an exact copy of the original process. This new process is called a child process, while the original process is called the parent process.

My understanding of Merlin is that it employs an auto-healing mechanism. Each daily run checks for the need for a backfill. If required, a new Spark job is initiated in the backfill cluster, and batches of data are continuously fed into this dedicated job. Merlin's job configuration includes a time-to-kill setting, enabling it to control the backfill application

To preserve the self-healing capability, we can retain the existing logic in the daily runs. Let's refer to these standard daily run Merlin jobs as "root jobs," which consistently execute in the normal cluster (e.g., prod-dma-emr6). They will be orchestrated by Airflow. When a backfill is detected, instead of launching a separate Spark job, I propose that the root job "fork" itself into the backfill cluster, creating one "fork" per day. We'll call these forked backfill jobs "child jobs."

Within each forked child job, we should disable the backfill detection logic to prevent a recursive backfill loop. To track the backfill state across multiple root jobs, we might need to introduce a new table (either in Iceberg or MySQL).

As an example, let’s assume a cluster issue that resulted in a delay of 7 days. After the issue is fixed, we want to quickly backfill 7 days of data. The new backfill framework works this way:

1. Airflow will clear and restart 7 merlin jobs (root jobs) in its normal cluster (e.g. prod-dma-emr6).  
2. The initial Merlin root job, triggered by Airflow, will identify all seven days requiring backfilling. This information will be stored in a table (e.g., MySQL). Given the default batch size of 14, which exceeds the number of days to be backfilled, this root job will fork itself, resulting in seven daily Merlin jobs within the backfill cluster. These child Merlin jobs will not re-evaluate the need for backfilling. Since the root job will adjust the date range input for each child job to encompass a single day of data, their performance and reliability should align with regular daily runs.  
3. If the backfill date range surpasses the configured batch size, the root Merlin job will monitor the status of current live jobs. As child jobs complete, it will initiate new ones to ensure continuous backfilling.  
4. The remaining six Merlin root jobs, cleared by Airflow but initiated later, will recognize that a backfill has already started (e.g., by querying the MySQL or Iceberg table). These jobs will not need to take any action. Instead, they will retrieve the current status from the state store (MySQL or Iceberg) and log the Spark application ID, aiding in debugging if the job fails within the backfill-emr6 cluster. This root job will remain blocked until the corresponding daily backfill is completed. At that time, the root job will return with the same exit status of the backfill child job. If the child job for a particular ds failed, this root job will also fail. This allows the next round of Airflow retry to pick it up again.  
5. The other 6 merlin root jobs cleared by Airflow but started later, will be able to detect that a backfill has already started (e.g. by querying the MySQL table or Iceberg table). They don’t need to do anything, just fetch the current status from the state store (MySQL or Iceberg), print out the Spark application\_id in its log, which helps debugging if the job failed in the backfill-emr6 cluster. This root job continues to block until the corresponding daily backfill finishes. 

The benefit of this approach, if it is workable, include:

* The backfill child jobs are the same jobs with the normal daily run, so it will be as reliable as performance with their daily run. Tuning the daily run jobs will reflect automatically to the backfill for both performance and reliability. This solves the problem today that when we tune the daily job, it will impact the backfill, and when we tune backfill, it will impact daily jobs.  
* In the future when we can auto-tune Spark jobs per task, we can also auto-tune those backfill child jobs that have the same profile with their normal daily runs.  
* We will have significant scalability improvements. We can still let users or the infrastructure determine how many daily child jobs to run in parallel. This takes away all the necessary complexity inside Merlin backfill today for tuning the performance. 

