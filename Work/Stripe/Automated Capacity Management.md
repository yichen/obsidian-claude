#capacity

Follow up with Efficiency Team
- Can we eventually automate the ODCR process? 
	- ODCRs can be thought as always running EC2 instances once they are delivered. They are billed at full price as soon as they are delivered. 
- We want to delay decommissioning, batch them once every day, in queued clusters. Any concern on cost attribution?
- We want to automate on-demand user requested scale ups. For incidents, the capacity tickets can be auto approved. What is the expected user experience for the automated capacity management? Is it enough for the UI to ask the user to fill in the CAPACITY ticket (similar to the requirement for running sc-asg sync command)?