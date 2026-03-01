# **EMR 7 and Spark 3.5 Migration Plan**

Status: *Under review*  Author:   [Yi Chen](mailto:chen.y@salesforce.com)  [Gage Gaskins](mailto:ggaskins@salesforce.com)  Created: Aug 14, 2025  Last Updated: Sep 15, 2025

# Executive Summary

The EMR 6 end-of-life deadline makes migration to EMR 7 mandatory[\[1\]](#bookmark=id.hi9bkngp62xn). This upgrade introduces broader changes than prior EMR 6 upgrades, including major language runtime, OS, and dependency shifts.

At the same time, EMR 7 creates an opportunity to streamline several paused infrastructure migrations. By combining these efforts, we can reduce duplicated work for Spark users, consolidate clusters, and adopt modern scheduling practices in one coordinated move.

We expect this migration to:

* Ensure all production workloads meet the EMR 7 requirements on time  
* Deliver 15-20% cost savings through improved scheduling efficiency and resource consolidation  
* Reduce long-term friction for both users and the DI team by completing multiple migrations in a single pass.

This document outlines the strategy for sequencing migrations, the expected benefits, and the risk management plan.

# Goals

By end of EMR 7 Migration:

* **EMR 7 Upgrade completed:** All production clusters run EMR 7, Java 17, Scala 2.12/2.13, Spark 3.5.x. We can depreciate all EMR 6 clusters.  
* **Cluster consolidation:** A very small number (3-5) of larger clusters replace team-specific clusters..  
* **Modern scheduling:**CapacityScheduler replaces FairScheduler, aligning with industry standards and providing stronger capacity management in larger clusters. Unlock future capacity management opportunities. 

Achieving these goals requires careful sequencing and prioritization. The following context section explains why combining migrations into a single effort is the most efficient and least disruptive approach.

# Context

Large infrastructure migrations are inherently disruptive, requiring collaborative effort from both the DI team and user teams (DIG, MF, Insights, DT, etc). EMR 7 is especially complex due to the scope of the change: a nine-version Java upgrade, a four-version Python upgrade, and an OS shift from Amazon Linux 2 to Amazon Linux 2023\.

If we treated EMR 7 in isolation, users would face multiple separate efforts soon after —- adopting CapacityScheduler, consolidating clusters. Each of these migrations, while lower-risk, demands time-consuming changes and close monitoring and tuning.

By combining them into a single coordinated migration:

* **Users move once:** Spark users migrate jobs a single time to the target EMR 7 clusters, rather than repeating such changes for each migration.  
* **Risks stay orthogonal:** The risks of cluster consolidation or scheduler adoption are mostly independent of EMR 7 risks[\[2\]](#bookmark=id.kfrynvepz4v7), making failure easier to diagnose and resolve.   
* **Total workload shrinks**: For example, if CapacityScheduler were handled separately as another migration, Spark teams would spend \~2 extra months migration DAGs. Folding it into the EMR 7 transition eliminates that duplicate effort.

This approach reduces total migration effort for Spark users while front-loading more coordination work on the DI side, a tradeoff that prioritizes user productivity and minimizes disruption across DE organizations.

# Strategy

The strategy for EMR 7 migration is to front-load high-risk areas and validate our approach early, ensuring that user-facing impact is minimized. Each phase builds confidence, reduces uncertainty, and delivers incremental value to both DI and user teams.

**Phase 1: Foundation**

In this phase, the DI team establishes the groundwork for migration:

* Stand up EMR 7 clusters with full automation parity (emrAdm, automatic rotation, healthcheck, Chef cleanup)  
* Configure CapacityScheduler as the default on new clusters and validate queue functionality for DIG and MF.  
* Define the initial cluster and queue layout to support consolidation and scheduling goals.  
* Conduct risk assessments (Java 17, Python 3.11, Spark 3.5.6) and publish user-facing guidance for expected issues.  
* Identify infrastructure-level automation or tooling that can proactively reduce friction for users.  
* Identify Spark User DRIs for each Spark user teams and cohorts[\[3\]](#bookmark=id.r8vgg8450unc).

**Outcome**: Users see no disruption while the DI team builds a production-ready EMR 7 environment and prepares documentation for a smooth migration.

**Phase 2: Pilot Migration**  
   
Plans must be validated under real workload conditions. The pilot migration engages a broader surface area with **low-risk but representative jobs**, surfacing issues that can’t be discovered through analysis alone.

* Migrate selected DIG, MF, and DT DAGs that have the largest version gaps but lowest operational risk  
* Validate Python-related dependencies and other ecosystem risks. Identify user-side engineering work.  
* Capture performance, stability, and cost observations from pilot jobs.  
* Refine and expand the migration playbook based on findings.

**Outcome**: Unknown risks are uncovered in a controlled way, mitigation strategies are documented, and both DI and user DRIs gain clarity on engineering effort and resourcing.

**Phase 3: Migration**  
The main migration effort follows a deliberate sequencing:

* Begin with DE-owned workloads. This ensures playbooks are hardened at scale before external adoption.  
* Extend to external DE user teams (adhoc, manitoba, search, ML, IDR, etc)  
* Continuously refine cluster/queue layout as workloads shift, and tune scheduler policies and capacity for performance and cost.  
* Maintain ongoing cost and performance analysis to measure impact

**Outcome**: Users transition once to EMR 7 clusters with validated playbooks, minimizing rework and disruption.

**Phase 4: Clean-up & Post migration Planning**  
After workloads are fully migrated:

* Decommission EMR 6 clusters, code, and artifacts  
* Simplify code paths and reduce technical debt.  
* Capture lessons learned to improve processes for future migrations (e.g. EMR 8, or Spark-on-Kubernetes).

**Outcome**: The EMR 7 migration is completed cleanly, and DI is positioned for more efficient future transitions.

# Execution Plan

| Stage | Task | Desired Outcome | Target Deadline | Docs/Resources/Discussions | DRI / Partners |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Foundation  | Stand up EMR 7 clusters with automation | At least 2 production-grade EMR 7 clusters launched with full parity  | FY26Q3 |  | [Gage Gaskins](mailto:ggaskins@salesforce.com) (DI) |
|  | Enable CapacityScheduler as default on new  clusters | DIG and MF queues validated | FY26Q3 | [Migration to CapacityScheduler on EMR 7.10: Strategic Recommendation](https://docs.google.com/document/d/1xCEfh5gzGtvGbDoh3Mydy3dbO9OWrUkTjJnvsw6R0_0/edit?tab=t.0) | [Gage Gaskins](mailto:ggaskins@salesforce.com) |
|  | Define initial Cluster and Queue Layout | Baseline cluster footprint deployed, roadmap agreed. | FY26Q3 | [EMR 7 Cluster and Queue Management](https://docs.google.com/document/u/0/d/1q_9aOVmVYHZ_UQ0VRiSAZyl9VUFSgVTqwHp3Q8FgtBc/edit) | [Yi Chen](mailto:chen.y@salesforce.com) |
|  | Deploy last-minute cost savings for EMR 6 clusters | Identify a clean cost baseline before EMR 7 migration for cost comparison | FY26Q3 |  | [Yi Chen](mailto:chen.y@salesforce.com) |
|  | Risk Assessments: Java 17, Python 3.11, Spark 3.5.6 | Clear migration plan; initial user-facing documentation |  | [Java & Python Upgrade for EMR 7](https://docs.google.com/document/u/0/d/19chWBBas9NwTk9lOUl09-BM5g3nZqUFxBVtDhWyj7v4/edit) [Spark 3.5.5 Upgrade Risk Assessment for EMR 7](https://docs.google.com/document/u/0/d/1pdL7ZoF-Ehtf3tH86ObyiO9KMGKl1sauXt2vrqI5LEo/edit)[Sqlpen’s Python](https://slack-pde.slack.com/archives/CJFHE7AR3/p1745533019238649?thread_ts=1699048360.478229&cid=CJFHE7AR3)[DataTools](https://slack-pde.slack.com/archives/CJFHE7AR3/p1749229142802789?thread_ts=1719603876.400149&cid=CJFHE7AR3)  | TBD [Travis Cook](mailto:travis.cook@salesforce.com)[Yongjun Park](mailto:yongjun.park@salesforce.com) |
|  | Risk Follow ups | TBD. (e.g. potential impact include parallel Spark jar build pipeline, HDFS caching changes). | FY26Q3 |  | TBD |
|  | Initial comms with user DRIs | First migration playbook delivered; DRIs identified and aligned | FY26Q3 |  | [Yi Chen](mailto:chen.y@salesforce.com) |
| Migration (Pilot) | DIG Pilot Migration | Identify low risk, high return DAG to migrate to uncover risks that may impact other DIG workloads. Prefer migrate workloads with the largest version gap from EMR 6.11.1.  | FY26Q4 |  |  |
|  | MF Pilot Migration | Identify low risk, high return DAGs to migrate to uncover risks that may impact other MF workloads. Prefer migrate workloads with largest version gap from EMR 6.11.1 | FY26Q4 |  |  |
|  | Data Tools Migration | Identify Python related risks early | FY26Q4 |  |  |
|  | DI Pilot Migration follow-up | Identify and document all issues discovered from pilot migrations. Measure performance improvements and cost improvements.  | FY26Q4 |  |  |
| Migration (DE internal)  | Migrate DIG workloads | Migrate DP, data-ingestion, percolator (?) clusters, all DIG backfill clusters | FY26Q4 |  |  |
|  | Migrate MF workloads | Migrate DMA and all MF backfill clusters | FY26Q4 |  |  |
|  | Continuous Cluster and Queue Tuning | continuous | FY26Q4 |  | [Yi Chen](mailto:chen.y@salesforce.com) |
|  | Cost and Performance analysis post migration | continuous | FY26Q4 |  | [Yi Chen](mailto:chen.y@salesforce.com) |
|  | Begin external team workload migration | External teams begin planning/implementing workload migrations | FY26Q4 |  |  |
| Migration (DE external) | Migrate all other clusters in US under data-engineering-prod account | Related EMR 6 clusters  migrated | FY27Q1 |  |  |
|  | Migrate adhoc clusters, manitoba, search, ml clusters | Related EMR 6 clusters  migrated | FY27Q1 |  |  |
|  | Configure, Deploy, and Migrate IDR clusters | Related EMR 6 clusters  migrated | FY27Q1 |  |  |
| Decommission EMR 6 and Post-Moterm | Decommission EMR 6 specific code, artifacts | EMR 6 code cleaned up | FY27Q2 |  | Person |
|  | Performance and Cost Analysis | Analyze cost savings and performance comparison | FY27Q2 |  | [Yi Chen](mailto:chen.y@salesforce.com) |
|  | Lessons Learned for next major migration | Identified next steps to make the next migration smoother | FY27Q2 |  |  |

# Risks & Mitigrations

## \[high\] Large Java & Python version gap

Unlike the EMR 6 migration, we need to address a new risk: the Java upgrade. EMR 7 upgrades the default runtime from Java 8 to Java 17 (a nine-version jump). This introduces potential compatibility and runtime issues. To mitigate the risk and avoid case-by-case ad hoc solution, the DI team will do a thorough impact assessment (see [Java & Python Upgrade for EMR 7](https://docs.google.com/document/u/0/d/19chWBBas9NwTk9lOUl09-BM5g3nZqUFxBVtDhWyj7v4/edit)), and come up with a plan to reduce user friction. 

## \[high\] Spark 3.5.6 Upgrade Risk

There are potential breaking changes in Spark 3.5.6 that may affect existing workloads that are still running on Spark 3.3.x. To mitigate the risk and avoid case-by-case ad hoc solutions during migration, the DI team will do a risk assessment and come up with a plan. See [Spark 3.5.5 Upgrade Risk Assessment for EMR 7](https://docs.google.com/document/u/0/d/1pdL7ZoF-Ehtf3tH86ObyiO9KMGKl1sauXt2vrqI5LEo/edit).

## \[medium\] Operation System upgrade

The EMR 6 to EMR 7 migration requires an OS upgrade from Amazon Linux 2 to Amazon Linux 2023, with no in-place upgrade path. There was no OS upgrade from EMR 5 to EMR 6 migration, so there are potential risks associated with this.

For example, Spark jobs relying on external libraries (e.g. numpy, pandas) may fail if those libraries are unavailable or incompatible with AL2023’s versions.

To mitigate the risk, we will engage key users (MF, Merlin/Sqlpen, DT, DIG) early and prioritize the breath in early migration, so we can uncover issues earlier.

# Spark User DRI List

To ensure a safe migration, each Spark user team should designate a DRI (Directly Responsible Individual) in October 2025\. The DRI will act as the accountable point of contact for their team’s workloads and coordinate with DI during the migration process.

DI will own the migration platform and provide shared tooling, documentation, and guidance, while Spark user DRIs ensure their team’s workloads are represented, migrated, and validated. This shared model surfaces risks early, balances engineering effort, and enables a confident EMR 7 rollout.

In terms of engineering effort for the DRI,it ranges from minimal (risk reviews, representative job validation, sign-off) to significant (adapting jobs if API/runtime incompatibilities are found). Early engagement allows us to scope and prioritize together.

| DRI | Workload / Scope | Main Risks and Concerns |
| :---- | :---- | :---- |
| [Sai Tarun Tadakamalla](mailto:saitarun.tadakamalla@salesforce.com) | Admin and Trust Insights TODO | TODO |
| [Deepak Agarwal](mailto:deepak.agarwal@salesforce.com) | Workloads in prod-ml-emr6, prod-search-emr6, adhoc-manitoba-emr6,  |  |
| [Jess Stewart](mailto:jessica.stewart@salesforce.com) | OLAP |  |
| [Samuel Bock](mailto:sbock@salesforce.com) | Data Orchestration  |  |
| [Robert MacNguyen](mailto:rmacnguyen@salesforce.com) | MPG |  |
| [Anthony Chao](mailto:achao@salesforce.com) | Experiments and Insights | None. |
| [Jake Ziegler](mailto:jacob.ziegler@salesforce.com) | MF |  |
| [Joseph Thaidigsman](mailto:jthaidigsman@salesforce.com)Person | DIG |  |

This information will give us the initial context we need to identify risks and dependencies. To start, please include all EMR clusters where your team’s workloads are running, since the mass migration will likely be organized at the cluster level. As a rule of thumb, the more context you provide, the better—for both DI and your team. If the details don’t fit here, feel free to link to a doc.

We’d like to get a sense of the following:

* Which EMR clusters is your team using?  
* Do your jobs require any cluster-specific dependencies (e.g., different Java versions or other custom configs)?  
* What’s the nature of your jobs—Scala or PySpark? Are you using Sqlpen/Merlin with Python dependencies?   
* If your job is not running through Airflow, who do you run your jobs? (eg. Quarry client, Notebooks)

# Appendix

## \[1\] We must migrate to EMR 7

The EMR 6 end-of-life is set for July 2026 (an extension from the original January 2026 deadline), making the migration to EMR 7 mandatory. Although we're working on Spark-on-Kubernetes, we must still move some workloads, such as search, ML, and Manitoba, to EMR 7 because they have a core dependency on Hadoop. We have no practical alternatives to run these workloads on Kubernetes before the EMR 6 deadline.

## \[2\] EMR 7.x Foundational Changes

* Spark 3.5.6, Python 3.11, Java Corretto 17 (JDK 17), Amazon Linux 2023 by default  .  
* Delta Lake 3.0+, Hadoop 3.4.1 (in newer 7.x like 7.9.0), Hudi, Iceberg, and other ecosystem components are updated  .  
* Deprecation of Ganglia; enhancements include CloudWatch Agent, Kerberos AES-only, S3A on Outposts, upgraded UIs, and container bin-packing in 7.9.0 .  
* Support lifecycle: EMR 6.15.x is under bridge support until early 2026, EMR 7.0 will go out of standard support in December 2025; newer releases like 7.9.0 extend support further to 2026–2027 .

## \[3\] Spark User DRI early engagement

To ensure a safe migration, each Spark user team should designate a DRI (Directly Responsible Individual) in October 2025\. The DRI will act as the accountable point of contact for their team’s workloads and coordinate with DI during the migration process.

DI will own the migration platform and provide shared tooling, documentation, and guidance, while Spark user DRIs ensure their team’s workloads are represented, migrated, and validated. This shared model surfaces risks early, balances engineering effort, and enables a confident EMR 7 rollout.

Your DRI ensures your team’s workloads are represented, risks surfaced, and migration outcomes unblocked, and final sign-off after the completion of migration.

Ranges from minimal (risk reviews, representative job validation, sign-off) to significant (adapting jobs if API/runtime incompatibilities are found). Early engagement allows us to scope and prioritize together.

# \======= Scratch Notes Below \======

## Current Active EMR 6 Clusters

### 

| Cluster Name | EMR Version | Spark Version | Java Version | Python Version |
| :---- | :---- | :---- | :---- | :---- |
| prod-etl-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| adhoc-manitoba-emr6 | emr-6.15.0 | 3.4.1 | 8 | 3.7 |
| dev-sqooper-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| prod-sqooper-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| staging-analytics-emr6  | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| prod-search-quality-emr6   | emr-6.15.0 | 3.4.1 | 8 | 3.7 |
| prod-percolator-emr6   | emr-6.15.0 | 3.4.1 | 11 | 3.7 |
| prod-dma-emr6 | emr-6.12.0 | 3.4.0 | 8 | 3.7 |
| prod-ml-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| prod-search-emr6 | emr-6.15.0 | 3.4.1 | 8 | 3.7 |
| prod-data-infra-emr6   | emr-6.15.0 | 3.4.1 | 11 | 3.7 |
| prod-data-platform-emr6 | emr-6.15.0 | 3.4.1 | 11 | 3.7 |
| prod-data-ingestion-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-search-quality-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-insights-emr6  | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-search-emr6   | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-dma-emr6 | emr-6.12.0 | 3.4.0 | 8 | 3.7 |
| backfill-dea-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-data-tools-emr6 | emr-6.11.1 | 3.3.1 | 8 | 3.7 |
| backfill-data-platform-emr6 | emr-6.15.0 | 3.4.1 | 8 | 3.7 |
| adhoc-manitoba-spark-emr6 | emr-6.15.0 | 3.4.1 | 8 | 3.7 |
| gov-search-emr6 | emr-6.15.0 | 3.4.1 | 11 | 3.7 |
| expressone | emr-6.15.0 | 3.4.1 | 11 | 3.7 |

### 

| EMR Version | Spark Version |  |  |
| :---- | :---- | :---- | :---- |
| emr-6.11.1 | 3.3.2 (livy: 0.7.1)/Scala:2.12.15/python:3.7/Hadoop:3.3.3/Hive:3.1.3 |  |  |
| emr-6.12.0 | 3.4.0 (livy:0.7.1/Scala:2.12.15/python:3.7/Hadoop:3.3.3/Hive:3.1.3) |  |  |
| emr-6.15.0 | 3.4.1/Scala:2.12.17/python:3.7/hadoop:3.3.6/hive:3.1.3 |  |  |
| emr-7.9.0 | 3.5.6/Scala:2.12.18/Livy:0.8.0/Hadoop:3.4.1/Hive:3.1.3 |  |  |

