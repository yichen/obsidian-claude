#spark-internal


# Decommision

Spark can choose to decommision nodes ([SPARK-7955](https://issues.apache.org/jira/browse/SPARK-7955)), and Spark also needs to handle the case when the nodes are taken away from Spark ([SPARK-20624](https://issues.apache.org/jira/browse/SPARK-20624)).  These are a few cases when nodes are taken away not by choice:
* When nodes are spot or preemptible instances (GCP, EC2)
* On a shared cluster when the node is being preempted by higher priority tasks.

Spark 3.0 will try best to gracefully decommion these nodes. The "forceful" decommion logic includes the following two components:
* Exclude the node from the schedulable resources.
* Migrate shuffle files and RDD blocks.

This feature also requires installation of Node Termination Event Handler to the Kubernetes cluster if we are running Spark on k8s. Note that this feature (Spark graceful decommion) currently is only available on kubernetes. Looks like the YARN support is targed for after Spark 3.4.0 (see [SPARK-30873](https://issues.apache.org/jira/browse/SPARK-30873), [SPARK-30835](https://issues.apache.org/jira/browse/SPARK-30835))


# Fair Scheduler vs. Capacity Scheduler
- Fair scheduler guarantees that all jobs get an equal share of resources over time. That is, each job get the 