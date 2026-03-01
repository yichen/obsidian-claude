# **2024 Year in Review: Spark on EMR**

Author: [Yi Chen](mailto:yichen@stripe.com)  [Gage Gaskins](mailto:ggaskins@salesforce.com)  Created: Dec 12, 2024  Last Updated: Jan 14, 2025

# Executive Summary

In 2024, we fundamentally resolved the reliability challenges for EMR while significantly improving cost efficiency, setting a new benchmark for operational excellence. Our efforts resulted in zero reported EMR reliability incidents in the last quarter, record annual cost savings of **$9.09 million**, and a **77.36%** cost reduction across the [top 20 EMR clusters](https://slack-pde.slack.com/archives/C8F0SQNSH/p1736455803190629). Additionally, we achieved substantial improvements in system observability and user experience.

I will provide a detailed breakdown of these achievements, highlighting the key projects that contributed to these results in the [**2024 Projects and Results**](#2024-projects-and-results) section, and offer a preview of upcoming initiatives in the [**2025 Priorities**](#2025-priorities) section.

# 2024 Projects and Results {#2024-projects-and-results}

## Cost Optimization

We exceeded our 2024 EMR cost savings goal, achieving [an annualized savings](https://salesforce-internal.slack.com/archives/C8F0SQNSH/p1736455803190629) of **$9.09 million** from March to December, representing a **77.36%** reduction—cutting costs by more than three-quarters. Key cost-saving initiatives include:

**Infrastructure Consolidation and Optimization (hardware):**

* Reduced resource waste by removing EC2 instances with [suboptimal memory-to-CPU ratios](https://docs.google.com/document/d/1J9AwR2G_UM10IvGB2bZp_TefA6DZU_D2rgCvtgUi0UM/edit?tab=t.0#heading=h.lnqfcyy21mit).  
* Eliminated spot instances from three critical clusters (data-platform, DMA, ETL) and secured capacity guarantees through ODCR purchases.  
* Consolidated [fragmented sub-clusters](https://docs.google.com/document/d/1Q8dkvYVi6Fwxs22Ta2Ei-8GwBia54cn6fyOgWB_hIW4/edit?tab=t.0#heading=h.lnqfcyy21mit) (e.g., merging [data-platform](https://slack-pde.slack.com/archives/C8EDM9MGA/p1711039411275369?thread_ts=1709759439.559199&cid=C8EDM9MGA), DMA, and Odin-tools).  
* Merged multiple small EMR clusters into larger and more efficient clusters: **prod-security-emr6**, **prod-data-infra-emr6**, **prod-data-tools-emr6**.  
* Removed [small EC2 instances](https://slack-pde.slack.com/archives/C8EDM9MGA/p1710168391306459?thread_ts=1709759439.559199&cid=C8EDM9MGA) (xlarge, 2xlarge, 4xlarge, 8xlarge) to reduce resource fragmentation and improve utilization.  
* Removed all expensive EC2 instances with local SSD disks.

**Resource Efficiency (software):**

* Fixed a technical debt that restricted Spark executors to only use 1 core ([PR](https://slack-github.com/slack/ops-go/pull/5934), [PR](https://slack-github.com/slack/ops-go/pull/6196)), which enabled per-job optimization.  
* Fixed a technical debt with improper use of TargetSpotCapacity and TargetOnDemandCapacity, which led to the unnecessary launch of a large number of instances during cluster startup ([PR](https://slack-github.com/slack/ops-go/pull/6317), [PR](https://slack-github.com/slack/ops-go/pull/6338))  
* Fixed a technical debt with long decommission timeout, which resulted in unnecessary waste during cluster decommission ([PR](https://slack-github.com/slack/ops-go/pull/6994))  
* Partnered with teams across the organization to manually identify and optimize Spark jobs with excessive resource allocation

## Reliability Improvement

By the end of Q2, we established [a new baseline for EMR reliability](https://docs.google.com/document/d/1vEQ5UD_r-cnqmI33CBxIDprPv074OHdYe_09wiZZeMY/edit?tab=t.0#heading=h.lnqfcyy21mit), with [no reported incidents in the last quarter](https://jira.tinyspeck.com/browse/DI-7751?jql=\(filter%20IN%20\(%22Data%20Engineering%20All%20Tickets%22\)\)%20AND%20\(\(project%20%3D%20%22Data%20Infrastructure%22\)%20AND%20\(labels%20%3D%20incident-review\)\)), eliminating EMR as a significant reliability concern. Key initiatives driving this success include:

**Root Cause Resolutions:**

* Identified and resolved [a long-standing reliability issue](https://slack-ce.slack.com/archives/C06PF50VCHJ/p1710432618074889) due to leaking file descriptors ([\#incd-240313-51084-dw-prod-logs-delayed](https://salesforce.enterprise.slack.com/archives/C06PF50VCHJ)) persisting for over three years.  
* Improved Livy stability by introducing HDFS caching, dramatically reducing application start times and eliminating failures caused by Livy timeouts.  
* Addressed [Spark shuffling challenges](https://docs.google.com/document/d/1xkddnyMmSJOyVHAAv8oMUll4Bw3KJo1TxCWDEnil3KU/edit?tab=t.0#heading=h.lnqfcyy21mit) by enabling Parquet compression, which reduced network transfer size and minimized disk storage footprint.

**Proactive Risk Management:**

* Developed a continuous EMR health check mechanism to automate risk detection and minimize operational impact.  
* Collaborated with partner teams to mitigate risks in the datahub listener and [Merlin backfills](https://docs.google.com/document/u/0/d/121mbhx08qjmLgo-rbYIXqroUAeyRhugwJnRHYUb4sjM/edit).  
* Achieved a clear understanding of current reliability risks, including [autoscaled cluster stability and capacity concerns](https://slack-pde.slack.com/archives/C8EDM9MGA/p1726601113255819), with plans to prioritize solutions.

## Observability and User Experience Enhancements

To improve the user experience, streamline troubleshooting, and increase operational visibility, we implemented the following:

**Log and Metrics Improvements:**

* Improved the availability of Spark/YARN logs by increasing YARN [log retention](https://slack-github.com/slack/ops-go/pull/6231) and removing spot instances from critical clusters.  
* Enhanced Airflow error logs with additional information to reduce user RCA (Root Cause Analysis) effort.  
* Improved YARN application tagging for better Spark metrics export.

**Metrics-Driven Decision Making:**

* Implemented [YARN and Spark metrics](https://docs.google.com/document/d/1qPAvq4bMi5fzmSpqC9D4z0E8GtAS9QCJe5SmaJQQvTw/edit?tab=t.0) to support data-driven prioritization of timeliness, reliability, and cost efficiency.  
* Introduced the capability to [measure](https://analytics.tinyspeck.com/v3/explore/1000000001545714) Spark-on-EMR infrastructure reliability separately from individual job reliability, enabling faster identification and classification of issues as either infrastructure health or application health.  
* Enabled targeted optimization by identifying specific Spark workloads for further reliability and cost improvements, initially focusing on [unmaintained jobs](https://docs.google.com/document/d/1nKxc_IoMLdnDAcDx9Y57DqWUc9fqqGgec249Kfu2p8k/edit?tab=t.0), which have already shown very [promising results](https://slack-pde.slack.com/archives/C06G45LGG7M/p1736445452506269).

**Team Toil, Knowledge Sharing and Scaling Best Practices:**

* Developed a Spark tuning guide for [container right-sizing](https://docs.google.com/document/d/199wkuvnvGWK5-5qdq83baCbvKaX3H_WiFwjJJXHDwY0/edit?tab=t.0#heading=h.lnqfcyy21mit) to promote cost-saving best practices.  
* Supported Nilanjana Mukherjee’s advanced Spark training to expand expertise across the user base.  
* Identified [inefficiencies in security tickets](https://docs.google.com/document/d/1TXqazw5qBeqyL_DYNf1w7XfG84s52MzLNdcg-TmR-pY/edit?tab=t.0), and are working with the partner teams to address this challenge.

# 2025 Priorities {#2025-priorities}

## We are prioritizing **Spark Capacity Management** and **EMR 7 Upgrades** as top initiatives to improve on-time performance and reliability while continuing to enhance cost efficiency and reduce operational risks across our EMR infrastructure. 

* We are launching a **Spark Capacity Management** [project](https://docs.google.com/document/d/19POB0Wl93-gE2JCnpOZaqDVrIXymhZjquY1Hg2brSVM/edit?tab=t.0#heading=h.lnqfcyy21mit) to address critical capacity constraints and ensure reliability across all clusters.  
* Due to resource limitations, our initial focus will be on implementing reasonable controls and resource allocation guarantees for critical workloads managed by the **MF** and **DIG** teams. Following this, we will upgrade EMR clusters to the latest **EMR 7.x** version, as all **EMR 6.x** clusters will reach end-of-life by **January 25, 2026**.   
* We will continue the cost saving effort in FY26Q1.  
* The remaining phases of the **Spark Capacity Management** project will resume after the EMR 7 upgrade is complete.

# Acknowledgements

Thank you to all the contributors to the EMR infrastructure, especially the members of the Data Infrastructure team under Nav’s leadership. This include [Nav Shergill](mailto:nshergill@salesforce.com),[Rahul Gidwani](mailto:rgidwani@salesforce.com)[Gage Gaskins](mailto:ggaskins@salesforce.com)[Tayven Taylor](mailto:tayven.taylor@salesforce.com)[Sherin Thomas](mailto:sherin.thomas@salesforce.com)[Mahendran Vasagam](mailto:mvasagam@salesforce.com)[Jigar Bhalodia](mailto:jbhalodia@salesforce.com)[Shreedhar Pawar](mailto:shreedhar.pawar@salesforce.com)

Thank you to [Deepak Agarwal](mailto:deepak.agarwal@salesforce.com) [Shrushti Patel](mailto:shrushti.patel@salesforce.com) for continued support.

Thank you to our partner teams for their tremendous efforts in tuning Spark jobs: [Nilanjana Mukherjee](mailto:nilanjana.mukherjee@salesforce.com), [Lawrence Weikum](mailto:lweikum@salesforce.com)[Joseph Thaidigsman](mailto:jthaidigsman@salesforce.com) [Alexander Bohr](mailto:abohr@salesforce.com). Thanks for taking over tasks that we do not have resources for. [Nilanjana Mukherjee](mailto:nilanjana.mukherjee@salesforce.com) for taking over the dashboarding and profiling, and [Jake Ziegler](mailto:jacob.ziegler@salesforce.com) for customizing DMA cluster queues, [Ian Davis](mailto:ian.davis@salesforce.com) for merging the security cluster.

Thanks to DE Leadership that supported these projects: [Nav Shergill](mailto:nshergill@salesforce.com)[Johnny Cao](mailto:johnny.cao@salesforce.com)[Lakshmi Mohan](mailto:lakshmi.mohan@salesforce.com)[Travis Cook](mailto:travis.cook@salesforce.com)[Prateek Kakirwar](mailto:pkakirwar@salesforce.com)[Benjamin Lee](mailto:benjaminlee@salesforce.com)[Suzanna Khatchatrian](mailto:skhatchatrian@salesforce.com)

