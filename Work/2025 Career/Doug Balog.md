
#stackav
#2025-06-04


- Platform Infrastructure Team
- The company is 2-year-old. Self driving trucks. Ingest the data into S3 object store. 
- Initially ingest data on AWS. Kafka, Redshift, EKS
- 9 months ago, migrate off AWS, rented data center space, to on-prem.
- We need to come up with an on-prem solution to replace redshift. Standardize on S3-compatible object store. Kubernetes for compute, and Iceberg table format. We picked Trino as the processing engine.
- 9 people in the group, but Doug is the only person on the data platform.
- Scheduler Omada from GResearch (on k8s). To run Spark on kubernetes. 
- IBM has a plug-in for Spark. 
- Why on-prem instead of cloud?
	- egress charge from S3 is too expensive from a previous company when they need to share the data with investors (Ford, VW), so the founders decided to be on-prem.



Work Life Balance
- it could be better.
- That's why we are hiring another person. Too much on my plate.
- support hours is 9-5pm, business hours.
- no after-hour on-call.
- We use Slack. We have standup at 11:30am for every group. Monday is the meeting heavy day. 