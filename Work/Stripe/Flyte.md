#flyte

- Flyte is a third party tool. See https://flyte.org/. 
- It is designed for ML process at scale, now identified as the adhoc workflow orchestration framework.
- Internally the early users include fraud-detection, programmically express their dynamic workflow.
- What problem does it solve for Stripe? Iterative, programmatic workflow with fast code-edit-to-execution cycles. 
- [Flyte uses Data-job-srv client](https://paper.dropbox.com/doc/Flyte-Requirements-for-Spark-Batch-Compute--BqM1H5BSCq_A_L0QIRY~ZUa8Ag-7zzorzA7xgTEOtTIQqPnZ), which has been depreciated. 
	- Why? Because an incident due to msp instability. MSP appears to be high risk.
	- DJS originally is a security offering, but limited benefit now that we use token based authentication.
- Best [blog about Flyte](https://eng.lyft.com/orchestrating-data-pipelines-at-lyft-comparing-flyte-and-airflow-72c40d143aad), how Lyft created it, and how it is deployed and operated.
	- Can use python, Spark, or ML framework leading to a resource-intensive computation, requiring custom libraries. The library version can be different across teams.
	- Ability to run heavy computation with no impact on other tasks.
	- ability to roll back and execute an older version of the workflow to compare the outputs and introspect.
	- support for results caching to speed up workflow execution, reduce cost.
	- Flyte architecture at Lyft
		- Flyte adds a meta-layer on top of Kubernetes to make large stateful executions possible. 
		- Flyte architecture is based on Kubernetes operators and custom resource definition. 