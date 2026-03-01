2020: [Tackling scaling challenges of Spark at LinkedIn](https://databricks.com/session_na20/tackling-scaling-challenges-of-apache-spark-at-linkedin)

#spark 
#linkedin

* What are the top-level scaling challenges?
	* At resource management layer
		* decouple the cluster admin from the business of resource management. Created org-centric resource queue structures that enable individual orgs to self manage their queues. 
		* Enhanced the resource scheduler to automatically manage queue elasticity by assigning the cluster idle resources to queues that are most in need.
		* As a result, the mundane resource management processes are largely automated or delegated to our users.
	* At the Compute Engine layer
		* major effort optimizing Spark shuffle service, which is the biggest bottleneck in this layer. 
		* Multiple SQL automation techniques, including adaptive query execution.
	* At the User Productivity layer
		* get out of the support trap by enabling automated spark job understandability to answer the three most common customer support questions (why does my job fail? Why is my job slow? how can I make it faster?)
			* automatic failure root cause analysis
			* BridBench for performance analysis
			* Tuning recommendations
		* Automatic Failure Root Cause Analsys
			* List all exceptions from all logs automatically in the failure page of Azkaban. Essentially, they can extract the exception from the log, and still provide a link to the position (line number) of the full log, which allows the engineer to double-check.
			* Categorize the failure breakdown root cause for each team using a piechart. This allows the teams to find where their hotspots are, and take actions accordingly
			* Created a cluster infra failure trending charts (network, data shuffle, etc). Help us detect abnormal issues early on.
		- GridBench to answer why my job is slow.
			* Single app report, aggregate diff report (compare with a previous run), regression analysis report
		* How to improve
			* Tuning heuristics and recommendations. Color-coded recommendation with red color to show there are room to improve. This looks like Dr. Elephant.
	* How to gather the data
		* looks like Dr. Elephant, which needs to read logs, which triggered the scaling of SHS.
		* Designed distributed SHS to allow horizontal scale of SHS.
		* Incremental log parsing. P99, 1h -> 18s.
		* Spark Tracking Service (kafka+samza) talks to SHS and Yarn RM
			* The tracking service first read a stream from RM to get application_id and relavent RM data, then query the SHS to get Spark metrics. Then generate derived metrics, then publish these metrics to a dataset.
