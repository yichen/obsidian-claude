# **Evaluating CapacityScheduler Migration alongside EMR 7 Migration**

Status: *Under review*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Aug 31, 2025  Last Updated: Sep 3, 2025

| Sep 3, 2025 | Shared in data-infra channel ([thread](https://slack-pde.slack.com/archives/CJFHE7AR3/p1756910089305629)). |
| :---- | :---- |
|  |  |

# Summary

We recommend using the EMR 7 migration as the forcing function: all new EMR 7 clusters should adopt CapacityScheduler as the default. Workloads can then be gradually cut over during the migration window.   Combined with cluster consolidation, this transition is expected to improve resource utilization and deliver significant cost savings—estimated at \~20%—through new scheduling features unavailable in FairScheduler.

**Key Benefits:**

* **Improved resource optimization** with global scheduling and asynchronous processing.  
* **Cost reduction** through container bin-packing and faster node scaling.  
* **Higher throughput performance** for multi-tenant Spark workloads.  
* **Alignment with industry standards and AWS defaults** (LinkedIn, Airbnb, Uber, Cloudera).

# Context and Justification

CapacityScheduler has become the industry standard for large Spark deployments and is the default in both AWS EMR and Cloudera. At Slack, our use of FairScheduler is now a deviation from best practice. Migration has been on our roadmap but repeatedly deferred due to limited bandwidth and unclear benefits.

With EMR 7, advanced CapacityScheduler features—including async scheduling, global scheduling, and container bin-packing—are now production-ready. These directly address our operational needs in cluster consolidation, workload performance, and cost efficiency. The EMR 7 migration creates a natural window to introduce CapacityScheduler with minimal incremental disruption.

# Feature Comparison

## Global Scheduling

* **What it is:** Optimizes allocation across the full cluster, not just within queues or nodes.  
* **FairScheduler limitation:** Focuses on fairness within queues, not global optimization.  
* **Business impact:** Smarter allocation across consolidated clusters → higher utilization and fewer idle resources.

## Asynchronous Scheduling

* ​​**What it is:** Decouples scheduling requests from the main thread, dramatically improving throughput.  
* **Performance:** Expected 40–60% improvement in concurrent application handling (per YARN-7327, Spark 3.5 integration).  
* **Business impact:** Better performance under high workload concurrency, reduced scheduling delays.

## Container Bin-Packing

* **What it is:** Consolidates containers onto fewer nodes, enabling faster decommissioning and reducing waste. Available in EMR 7.9+.  
* **Cost impact:** Estimated 10–20% compute cost reduction through improved node utilization (YARN-11736, YARN-11643, YARN-11742, YARN-4676).  
* **Business impact:** Direct cost savings through reduced cluster footprint.

# Risk Assessment and Mitigation Strategy

| Risk | Impact | Mitigation |
| :---- | :---- | :---- |
| Configuration Complexity | medium | Start with MVP, incremental improvements |
| Learning Curve | medium |  |
| Workload Compatibility | low | Phased migration |
| Performance Regression | medium | Phased migration with detailed monitoring |

# Migration Implementation Plan

## Phase 1: MVP adoption

* Set up prod-data-platform-emr7 using CapacityScheduler.  
* Initial queue config mirrors current FairScheduler setup (low risk).

## Phase 2: Continuous tuning of the queue during workload migration

* During workload migration, progressively enable async scheduling and container bin-packing.  
* Monitor performance, utilization, and cost metrics closely.