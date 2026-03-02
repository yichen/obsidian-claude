# **FY25H2 Spark Reliability and Cost Plan**

Status: *Under review*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Aug 22, 2024  Last Updated: Sep 17, 2024

[Context](#context)

[Q3 Plan](#q3-plan)

[Q4 Plan](#q4-plan)

[Project Details](#project-details)

[T-shirt sizing of Spark jobs](#t-shirt-sizing-of-spark-jobs)

[Problem](#problem)

[Ideas](#ideas)

[Improve reliability and SLA risk in shared clusters by using queues](#improve-reliability-and-sla-risk-in-shared-clusters-by-using-queues)

[Problem](#problem-1)

[Risk](#risk)

[Continue to tune EMR clusters](#continue-to-tune-emr-clusters)

[Remove unmaintained jobs](#remove-unmaintained-jobs)

[Identify jobs with large risk and ask the owner to fix them](#identify-jobs-with-large-risk-and-ask-the-owner-to-fix-them)

[Tune spark.sql.shuffle.partitions default](#tune-spark.sql.shuffle.partitions-default)

[Backfill cluster reliability and cost](#backfill-cluster-reliability-and-cost)

[Detect and Discover, and tune jobs with large data skew](#detect-and-discover,-and-tune-jobs-with-large-data-skew)

[Detect and Fix unhealthy, unreliable jobs](#detect-and-fix-unhealthy,-unreliable-jobs)

[F.A.Q](#f.a.q)

# Context {#context}

In FY25H1, we have [saved $6.21 million annual EMR costs for 12 tracked EMR clusters](https://slack-pde.slack.com/archives/C8F0SQNSH/p1722537988236069), while [improving EMR reliability by 65%](https://slack-pde.slack.com/archives/C06G45LGG7M/p1723138414787169) (more than 70% for critical clusters) at the same time. Most of these improvements are achieved through [engineering efforts that can be scoped within the Data Infra team](#heading=h.ut8aiosgud2u).

From FY25Q3, we will start to engage other teams to pursue more cost reduction and reliability improvements. We will also list a few upcoming projects in Q4 that need collaboration from other teams. The goal of this document is to share the plan and align with other teams, including other teams in DE, and also end-user teams who own the data pipelines.

# Q3 Plan {#q3-plan}

| Priority | Project | KR | Impact | Team Affiliation | DRI/Contributors | Ideas/Links/Docs/RFCs | Effort Estimate |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| high | First step to use YARN queues for reliability and on-time | There is a plan (RFC) to adopt queues in Spark clusters, communicated to stakeholders. **Stretch**: there is an initial reference implementation for data-platform | ReliabilityOn-Time | DIDIGMPG | [Yi Chen](mailto:chen.y@salesforce.com) | [Problem](#problem-1)[Risk](#risk) | 6 weeks |
| high | Improve coarse resource sizing (t-shirt sizing) in DMA cluster | There is a short-term plan, implementation, and process to stop the bleeding | CostReliabilityOn-Time | MPG TBD | TBD | [Problem](#problem)[Ideas](#ideas) | 4 weeks |
| high | Identify and Remove **unmaintained** jobs in prod clusters | There is a dashboard identifying jobs with high failure rate (airflow retries) There is a process to ensure ensure those jobs are either fixed or deprecated | CostReliabilityOn-Time | TBD | [Gage Gaskins](mailto:ggaskins@salesforce.com) | [Problem Statement](#remove-unmaintained-jobs) [Unmaintained based on max tries](https://analytics.tinyspeck.com/v2/explore/1000000001459878) | 1 week |
| high | Apache Celeborn | Celeborn is deployed to k8s and handles shuffle for one cluster. | CostReliability | DI | [Rahul Gidwani](mailto:rgidwani@salesforce.com) | [Spark Shuffle Reliability](https://docs.google.com/document/d/1xkddnyMmSJOyVHAAv8oMUll4Bw3KJo1TxCWDEnil3KU/edit) | TBD |
| medium | Backfill cluster cost and reliability | Backfill jobs process the same amount of those corresponding normal-run jobs | CostReliability | MPG? | TBD | [Problem Statement](#backfill-cluster-reliability-and-cost) | TBD |
| medium | Tune spark.sql.shuffle.partition | A new default value is implemented  | CostReliability | DI | [Yi Chen](mailto:chen.y@salesforce.com) | [Problem Statement](#tune-spark.sql.shuffle.partitions-default) | 1 week |
| medium | Identify and fix jobs with large waste (automate what’s done in Q2) | There is a dashboard to identify jobs with large waste Identify the direct or indirect owners to ensure these jobs are fixed  | CostReliability | MPG | [Nilanjana Mukherjee](mailto:nilanjana.mukherjee@salesforce.com) | [Problem Statement](#identify-jobs-with-large-risk-and-ask-the-owner-to-fix-them)  | 2-4 weeks |
| low | Continuous cluster-level tuning | Investigate cluster-level/global configurations and look for new savings opportunities | CostReliability | DI | [Yi Chen](mailto:chen.y@salesforce.com) |  | TBD |

# Q4 Plan {#q4-plan}

After Q3, we will rollover unfinished projects into Q4. The following is a list of projects that we are looking into besides potential rollover

| Priority | Project | Team Affiliation | Impacts | Notes and Next Steps | Effort Estimate |
| :---- | :---- | :---- | :---- | :---- | :---- |
| See table above | Continue on whatever we can’t finish in Q3 | NA |  | NA |  |
| high | Merging team-specific clusters into data-platform cluster in queues | DIDIGMPG EMR Cluster Owners | Cost | Planning with \#de-planning | 8 weeks |
| medium | Detect jobs with large data skew that’s a cost and reliability risk, provide a document/process/training to fix those skew | EMR Cluster Owners | CostReliability | Nila has training planned for dealing with skews. | 2 weeks |
| medium | Vcore over-subscription | DI | Cost | A data-platform cluster is the best candidate with the most potential for cost savings. The next step is to find out how to implement EMR.[WIP doc](https://docs.google.com/document/d/1sW4_5Ob3aNd3zs15yiZVtpQ4dy_kcydnZgs8hlBCTc0/edit) | 3 weeks |

# Project Details {#project-details}

## T-shirt sizing of Spark jobs {#t-shirt-sizing-of-spark-jobs}

### *Problem* {#problem}

So far, we were able to achieve almost 80% total savings for data-platform-emr6 clusters. We have a lot less savings from the dma-emr6 cluster, mostly because the jobs on DMA are much more difficult to tune. The reason is that there is no clear owner definition on who should be responsible for tuning these jobs. There are (TODO: confirm) merlin and Sqlpen jobs running, which comes with some t-shirt sizing configurations. The end users are data scientists or data engineers who only have knowledge of SQL and don’t have the skill to tune their jobs. The frameworks (TODO: confirm) provide t-shirt sizing for spark jobs but those sizing made large but often unreasonable assumptions. As a result, it creates both cost and reliability risk in the short term.

This is a very challenging problem to fix, but we need to find a path forward by working together with the MF team.

[See recent example](https://slack-github.com/slack/data-airflow/pull/55255)

\[Add more analysis of recent examples here\] 

### *Ideas* {#ideas}

* Tune every job that is currently marked for sizing of LARGE and EXTRA\_LARGE. After tuning, remove LARGE and EXTRA\_LARGE from the code base, so that nobody will use that notion again.  
* Come up with a doc describing how to do, how to size the executors and drivers so that the metrics team can tune the driver and executor memory.  
* Come up with a PR code review process, so that the jobs are not blindly over-sized.  
* Provide training for the Experiment team about how to size the driver and executor resources.

## Improve reliability and SLA risk in shared clusters by using queues {#improve-reliability-and-sla-risk-in-shared-clusters-by-using-queues}

### *Problem* {#problem-1}

There are many jobs not belonging to DIG that are running in the critical data-platform-emr6 cluster. If these jobs run rogue, it can affect the reliability and SLA of important jobs in the data-platform-emr6.

This risk can also show up in a different form. For example, \[FIND THE INCIDENT LINK here\], during an incident, some DMA workload were moved to the data-platform-emr6, and because data-platform-emr6 cluster is tuned for its stable workload, the additional DMA workload took down the data-platform-emr6 cluster. 

The high level approach is to use YARN queues that provide better resource guarantees, so a rogue job will not affect critical jobs. The downside is that this may increase cost so we need to do it carefully, ensuring that the cost increase is manageable, or ideally, balance the cost increase with other trade-offs (e.g. preemption for low priority jobs). 

### *Risk* {#risk}

- This can potentially increase cost. We will look into CapacityScheduler, which may reserve a minimum capacity for a queue that is over-provisioned, which can use underutilized resources.  
- We may be blocked for the fact that we have too many different EMR versions (EMR 6.11, 6.12, 6.15), making it difficult to migrate workloads to a cluster with a different EMR version.  
- We may be blocked for the S3 permissions and other security related issues that are currently set at per-cluster level.

## Continue to tune EMR clusters {#continue-to-tune-emr-clusters}

This project involves identifying new cluster-level opportunities to improve reliability and cost. This is a “continuous” project, mainly for visibility and tracking purposes. We will continue to discover new opportunities that are low effort and low return, but the result can add up. 

## Remove unmaintained jobs {#remove-unmaintained-jobs}

There are unmaintained jobs running in our infrastructure. This is [an example of a job that has been failing since 2023](https://slack-pde.slack.com/archives/C8EDM9MGA/p1722447467365739?thread_ts=1721694619.467879&cid=C8EDM9MGA). Now that we have the YARN metrics, we can identify them and ask the owner to remove them.

We should be able to identify these jobs by using YARN metrics, identifying the jobs that have the most number of retries per day. For example, if it is a daily job, we should see one YARN app per day. 

## Identify jobs with large risk and ask the owner to fix them {#identify-jobs-with-large-risk-and-ask-the-owner-to-fix-them}

Since Q2, I have been doing this manually. Now that we have YARN and Spark metrics, we will work on a system and process to identify these high-risk jobs automatically, provide documentation and training to help them tune these jobs.

## Tune spark.sql.shuffle.partitions default {#tune-spark.sql.shuffle.partitions-default}

We currently don’t have a default value for this configuration, so most likely the majority of our jobs are running with the default value of 200 shuffle partitions. This configuration has a large impact on the job’s reliability and performance. 

The first step of this project is to opportunity-size this effort, to answer the following questions:

- How many jobs are running with the default 200 value?  
- What’s the average task duration for the longest running stage?   
- Do they also have large skew because of this low default number?

After we answer the above questions, it will allow us to decide if we need to set a new cluster-level default. We will need to answer this question:

- What is the new default value?  
- What’s the process to determine this value and how is the result?

The third step is to confirm the impact:

- How did the new default impact the reliability of jobs?   
- How did the new default impact the timeliness of jobs? Do they run faster or slower?

## Backfill cluster reliability and cost {#backfill-cluster-reliability-and-cost}

There is a known risk of cost and reliability for backfill jobs because some backfill frameworks are feeding multiple days worth of data to jobs that are developed for handling one-day worth of data (assuming it is daily jobs). For example, if a normal-run daily job is tuned to handle one-day worth of input data, but the same job processes multiple days worth of data, it will most likely become unreliable. The symptoms we have seen so far include a large number of stage-level retries, which easily doubles or triples the cost of running these jobs. We’ve also seen backfill jobs failing in the backfill cluster but healthy in their normal-run clusters. 

One possible solution is to remove the optimization of loading multiple days worth of data during backfill. That is, the backfill framework should ensure each Spark job handles the same data with its normal-run jobs. This way, an improvement in performance and reliability of these jobs will automatically translate to improved performance and reliability of backfill .

## Detect and Discover, and tune jobs with large data skew {#detect-and-discover,-and-tune-jobs-with-large-data-skew}

With YARN and Spark metrics, we can identify the jobs with large data skew. There are usually significant opportunities to reduce cost by addressing them. The challenge is that it is difficult to tune some jobs. So the initial goal is to go through this exercise to opportunity-size what we can achieve in the short-term, and decide what’s the path forward for the long term. 

## 

## Detect and Fix unhealthy, unreliable jobs {#detect-and-fix-unhealthy,-unreliable-jobs}

With YARN and Spark metrics, detect jobs that are not reliable, identify the owners and either fix them, deprecate them, or move them to a lower-tier cluster. For example, we can find all jobs that are being retried multiple times within their daily runs by Airflow, all jobs with a large number of stage-level retries. 

# F.A.Q {#f.a.q}

