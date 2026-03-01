# **\[WIP\] Spark Capacity Management**

Status: *In progress*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Jul 1, 2024  Last Updated: Jan 14, 2025

This doc is work-in-progress, not ready for external reviews

# Executive Summary

By the end of FY25 Q2, we have made significant progress in Spark infrastructure (EMR) cost savings and also improving reliability at the same time. In FY26, we must start to invest in Spark capacity management, to further improve reliability, SLA timelessness, and continue to reduce cost. 

# Key Challenges

## Some critical clusters do not have true control on capacity guarantee

The prod-data-platform-emr6 cluster is one of our most critical clusters, running business critical pipelines for the data ingestion team, yet we don’t have a good way to protect and guarantee the cluster resources for these critical pipelines. In one case, we discovered that a non-critical job consumed 20% of the cluster resources. In another case, resource intensive jobs get delayed without enough resources ([example](https://slack-pde.slack.com/archives/C8EDM9MGA/p1730329411660409)). The reason is that this cluster has access to a secured dataset, and some non-critical pipelines are also running in this cluster. It is our goal to consolidate our pipelines into fewer and larger clusters, including prod-data-platform-emr6, but we also need to provide capacity guarantees for the critical pipelines in the multi-tenant environment.

## A large number of autoscaled Spark clusters is unreliable and expensive

A past decision was made to create dedicated, team-specific EMR clusters for individual teams to provide better capacity guarantees and reliability. However, this approach has proven counterproductive. The creation of numerous small, auto-scaled clusters not only increases reliability risks but also results in higher costs.

Recently, a new capacity risk has emerged. We have experienced multiple instances where AWS in the **us-east-1** region ran out of EC2 capacity for both on-demand and spot instances. When this happens, it impacts all of our EMR clusters, preventing them from scaling up to accommodate new workloads.

## High toil for handling security tickets

The Data Infrastructure team has to manually handle a large volume of security tickets due to the fact that we deal with a large number of EC2 machines. We currently have bought ODCR to cover almost 600 machines. We also automatically rebuild all of our clusters once a week. 

The security team automatically detects EC2 hosts that are vulnerable to security risks, such as outdated versions of software and operating systems. However, the verification process requires manual checks for each machine, and many of these JIRA tickets list hundreds of affected hosts. 

The challenge is further compounded by the fact that many clusters have autoscaling enabled. As a result, by the time we address the issue, many of these hosts may no longer exist, making the process even more difficult to manage.

## Weekly Cluster rotation is not only wasteful, but also at risk for capacity loss

We rebuild every EMR cluster every Wednesday. During this process, the old cluster must drain its workload while new workloads are submitted to the new cluster, leading to a temporary overlap. This overlap causes our cluster costs to nearly double during the rebuild period.

The primary reason for this resource waste is the low utilization of both the old and new clusters during the workload draining phase. By reducing the frequency of these rebuilds, we can significantly minimize this inefficiency. I estimate that we could save approximately 5% of our EMR costs by substantially decreasing the rebuild frequency.

We purchase **On-Demand Capacity Reservations (ODCR)** to ensure EC2 capacity for our clusters. However, we face significant risks during these rotations as well. The primary issue arises during the rotation process: the old cluster requires several hours to drain existing workloads, holding onto a substantial portion of its EC2 instances throughout the lengthy decommissioning period. This creates a high risk that AWS may encounter insufficient EC2 capacity during this time. Consequently, the new cluster may be unable to acquire the instances it needs, even though new workloads have already been redirected to it.

This capacity shortfall during the transition period can result in significant delays for new workloads, increasing the likelihood of SLA breaches and operational disruptions.

# Spark Capacity Management North Star

To address these challenges we face, I propose the north star for Spark capacity management.

## A very small number of larger clusters

We will reverse the previous decision to create team-specific clusters and consolidate them into larger, shared clusters. Ideally, we should maintain only two to three clusters: one for pipelines requiring secure data access and another for jobs that do not require secure data access.

This approach aligns with industry best practices for running large YARN clusters to achieve better cost efficiency. It was also validated during our FY25Q1 efforts, where merging smaller subclusters into main clusters (starting with three data-platform subclusters, three DMA subclusters, and three Odin-tools subclusters) contributed significantly to our cost-saving initiatives.

To provide better capacity guarantee for critical workloads, we will use team-specific queues in the shared clusters. This allows us to prioritize resources for more critical workloads. We plan to give enough freedom for the teams to create their own sub queues within their top-level queue so they have better control on how to distribute the resources. 

The main risk of this goal is the fragmentation of Spark and EMR versions. We currently have 5 different versions of EMR, each comes with a different Spark version. 

## Long-running clusters with intelligent, node-based rotation

Instead of weekly cluster rotation (tear-down and rebuild), we will run our cluster long term, potentially with HA enabled (running 3 master nodes instead of one), and only rotate when we face issues that can’t be solved. With this project, we can solve the following problems mentioned above:

* We will dramatically reduce the frequency of rebuilding the whole cluster, allowing us to capture about 5% of cost savings.  
* We will drastically reduce the team toil of manually verifying individual machines for each security ticket. We can develop automation to 

We will develop systems to automatically decommission nodes that are identified by the security team and remove them from the cluster, which will significantly reduce the manual work to check the node versions. 

The main risk of this project is to align with AWS EMR. We are in early conversation with EMR, which is willing to consider our needs and provide support to allow us to decommission and replace individual machines without having to rebuild the whole cluster.

## Intelligent auto-scaling

There are still use cases that can create bursty, unpredictable workloads that come with SLA expectations. For example, some critical metrics expect SLA that can be influenced by backfill performance. Some notebook users may expect a reasonable user experience when they explore a large amount of data. We may still need to find a way to accommodate these ad hoc workload in a cost effective way.