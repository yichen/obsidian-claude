- Build or Buy (EMR). The [decision](https://paper.dropbox.com/doc/Spark-Platform-Choice-v1--Bm~ZgjygRHjX0okHJ8sheWviAg-WXjQxzf2SpmkaCFSO9lRr) is to build for 2 years and decide again. 
- Today, Batch Compute runs YARN and HDFS to support Spark and Scalding worklaods.
- Hadoop infra cost is increasing: $61 million dollars pre-EDP in 2020 and expected to grow to $99 million pre-EDP in 2021. Data Platform has committed to reducing this amount in 2021
- [Why stay on folked Spark](https://paper.dropbox.com/doc/Why-stay-on-forked-Spark--Bm~ewFqX_rFdpU74ZD9guf5NAg-KkfeDRMhQPLEIvHVVqahg)
- Clusters are mostly static due to long decomission times (as of the end of 2021)
- 

[how to batch compute forecasts and track spend](https://paper.dropbox.com/doc/How-To-How-Batch-Compute-Forecasts-and-Tracks-Spend--Bm8sf~wtQ9yvLJtsSpmhFtREAg-aj4kYc17baoxnhnQSxLhr)
- As of Dec 2021, data platform does its own group-level spend forecast. Finance works with gsheets with actuals.
- hadoop_aws_ratio
- [batch compute budget dashboard](https://hubble.corp.stripe.com/viz/dashboards/23597-batch-compute-budget-dashboard)
- the driver of batch compute spending is overflow from billing users from rate-card rates.
- How batch compute cost impact stripe? Our per-transaction cost is 10x of competitors.
- What's next?
	- cost attribution is messy.
	- we don't understand what's driving our hadoop spend.
	- the rate card for a few clusters are difficult to get right.


[2022 August: Timeline Observability Spike](https://paper.dropbox.com/doc/notes-Timeliness-Observability-Spike-UAR--Bm8SlEASGArUZOvI1OU6RCE_Ag-OafDCCCz4smyDoY6RwUh5)
	
[2021 Q2: after-hours pages analysis](https://paper.dropbox.com/doc/After-hours-pages-analysis-Q2-2021--Bm~zEkVPPih5~wIh1mkdSZMvAg-rNgzgmf2ZZnRa0H2ur62R)
- looks like there is nothing of significant. 
- Looks like there are a total of 13 pagers in Q2, which is about 1 per week on average.

[2022 April UAR Report Retro](https://paper.dropbox.com/doc/April-UAR-support-retro--Bm_UbVkgcB2wljZSEO4ngF7fAg-l3IKpNZtCRymOjwaARBzU)
- batcom had to provide a lot of manual support for all scaleup requests. 
- Why not self-service? because users can't successfully execute commands on their own, constantly make errors in scaleup PRs, and lack of guardrails for executing commands.
- Even if we can self-service, our clusters are not ready for frequent scaleup and downs.


## Useful links

[List of Hadoop Clusters](https://confluence.corp.stripe.com/display/BATCOM/List+Of+Hadoop+Clusters)


-----

Questions
- The reference of cost pre-EDP. What is the meaning of "pre-EDP"?
	- 
- What is a "runner"? Are they the people on pager duty?
- "~25% of run for a week to be a single Spark-job-help ticket spread over the whole week." Does it mean it requires an engineer a week to help one ticket?
- What is data-job-srv? aka djs.
	- [djs explained](https://paper.dropbox.com/doc/Explaining-data-job-srv--Bm~JHBDv_QRTIck0lQLC_P7xAg-CcHXQW26wIfHSWkOVUIFC)
	- [djs design](https://paper.dropbox.com/doc/data-job-srv-Design--Bm_fkamXHPzbhadiABCGTFreAg-WV0dsxxvbAM2Lo2ehXsxx)
	- Essentially, it is the submisison gateway service for Hadoop jobs. It provides cluster routing, security principles and monitor/observability features.
	- currently all scheduled jobs are submitted throguh djs.
	- it is built in CI, deployed by Amp/Henson out of gocode repository.
	- 
- What is "non-icp jobs"?
	- ICP=Internal Controls Platform (financially relevant datasets?)
- "It’s turned off for ICP jobs, since without CIA we wouldn’t be able to securely tell jobs apart." What are ICP jobs? What is CIA?
- What is DOBC?
- What is TPP?
- What is SCD Hadoop Guard?
- What is blueberry? Is it a cluster name?
- What is gameday?
- What is CTR? Is it a cluster?
- What is RDP? Is it a cluster?
- What is sonic?
- What is amp?
- What are USM jobs?
- What is UAR? Is it "User Activity Report"?
- How do I query a hive table? 
- What is concord?
- What is ODCR?
	- On-demand ....
- What is Owl?
- What is Data Archiver?
- What is Hansel?
- Why cost attribution is based on vcores, not by memoryseconds?
- What is MyData host? Are they gateway machines?

- How does Henson work?
- What does "sc" means in sc commands?

- MyData is your personal server.


- during your onboarding, what did you do?