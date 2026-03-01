# **Spark-on-Kubernetes Execution Plan for Jul 31, 2025**

Status: *Approved*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Jun 5, 2025  Last Updated: Jun 16, 2025

# Summary

The next executive review meeting for the Spark on Kubernetes initiative is scheduled for **July 31, 2025**. The DI team is also under growing external pressure ([example](https://slack-pde.slack.com/archives/CJFHE7AR3/p1749157262950529?thread_ts=1719603876.400149&cid=CJFHE7AR3)1, [example2](https://slack-pde.slack.com/archives/CJFHE7AR3/p1745533019238649?thread_ts=1699048360.478229&cid=CJFHE7AR3))  to provide a clear strategic direction for our Spark platform. Two main takeaways from the May 22 review were:

1. We need **reliable**, **evidence-based data** to build confidence that Spark-on-Kubernetes is the right long-term path for Slack.  
2. We must provide **clarity to our users around migration planning**—particularly to avoid forcing teams to migrate twice within a short time window.

Spark-on-Kubernetes remains a relatively new and sparsely adopted technology within the industry[\[1\]](#bookmark=id.72fyvd3v47qr). This reality makes the decision highly consequential-not only for the Data Infrastructure (DI) team, but for Slack’s broader data strategy. Given the level of uncertainty and potential impact, we must make some very **focused** near-term decisions to provide clarity to our users.

We believe this decision must be approached on two levels:

1. **Strategic Direction**: can we confidently determine whether Spark-on-Kubernetes should be part of Slack’s long-term platform strategy by Jul 31, 2025?  
2. **Near-term Execution**: if the answer is yes for the first question, how should we proceed — especially in light of the upcoming EMR 6 end-of-life in July 2026 and the engineering resource trade-offs involved.

Answering the first question sets our long-term directions: either commit to Spark-on-Kubernetes or continue investing in EMR in the next 2 years. The second question helps identify the engineering, migration, and support gaps we’ll need to address—and prioritize—if we choose to move forward with Kubernetes.

The **Methodology** section outlines a decision-making framework and the potential options we may consider by the July 31st deadline. The **Plan** section highlights the short-term questions we need to answer to de-risk the project and make forward progress. Known issues and concerns are addressed in the **Risks** section.

# Methodology

By July 31, we aim to align on one of the following directional decisions:

* **Option 1: Proceed with Spark on Kubernetes.** Our implementation is deemed production-ready, and user migration will begin. We will not proceed with migration to EMR 7\.  
* **Option 2: Spark on Kubernetes is the future soon, but not yet ready.** While Spark-on-Kubernetes is our intended long-term platform, the current implementation lacks production readiness, or we require more data to build confidence. Migration will be split: some users will move to Spark-on-Kubernetes, others to EMR 7 to meet near-term needs.   
* **Option 3: Defer Spark on Kubernetes.** Due to current technical maturity or implementation gaps, we pause the initiative and move forward with EMR 7\. This is not a permanent rejection—technology continues to evolve. A likely re-evaluation point will come within two years, aligned with EMR’s next lifecycle milestone and industry developments, such as Airbnb’s Kubernetes migration and maturing open-source tooling. 

While there is strong internal enthusiasm for exploring new technologies, the core challenge is that Spark-on-Kubernetes remains relatively immature and has limited real-world adoption among companies with serious Spark workloads. We must approach this decision with discipline. Without broader adoption or operational data, we risk overcommitting to a path based on idealized assumptions.

To de-risk the initiative and support a confident decision by July, we will focus on two key areas:

1. **Targeted Benchmarking**. We will migrate a full EMR cluster to Kubernetes and evaluate performance against clear success criteria. The primary goal is to validate the cost-saving hypothesis—a 50% improvement driven by the elimination of 25% EMR fees, and performance gains from newer technology such as Apache Comet (which is not currently implemented on EMR).  Given that cost has become the central justification for this migration, objective benchmarks are essential.   
2. **Knowledge Expansion & Stakeholder Engagement**. We will deepen our internal understanding of Spark-on-Kubernetes and connect with peer companies (e.g. Pinterest, Airbnb) to learn from their experience. We’ll engage key internal stakeholders to ensure they gain a realistic understanding of what Spark-on-Kubernetes entails—beyond high-level promises. This is critical to bridge the current knowledge gap, which has limited the team’s ability to anticipate real-world operational challenges. 

# Execution Plan

By July 31, our focus will be on completing the targeted benchmarking to provide clear evidence that Spark-on-Kubernetes can serve as our long-term platform. In parallel, we will identify all remaining blocking gaps needed for production readiness. The outcome will help determine whether we can move forward without migrating to EMR 7, or if a parallel migration to both EMR 7 and Spark-on-Kubernetes is necessary while those gaps are being addressed.

| task | DRI | Impact of Not Doing | Effort in weeks |
| :---- | :---- | :---- | :---- |
| Stabilize DMA and Percolator clusters for cost comparison before migration | [Yi Chen](mailto:chen.y@salesforce.com) | Unreliable cost comparison | 1 |
| Migrate the entire Percolator cluster workload to Kubernetes ([context](https://slack-pde.slack.com/archives/CJFHE7AR3/p1749482786801989)) | [Jigar Bhalodia](mailto:jbhalodia@salesforce.com) | Unreliable cost comparison | 4 |
| Identify potential migration path (EMR 7 vs. Spark-on-Kubernetes), including a potential transparent/seamless migration path to remove the need for 2 migrations  ([context](https://slack-pde.slack.com/archives/C056FV1CE9X/p1748624741792229?thread_ts=1748541642.563909&cid=C056FV1CE9X)) | [Yi Chen](mailto:chen.y@salesforce.com) | Users will be forced to migrate twice within a short period of time | TBD |
| Identify engineering tasks that need to happen before Spark-on-Kubernetes is production ready | Jigar / Gage | Immature migration, large operational burden for both DI and users | TBD |
| Reach out to Airbnb for a knowledge sharing meeting | [Yi Chen](mailto:chen.y@salesforce.com) | Limited visibility into the risks may lead to overly optimistic assumptions and impact the quality of decision-making. |  |
| Reach out to Pinterest for a knowledge sharing meeting | [Yi Chen](mailto:chen.y@salesforce.com) | Limited visibility into the risks may lead to overly optimistic assumptions and impact the quality of decision-making. |  |
| \[TODO\] Add any other blocking issues here | Person |  |  |

The following table outlines the key tasks required before we can consider our Spark-on-Kubernetes implementation production-ready—meaning the Data Infrastructure team can confidently support it. Completing these tasks will bring us to feature parity with current operational needs. While they don’t need to be finished by July 31, we do need to align on critical dependencies and establish a confident delivery timeline. That timeline will guide how we prioritize and allocate resources, especially in light of the upcoming EMR 6 end-of-life in July 2026..

# GA Readiness Plan

| task | DRI | Required for GA | Impact ofNot Doing | Effort in weeks(1,2,3,5, 8\)  | Stakeholders |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Feature parity for log debugging experience ([context](https://slack-pde.slack.com/archives/CJFHE7AR3/p1749227179084199)): Driver and executor logs persistence in S3 ([context](https://docs.google.com/document/d/1yYBL3k-_ElL56G0gCnBRek15BAdGlF446k6iprsETHU/edit?disco=AAABlzZvh30)) | TBD | Yes | Significant loss of productivity in debugging and root-causing Spark issues |  |  |
| Feature parity for YARN metrics (End-to-end Spark application metrics) ([context](https://slack-pde.slack.com/archives/G01BC76P1HD/p1749139981944989?thread_ts=1749139162.622289&cid=G01BC76P1HD)) ([context](https://slack-pde.slack.com/archives/C056FV1CE9X/p1749824223062319?thread_ts=1749577762.190339&cid=C056FV1CE9X)) | TBD | Yes | Difficult to debug Spark jobs and root-cause issues |  |  |
| Feature parity for submitting odin-tools jobs to Bedrock ([context](https://slack-pde.slack.com/archives/C056FV1CE9X/p1750082869398899)) | TBD | Yes | Migrate to EMR 7 first |  |  |
| Feature parity for submitting notebook jobs to Bedrock ([context](https://slack-pde.slack.com/archives/C056FV1CE9X/p1750082805648559)) | TBD | No \- Post launch | Migrate to EMR 7 first |  | DT \- [Mimi Wang](mailto:mimi.wang@salesforce.com)[Colin Coppersmith](mailto:ccoppersmith@salesforce.com) |
| Gather information from peer companies (Pinterest, Airbnb) about opportunities and risks through knowledge sharing meetings. | TBD | No | Making decisions without knowledge of potential risks |  |  |
| PySpark with Python 3.11+ Requirements:\- ([thread](https://slack-pde.slack.com/archives/CJFHE7AR3/p1719603876400149))([thread](https://slack-pde.slack.com/archives/CJFHE7AR3/p1745533019238649?thread_ts=1699048360.478229&cid=CJFHE7AR3)) ([Data Tools DRI](https://slack-pde.slack.com/archives/CJFHE7AR3/p1749229142802789?thread_ts=1719603876.400149&cid=CJFHE7AR3))\- ([docker image with PySpark](https://slack-pde.slack.com/archives/C056FV1CE9X/p1750255238298669)) | TBD | N/A \- already done | Merlin/Sqlpen/Data tools will migrate to EMR 7 |  | [Yongjun Park](mailto:yongjun.park@salesforce.com)[Travis Cook](mailto:travis.cook@salesforce.com) |
| Application Support Dependency and Image matrix  |  | Yes |  |  |  |
| Clarity on what to do with Hadoop jobs (those running in the adhoc-manitoba cluster) ([thread](https://slack-pde.slack.com/archives/C056FV1CE9X/p1750096308319959))  | TBD | No | We will have to do EMR 7 upgrade for them |  | [Deepak Agarwal](mailto:deepak.agarwal@salesforce.com)[Raj Kumar](mailto:kumar.raj@salesforce.com) |
| Clarity on distcp jobs for DocJoin, a Hadoop job | TBD |  |  |  |  |
| Clarity on how to set executor PVC sizing ([context](https://slack-pde.slack.com/archives/CJFHE7AR3/p1750173834002969)) | TBD | Yes \- already have a plan  |  |  |  |
| Clarity on operation boundary with Cloud team. E.g. who is responsible for doing what during incidents. | TBD | Yes |  |  |  |
| Feature parity for queues for MF and DIG team, and potential future critical jobs. | TBD | Yes | SLA risk for critical jobs |  |  |
| Clarity on ODCR to support resource guarantee for critical jobs, required by MF and DIG queues | TBD | Yes | SLA risk for critical jobs |  |  |
| Clarity on automation of security patches ([context](https://slack-pde.slack.com/archives/C056FV1CE9X/p1750267482745719)) | TBD | Yes | Higher operational burden |  |  |
| Clarity on GovCloud (looks like it requires some code changes for DIG) | TBD |  |  |  |  |
| Security Review | TBD | Yes |  |  |  |
| Architecture Review | TBD | Yes |  |  |  |
| PRR  | TBD | Yes |  |  |  |
| HMS version / security / scalability | TBD |  |  |  |  |
| \[TODO\] Add more tasks here as we make progress |  |  |  |  |  |
| Spark UI inconsistent behavior ([example](https://slack-pde.slack.com/archives/C056FV1CE9X/p1752770115402129?thread_ts=1752599066.390979&cid=C056FV1CE9X)) |  | Yes | Operational burden |  |  |

# Risks

\[TODO\]

# Appendix

## \[1\] Spark-on-Kubernetes is a relatively new technology with limited industry adoption.

There is a common misconception that because Kubernetes is a mature and widely adopted platform, Spark-on-Kubernetes must also be equally mature. This assumption risks underestimating the complexity and potential pitfalls of the technology.

Publicly available data indicates that development activity on Spark-on-Kubernetes has slowed since 2022, and some supporting technologies like YuniKorn have seen reduced community engagement in the same period. Adoption has been relatively limited, with a few notable companies such as Apple and Pinterest having adopted it. Airbnb also intends to begin migration in the near future (Q3, 2025).

See more: [Spark-on-Kubernetes: additional concerns](https://docs.google.com/document/d/13xZ5jNc9yixC7uSIxpRrNBJfSh_775mCs7z5Tx5HDF8/edit?tab=t.0)

