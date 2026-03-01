
#work  #batcom

## TODO
- Dmitry: what's the idea around CapacityScheduler, NodeLabel.

-----

## 2023-11-15

Your request for help has been submitted to paidleave@esd.wa.gov. If you would like to follow up, please contact paidleave@esd.wa.gov or 833-717-2273

WA Medical Leave Account
- Customer ID: F6GRDD2R0Q
- Claim ID: **F6GRDD2R0Q-1**

## 2023-10-30
Larkin Company
	- Complete the certification process by Nov 14. It could be MD, RN, and I have to be seen (screenshot of appointment is OK) in the first 8 days, in order to approve the leave. 
	- For salary replacement, (1) I need to apply for WA medical leave benefits myself. (2) I also need to apply short-term disability insurance from LincolnFinancial. (3) Stripe provides top-up to make up the diff for the first 8 weeks.
	- jwright@thelarkincompany.com
		- 650-938-0933, Direct extension: 376
	- I will not have access to Stripe email during leave.

## 2023-10-16
- Count-Min Sketch is considered an implementation of Counting Bloom Filter, just used differently. A counting bloom filter is a generalized bloom filter, used to test whether a count number of a given element is smaller than a given threshold when a sequence of elements is given. 
- CMS (Count-Min Sketch) can be used to estimate the frequency of items in a stream of data. It is particularly useful when the size of the data stream is too large to store in memory, or when we want to perform frequent updates to the data stream in real-time.
- CMS results are not always accurate ("probabilistic data structure"), but the probability of error can be controlled by the user.
- [CMS is used in streaming](https://www.synnada.ai/blog/probabilistic-data-structures-in-streaming-count-min-sketch#:~:text=The%20Count%2DMin%20Sketch%20(CMS,data%20stream%20in%20real%2Dtime.)
- The basic idea of CMS:
	- use hash functions to map items in the stream to a fixed-size array, and then use this array to store an estimate of the frequency of each item. The CMS maintains a 2-D array of counters, where each row corresponds to a hash function and each column corresponds to a hash value. When an item is encountered in the stream, it is hashed using each of the hash functions and the corresponding counters are incremented. 
	- CMS are biast estimators of the true frequency of events: they may over estimate, but never underestimate the true count in a point query. 
	- While the min estimator works well when the distribution is highly skewed, other sketches such as the Count sketch based on means are more accurate when the distribution is not sufficiently sewed.
- Applications
	- Database query planning: when determining the order in which several joins are performed, a task known as join order optimization.
	- Estimate the table sizes yield by certain subqueries. 
- Sketch Join 
	- compute count min sketch of keys of transactions 
	- Add integer column to transactions based on the count of the key from count min sketch
	- add integer column to countries and replicate entries based on the count of the key from count min sketch
	- join transactions with countries using the country code and the integer as the join key
	- 
## 2023-09-11

Understanding [YARN Node Labels](https://hadoop.apache.org/docs/stable/hadoop-yarn/hadoop-yarn-site/NodeLabel.html)
- One node can have only one node partition. There are two kinds of node partitions: exclusive and non-exclusive. Non-exclusive partition shares idle resource to container requesting DEFAULT partition (it seems to mean that a container request to DEFAULT partition can also be answered by non-exclusive partitioned nodes.)
- Users can specify set of node labels which can be accessed by each queue (which determines what node labels the applications in the queue can access)
- Each node can be assigned one label.
- Specify percentage of resource of a partition which can be accessed by a queue. Eg. queue A can access 30% of resources on nodes with label=hbase.
- If no node label requirement in resource request, it will be allocated on nodes belong to DEFAULT partition.
- Node labels and node labels mapping can be recovered across RM restart.
- Admin can update labels on nodes and labels on queues when RM is running.
- 3 ways to map NM to node labels:
	- Centralized: done through RM exposed CLI, REST, or RPC
	- Distributed: set by a configured Node Labels Provider in NM. Two providers in YARN: Script based provider (the script emit the labels) and Configuration based provider (yarn-site.xml). In both cases, dynamic refresh of the label mapping is supported.
	- Delegated-Contralized: set by a configured Node Labels Provider in RM. 
	- 

Experiment on Pluot
- 

## 2023-09-08

Capacity Management Project Outline Review Meeting
- Ideal state: work towards a bright future, we can call out things we can't do in the short term (like larger clusters)
	- Habib: for example, the capacity ticket process is manual, it is not part of ideal state.
- Dmitry: autoscale under utilized queues.
- Habib: we need a more accurate estimate before the design meeting.
	- 3 weeks is too optimistic. If it is only 3 weeks, we can just break down to tasks and assign somebody to work on it.
- Habib: Have a FAQ why each users can take a physical cluster instead of queues, in case anybody ask this question.
- Dmitry: for Blueberry true-ups. One of the issue is multi-tenant in this cluster. One bad user can saturate and distablize the whole cluster, and cause other jobs to miss SLAs.
- Dmitry: who should plan the capacity? Who should say this queue should up scale or down scale. This creates waste. We should have clarification, how to detect such cases, starvations, etc. It worth calling it out as objective. 

## 2023-09-06

Meeting with Habib
- Don't want to get too much into details. We want to make sure we are addressing the right problems. When it is done, we will solve future capacity management issues.
- Plan project outline meeting this Friday, inviting Dmitry, Habib, Gaurav, Mike, Eugene
- Extra work may need my time that takes a day or two, ping Dmitry or Yashiyah, regarding some monitoring work.

Meeting with Efficiency
- ODCR automation
	- How does it work? Will you have an API, a service?
	- When it will be done?
- ODCR: what can be automated?
	- can we automate go/spark-capacity-request?
	- Can we automate Apricot V2?
	- Can we automate sapphire?
- What do you think if we do autoscale transparently?
	- Apricot V2: users asks to auto-scale transparently (usm and notebook). They don't want to reserve capacity, they just want it to work.
- What about savings plan?
	- Is based on how much time we ended up paying AWS.
	- It makes sense to have a base line covered by saving plane. 
	- It will be tough for Yarn scheduler to determine for two rate cards. Ben and Eugene can be better for this question.
- Do you have major concern for 
- Ben/


## 2023-09-05

Meeting with Dmitry:
- We don't have to call out the implementation of reduce fragmentation. That is also transparent to users.
- What to do with Blueberry. We should have a list of problems we face today, and breakdown solution.
- D: do you mean we have two rate cards for Apricot v2?
	- Current rate card doc: https://docs.google.com/document/d/15JN3vgYzYJ4TUVN_4tUAVt_cUH0e-qN_FXnPqJ-baQ8/edit#heading=h.hn1eojhflea1
	- A trade off, we may increase cost of Apricot V2 by 20%.
- D: you need to decide for yourself if the Project Outline should 
- Apricot is also ad hoc cluster.
- D: it is up to you to decide what is the outcome by the end of this month. If you need help, please communicate upfront. 
	- Personally it doesn't sound good if we postpone Apricot work (users ask for it). 
	- You need to make a call.

- [ ] do we need to schedule a project outline meeting with DP or just private sharing?
- [x] Habib wants to include the "golden path" for capacity management, and want to discuss if the apricot v2. but we also want to make things doable in Q4.
	- [ ] What's your opinion about the scope of the DP Design Doc? 
	- [ ] I plan to write the design doc to start with long-term goal, but with more details for Q4 deliverables.
	- [ ] Do we need a DP level alignment for project outline? If so, how to scope it out if it can be done in Q4?

Meeting with Gaurav
- Node Label vs. Dynamic Allocation
- Savings Plan
	- Need to work with Efficiency team and figure out how they calculate savings plan[]()
- ODCR is more complicated
	- If we don't have ODCR in Apricot.
	- We should have a base line node count for Apricot covered by Savings Plan.
- Slack first. Don't need to share the doc yet, just say what you want to do, link to doc later. 
- Maybe you should also talk to Zach Puller. He worked on Yarn CLI toolings, and he may ran into some stopper.


## 2023-08-31

TODO: Meeting for Automated Hadoop Capacity Management
- How ODCR's impact for this project? According to the doc, we need an ODCR for requests for more than 500 vcores. According to [Vein's email](https://groups.google.com/a/stripe.com/g/data-platform-users/c/fgC3L4WP3Js/m/RVZJ7CRrAAAJ), the go/spark-capacity-request has a toggle to label ODCR desired (for EOM scale ups), then copy a string to a google sheet, then link this google sheet to the capacity ticket. 
	- Does automation means replace the go/spark-capacity-request with a planned UI, and automatically creating the Google sheet, and automatically generate the Google Sheet?
- Should we create a use case to handle organic growth scale ups? See [Vein's comment](https://docs.google.com/document/d/1PG-nW1PwPlNWiAskRnIfK_GyHSioDs9DdiW1UFEvNIM/edit?disco=AAAA4Fy7Wh8).
- Meeting Notes:
	- Vein: we don't use ODCR for UAR anymore although we used to ask the users to give 6 weeks of leading time. With current node type (i4) we have more availability. This could change anytime because it is tied to specific AZ. 
	- Do we need ODCR for graviton? For BFCM for sure. 
	- Why can't we create ODCR on-demand? Vein: it has to be accepted by AWS, and it takes about 1 day. So automation of ODCR creation has limit, it won't work for urgent scale ups.
	- Vein: Ben Sanders wrote a script to detect on-demand pool, by doing a dummy instance requests, like 100 instances of a certain type, and then return it back to the pool, to poke and see if getting any ICE error. 
	- Vein: we can automate a ODCR request through API if it cross a certain threshold. We need to automate canceling them as well.
	- If any request over 50 instances, or the pool is low, over 10 instances, we should create an ODCR.  If ODCR is not fast enough for incident, we have a donor list, for teams who is willing to donate cores. But how do we know if a pool is lower? We can work with the Efficiency team (@bensanders)
	- Check with Efficiency Team if we can call ODCR API endpoints directly, or their team should provide an abstraction.
	- Regarding Savings Plans. For Apricot, even if we scale up and down frequently, it is almost cheaper to keep nodes alive. If you can scale down 50% for 50% of the time, it worth auto-scaling. The goal is to consolidate and see if this can be improved


Understanding Savings Plan
- [Auto-Scaling and Savings Plans](https://confluence.corp.stripe.com/display/EFC/AWS+Auto-Scaling+and+Savings+Plans)
	- Get up to 60% discount on on-demand EC2 instances in exchange for a commitment.
	- SPs automatically apply across all instance types and regions. 
	- Stripe: we want to cover 98% of on-demand EC2 spend with SPs.
	- SPs are purchased by Efficiency team by a process.  Purchases once in a while (e.g. once a month). If we see $100/hour in permanent on-demand spending, we would go ahead and purchase a SP worth $50/hour. The reason is that the SP discounted rate is 50% cheaper compared to on-demand.
	- Auto-scaling with spot or on-demand instances.
		- Spot: save 90% discount on on-demand pricing without the need to enter into hourly commitment. There is no risk of wast during periods of scaled down. Spot instances are not covered by savings plans.
		- On-Demand: the instances have to be scaled down at least 33%/day (8h) day on weekdays and 100% on weekends to achieve savings from auto-scaling with on-demand. This will result in at least 5% savings. 
-  Typical savings plan terms are 1 years and 3 years.


Understanding ODCR (On-Demand Capacity Reservations)
- [Stripe's doc on ODCR](https://confluence.corp.stripe.com/display/EFC/On-Demand+Capacity+Reservations).
- ODCRs enable us to reserve and guarantee availability of EC2 capacity in a specific region and availability zone for any duration. 
- ODCR has no relationship to Savings Plans. This is because ODCRs can be created, resized, or canceled at any time without entering into a term commitment (whereas SPs cannot be canceled once purchased), and ODCR do not affect pricing. 
- ODCRs are billed at regular EC2 rates, and billing starts as soon as the capacity is provisioned and made available to Stripe. 
- ODCRs can be thought of as always running EC2 instances once they are delivered, even if no actual EC2 instances are running to consume these ODCRs.
- Use cases for ODCRs:
	- migrations.
	- guaranteed capacity needs for special events (Prime Day, BFCM)
	- limited instance types.
- We request capacity in advance from AWS. If AWS already have enough avaiable, AWS will inform us that no ODCR is needed. Otherwise, they will ask us to submit an ODCR. 
- We don't pay anything if we cancel an ODCR before it's active
- ODCR request workflow
	- All capacity needs with a future date (e.g. BFCM) need an ODCR.
	- Request process is manual: submit an intake document, capacity request to get spend approved. The efficiency team work with AWS 
	- Each team's ODCR requests should be filed separately, so the efficiency team can track it properly.
- BATCOM is now requiring ODCRs filed at least 6 weeks before EOM scale-up. See [Vein's email](https://groups.google.com/a/stripe.com/g/data-platform-users/c/fgC3L4WP3Js/m/RVZJ7CRrAAAJ).
	- 

## 2023-08-30
Meeting with Habib
- Be strategic, long term, instead of tactical
	- For example, the design doc need to answer why not EMR, why not LinkedIn approach.
	- There will be a lot of people with a lot of opinions. It is important to get early feedbacks.
- 

[Decommission Stats of past 30 days](https://splunk.corp.stripe.com/en-US/app/search/search?q=search%20source%3D%22%2Fpay%2Flog%2Fterminator.log%22%20%20%22terminator%3A%20Checking%20host%20termination%20status%20for%20decom_v4%22%20%0A%7C%20rename%20_time%20as%20time_A%20%20%20%0A%7C%20join%20host%20%5Bsearch%20source%3D%22%2Fpay%2Flog%2Fterminator.log%22%20%22terminator%3A%20Done%20checking%20host%20termination%20status%20for%20decom_v4%22%20%7C%20rename%20_time%20as%20time_B%5D%20%20%20%0A%7C%20eval%20duration%20%3D%20(time_B%20-%20time_A)%2F3600%20%20%20%0A%7C%20table%20host%20duration&earliest=-30d%40d&latest=now&display.page.search.mode=smart&dispatch.sample_ratio=1&display.page.search.tab=statistics&display.general.type=statistics&display.prefs.statistics.offset=0&display.statistics.sortColumn=duration&display.statistics.sortDirection=desc&sid=1693418032.655306_DE80D5E2-3181-423B-90C7-CAA234E8DC08&display.prefs.statistics.count=100)
- 8325 total number of Hadoop nodes decommissioned 
- Total hours are 41565 hours for these 8325 nodes. This means that we spend 5 hours per node for decommissioning on average.


## 2023-08-29

Meeting with Dmitry
- Automate Capacity Management
	- Prototyping 
		- have a sense of scope
		- verify the node labeling work
	- Design doc: run some numbers for efficiency team so they have some story to tell. For example, how would apricot autoscaling not causing blow up in cost.
	- If you need additional help, ask for it.
	- DP Review: schedule it up front, not wait for the last minute. We don't need more gavel besides Efficiency. 
- Getting out of low ROI Spark jobs.
	- What's missing is somebody need to make a call.
	- Be very explicit about this. Otherwise, we keep the box open, and people keeps providing feedbacks and suggestions.
- If it helps to sync more often on automate capacity management. Let me know.

Detail Engineering Work
- How many nodes do we have today across all clusters?
	- strawberry: 94, decommissioned:29
	- strawberryarm64: 438, decommissioned:864
	- blueberry: 185, decommissioned:38
	- blueberryarm64: 733, decomissioned: 33
	- sapphire: 53, decommissioned:385
	- qos: 123, decommissioned: 22
	- qosarm64: 346, decommissioned: 98
	- apricot: 259, decommissioned: 214
	- indigo: 813, decommissioned: 18
	- concord: 1283, decomissioned: 130
	- plum: 3
	- test: 6
	- pluot: 3
	- foley: 6
	- 


Understanding hadoop-adhoc
- Looks like there is a service called [hadoop-adhoc-srv](https://confluence.corp.stripe.com/pages/viewpage.action?pageId=228315501) It handles adhoc provisioning of hadoop queue capacity.
	- It uses postgresql
	- ssh connectivity to a running hadoop cluster.
	- How does hadoop-adhoc-srv creates an audit trail/history records?

## 2023-08-28
Meeting with Dmitry and Priyaka
- User ask for Priyanka's project: https://docs.google.com/document/d/1aNmeG_FyL-sAA6AvALB1mD6xPBLRsUISrW8FRTOo8e4/edit#heading=h.g2d8olu0xw74
- Discussions
	-  We still need to do Schedule ups and downs, assume less than 10% scales ups and downs. We should not consider using node labels for queued clusters.
	- Ad hoc cluster, apricot cluster. We can afford node labels on ad hoc cluster for single-tenancy 
	- Decommission every 2 days, only works for queued cluster. Not working for adhoc cluster with no queues.
	- Ad hoc: we do not expect the users to plan capacity up front.
	- Sharing adhoc and scheduled workload in team-based queue is not feasible now because of ICP
	- Dmitry: add a prototype with capacityscheduler. From implementation point of view.
- Decisions
	- Plan to run two projects under one umbrella, Yi is the DRI. We use the project's slack channel.
	- Yi to decide if we need extra headcount for CapacityScheduler prototyping
	- Yi to come up with project outline and design doc, with milestones and justifications for headcount.
	- Follow up on Thursday morning.
## 2023-09-15

Apricot analysis
- In first 7 days in September:
	- [all apps](https://hubble.corp.stripe.com/queries/yichen/b8008685): P90: 34, p85: 17, p75:6, p50:1, p25:0
	- [USM apps only](https://hubble.corp.stripe.com/queries/yichen/8e96521c):  P90: 53, p85:30, p75:10, p50:2, p25:1
- In last 90 days:
	- [non usm apps](https://hubble.corp.stripe.com/queries/yichen/058ca99c):  P90:35, P75: 8, P50: 2, P25:0
	- [usm only](https://hubble.corp.stripe.com/queries/yichen/995f2bfb): P90:64, p85:35, p75:13, p50:2, p25:1
- Apricot scheduler API: https://hadoop-apricot-resourcemanager.corp.stripe.com/ws/v1/cluster/scheduler
- An example app: [application_1685468332903_2470]( https://hubble.corp.stripe.com/queries/yichen/ff837d9a)
	- vcore_seconds: 1706476
	- killed after 2,938 minutes in apricot  (48.9 hours)
- Compared to a app finished with 40 minutes: application_1691513392670_11270
	- vcore_seconds: 303,037
Meeting with Vein
- How much apps is from notebook? It will keep the queue and app alive for a long time. If there are more pending container request for a queue, we can scale up that queue. We have signalfx metrics. Maybe ResourceManager JMX can have this metrics.
- Ask if there is a way to query hubble/trino. 

Meeting with Helen
- Node Label: can I spin up new nodes with ASG but label with with a different label than the rest?
- hadoop-adhoc-srv, does it have a manual way to override the automation? How much effort we spend in developing this service in weeks?
- How do we do security check? How do we map the user name to the team name who owns the queue?
- Do we have a way to deploy a service to the RM nodes besides cronjobs? How does this client identify itself by a cluster ID?
- We use puppet to push labels to node: https://livegrep.corp.stripe.com/view/stripe-internal/puppet-config/modules/hadoop/manifests/resource.pp#L123
	- Helen: maybe it is easier to add a new host type (with same instance type), and use puppet to push the node labels.
	- Looks like at bootstrap time with puppet, labels are stored here: `system/yarn/node-labels/`
- 
- TODO:
	- Try replaceLabelsOnNode: https://hadoop.apache.org/docs/stable/hadoop-yarn/hadoop-yarn-site/NodeLabel.html#Add.2Fmodify_node-to-labels_mapping_to_YARN
	- What are the chances when an app we thought will finish within 30 minutes did not.
- 


## 2023-09-12

Understanding hadoop-adhoc
- Looks like there is a service called [hadoop-adhoc-srv](https://confluence.corp.stripe.com/pages/viewpage.action?pageId=228315501) It handles adhoc provisioning of hadoop queue capacity.
	- It uses postgresql
	- ssh connectivity to a running hadoop cluster.
	- valid iam credentials for the engineers role
	- How does hadoop-adhoc-srv creates an audit trail/history records?
- Service calls to interact with ASG requires IAM credentials. 
- API source code: https://git.corp.stripe.com/stripe-internal/zoolander/tree/master/src/scala/com/stripe/hadoop/adhoc/api/v1
	- Looks like this Scala service was built on Twitter Finagle library. It has a statsd client which emits metrics to SignalFX.
	- It has ability to run `scheduleTask` inside the service. There are two scheduled tasks: queue clean up and hdfs clean up. The source code for tasks is under ./task/ tree. Looks like these tasks are scheduled once every 10 minutes.
	- HadoopClusterClient: it uses RM's REST API. It also has an ASG client, to describe ASG.

## 2023-09-11

Understanding [YARN Node Labels](https://hadoop.apache.org/docs/stable/hadoop-yarn/hadoop-yarn-site/NodeLabel.html)
- One node can have only one node partition. There are two kinds of node partitions: exclusive and non-exclusive. Non-exclusive partition shares idle resource to container requesting DEFAULT partition (it seems to mean that a container request to DEFAULT partition can also be answered by non-exclusive partitioned nodes.)
- Users can specify set of node labels which can be accessed by each queue (which determines what node labels the applications in the queue can access)
- Each node can be assigned one label.
- Specify percentage of resource of a partition which can be accessed by a queue. Eg. queue A can access 30% of resources on nodes with label=hbase.
- If no node label requirement in resource request, it will be allocated on nodes belong to DEFAULT partition.
- Node labels and node labels mapping can be recovered across RM restart.
- Admin can update labels on nodes and labels on queues when RM is running.
- 3 ways to map NM to node labels:
	- Centralized: done through RM exposed CLI, REST, or RPC
	- Distributed: set by a configured Node Labels Provider in NM. Two providers in YARN: Script based provider (the script emit the labels) and Configuration based provider (yarn-site.xml). In both cases, dynamic refresh of the label mapping is supported.
	- Delegated-Contralized: set by a configured Node Labels Provider in RM. 
	- 

Experiment on Pluot
- 

## 2023-09-08

Capacity Management Project Outline Review Meeting
- Ideal state: work towards a bright future, we can call out things we can't do in the short term (like larger clusters)
	- Habib: for example, the capacity ticket process is manual, it is not part of ideal state.
- Dmitry: autoscale under utilized queues.
- Habib: we need a more accurate estimate before the design meeting.
	- 3 weeks is too optimistic. If it is only 3 weeks, we can just break down to tasks and assign somebody to work on it.
- Habib: Have a FAQ why each users can take a physical cluster instead of queues, in case anybody ask this question.
- Dmitry: for Blueberry true-ups. One of the issue is multi-tenant in this cluster. One bad user can saturate and distablize the whole cluster, and cause other jobs to miss SLAs.
- Dmitry: who should plan the capacity? Who should say this queue should up scale or down scale. This creates waste. We should have clarification, how to detect such cases, starvations, etc. It worth calling it out as objective. 

## 2023-09-06

Meeting with Habib
- Don't want to get too much into details. We want to make sure we are addressing the right problems. When it is done, we will solve future capacity management issues.
- Plan project outline meeting this Friday, inviting Dmitry, Habib, Gaurav, Mike, Eugene
- Extra work may need my time that takes a day or two, ping Dmitry or Yashiyah, regarding some monitoring work.

Meeting with Efficiency
- ODCR automation
	- How does it work? Will you have an API, a service?
	- When it will be done?
- ODCR: what can be automated?
	- can we automate go/spark-capacity-request?
	- Can we automate Apricot V2?
	- Can we automate sapphire?
- What do you think if we do autoscale transparently?
	- Apricot V2: users asks to auto-scale transparently (usm and notebook). They don't want to reserve capacity, they just want it to work.
- What about savings plan?
	- Is based on how much time we ended up paying AWS.
	- It makes sense to have a base line covered by saving plane. 
	- It will be tough for Yarn scheduler to determine for two rate cards. Ben and Eugene can be better for this question.
- Do you have major concern for 
- Ben/


## 2023-09-05

Meeting with Dmitry:
- We don't have to call out the implementation of reduce fragmentation. That is also transparent to users.
- What to do with Blueberry. We should have a list of problems we face today, and breakdown solution.
- D: do you mean we have two rate cards for Apricot v2?
	- Current rate card doc: https://docs.google.com/document/d/15JN3vgYzYJ4TUVN_4tUAVt_cUH0e-qN_FXnPqJ-baQ8/edit#heading=h.hn1eojhflea1
	- A trade off, we may increase cost of Apricot V2 by 20%.
- D: you need to decide for yourself if the Project Outline should 
- Apricot is also ad hoc cluster.
- D: it is up to you to decide what is the outcome by the end of this month. If you need help, please communicate upfront. 
	- Personally it doesn't sound good if we postpone Apricot work (users ask for it). 
	- You need to make a call.

- [ ] do we need to schedule a project outline meeting with DP or just private sharing?
- [x] Habib wants to include the "golden path" for capacity management, and want to discuss if the apricot v2. but we also want to make things doable in Q4.
	- [ ] What's your opinion about the scope of the DP Design Doc? 
	- [ ] I plan to write the design doc to start with long-term goal, but with more details for Q4 deliverables.
	- [ ] Do we need a DP level alignment for project outline? If so, how to scope it out if it can be done in Q4?

Meeting with Gaurav
- Node Label vs. Dynamic Allocation
- Savings Plan
	- Need to work with Efficiency team and figure out how they calculate savings plan[]()
- ODCR is more complicated
	- If we don't have ODCR in Apricot.
	- We should have a base line node count for Apricot covered by Savings Plan.
- Slack first. Don't need to share the doc yet, just say what you want to do, link to doc later. 
- Maybe you should also talk to Zach Puller. He worked on Yarn CLI toolings, and he may ran into some stopper.


## 2023-08-31

TODO: Meeting for Automated Hadoop Capacity Management
- How ODCR's impact for this project? According to the doc, we need an ODCR for requests for more than 500 vcores. According to [Vein's email](https://groups.google.com/a/stripe.com/g/data-platform-users/c/fgC3L4WP3Js/m/RVZJ7CRrAAAJ), the go/spark-capacity-request has a toggle to label ODCR desired (for EOM scale ups), then copy a string to a google sheet, then link this google sheet to the capacity ticket. 
	- Does automation means replace the go/spark-capacity-request with a planned UI, and automatically creating the Google sheet, and automatically generate the Google Sheet?
- Should we create a use case to handle organic growth scale ups? See [Vein's comment](https://docs.google.com/document/d/1PG-nW1PwPlNWiAskRnIfK_GyHSioDs9DdiW1UFEvNIM/edit?disco=AAAA4Fy7Wh8).
- Meeting Notes:
	- Vein: we don't use ODCR for UAR anymore although we used to ask the users to give 6 weeks of leading time. With current node type (i4) we have more availability. This could change anytime because it is tied to specific AZ. 
	- Do we need ODCR for graviton? For BFCM for sure. 
	- Why can't we create ODCR on-demand? Vein: it has to be accepted by AWS, and it takes about 1 day. So automation of ODCR creation has limit, it won't work for urgent scale ups.
	- Vein: Ben Sanders wrote a script to detect on-demand pool, by doing a dummy instance requests, like 100 instances of a certain type, and then return it back to the pool, to poke and see if getting any ICE error. 
	- Vein: we can automate a ODCR request through API if it cross a certain threshold. We need to automate canceling them as well.
	- If any request over 50 instances, or the pool is low, over 10 instances, we should create an ODCR.  If ODCR is not fast enough for incident, we have a donor list, for teams who is willing to donate cores. But how do we know if a pool is lower? We can work with the Efficiency team (@bensanders)
	- Check with Efficiency Team if we can call ODCR API endpoints directly, or their team should provide an abstraction.
	- Regarding Savings Plans. For Apricot, even if we scale up and down frequently, it is almost cheaper to keep nodes alive. If you can scale down 50% for 50% of the time, it worth auto-scaling. The goal is to consolidate and see if this can be improved


Understanding Savings Plan
- [Auto-Scaling and Savings Plans](https://confluence.corp.stripe.com/display/EFC/AWS+Auto-Scaling+and+Savings+Plans)
	- Get up to 60% discount on on-demand EC2 instances in exchange for a commitment.
	- SPs automatically apply across all instance types and regions. 
	- Stripe: we want to cover 98% of on-demand EC2 spend with SPs.
	- SPs are purchased by Efficiency team by a process.  Purchases once in a while (e.g. once a month). If we see $100/hour in permanent on-demand spending, we would go ahead and purchase a SP worth $50/hour. The reason is that the SP discounted rate is 50% cheaper compared to on-demand.
	- Auto-scaling with spot or on-demand instances.
		- Spot: save 90% discount on on-demand pricing without the need to enter into hourly commitment. There is no risk of wast during periods of scaled down. Spot instances are not covered by savings plans.
		- On-Demand: the instances have to be scaled down at least 33%/day (8h) day on weekdays and 100% on weekends to achieve savings from auto-scaling with on-demand. This will result in at least 5% savings. 
-  Typical savings plan terms are 1 years and 3 years.


Understanding ODCR (On-Demand Capacity Reservations)
- [Stripe's doc on ODCR](https://confluence.corp.stripe.com/display/EFC/On-Demand+Capacity+Reservations).
- ODCRs enable us to reserve and guarantee availability of EC2 capacity in a specific region and availability zone for any duration. 
- ODCR has no relationship to Savings Plans. This is because ODCRs can be created, resized, or canceled at any time without entering into a term commitment (whereas SPs cannot be canceled once purchased), and ODCR do not affect pricing. 
- ODCRs are billed at regular EC2 rates, and billing starts as soon as the capacity is provisioned and made available to Stripe. 
- ODCRs can be thought of as always running EC2 instances once they are delivered, even if no actual EC2 instances are running to consume these ODCRs.
- Use cases for ODCRs:
	- migrations.
	- guaranteed capacity needs for special events (Prime Day, BFCM)
	- limited instance types.
- We request capacity in advance from AWS. If AWS already have enough avaiable, AWS will inform us that no ODCR is needed. Otherwise, they will ask us to submit an ODCR. 
- We don't pay anything if we cancel an ODCR before it's active
- ODCR request workflow
	- All capacity needs with a future date (e.g. BFCM) need an ODCR.
	- Request process is manual: submit an intake document, capacity request to get spend approved. The efficiency team work with AWS 
	- Each team's ODCR requests should be filed separately, so the efficiency team can track it properly.
- BATCOM is now requiring ODCRs filed at least 6 weeks before EOM scale-up. See [Vein's email](https://groups.google.com/a/stripe.com/g/data-platform-users/c/fgC3L4WP3Js/m/RVZJ7CRrAAAJ).
	- 

## 2023-08-30
Meeting with Habib
- Be strategic, long term, instead of tactical
	- For example, the design doc need to answer why not EMR, why not LinkedIn approach.
	- There will be a lot of people with a lot of opinions. It is important to get early feedbacks.
- 

[Decommission Stats of past 30 days](https://splunk.corp.stripe.com/en-US/app/search/search?q=search%20source%3D%22%2Fpay%2Flog%2Fterminator.log%22%20%20%22terminator%3A%20Checking%20host%20termination%20status%20for%20decom_v4%22%20%0A%7C%20rename%20_time%20as%20time_A%20%20%20%0A%7C%20join%20host%20%5Bsearch%20source%3D%22%2Fpay%2Flog%2Fterminator.log%22%20%22terminator%3A%20Done%20checking%20host%20termination%20status%20for%20decom_v4%22%20%7C%20rename%20_time%20as%20time_B%5D%20%20%20%0A%7C%20eval%20duration%20%3D%20(time_B%20-%20time_A)%2F3600%20%20%20%0A%7C%20table%20host%20duration&earliest=-30d%40d&latest=now&display.page.search.mode=smart&dispatch.sample_ratio=1&display.page.search.tab=statistics&display.general.type=statistics&display.prefs.statistics.offset=0&display.statistics.sortColumn=duration&display.statistics.sortDirection=desc&sid=1693418032.655306_DE80D5E2-3181-423B-90C7-CAA234E8DC08&display.prefs.statistics.count=100)
- 8325 total number of Hadoop nodes decommissioned 
- Total hours are 41565 hours for these 8325 nodes. This means that we spend 5 hours per node for decommissioning on average.


## 2023-08-29

Meeting with Dmitry
- Automate Capacity Management
	- Prototyping 
		- have a sense of scope
		- verify the node labeling work
	- Design doc: run some numbers for efficiency team so they have some story to tell. For example, how would apricot autoscaling not causing blow up in cost.
	- If you need additional help, ask for it.
	- DP Review: schedule it up front, not wait for the last minute. We don't need more gavel besides Efficiency. 
- Getting out of low ROI Spark jobs.
	- What's missing is somebody need to make a call.
	- Be very explicit about this. Otherwise, we keep the box open, and people keeps providing feedbacks and suggestions.
- If it helps to sync more often on automate capacity management. Let me know.



## 2023-08-28
Meeting with Dmitry and Priyaka
- User ask for Priyanka's project: https://docs.google.com/document/d/1aNmeG_FyL-sAA6AvALB1mD6xPBLRsUISrW8FRTOo8e4/edit#heading=h.g2d8olu0xw74
- Discussions
	-  We still need to do Schedule ups and downs, assume less than 10% scales ups and downs. We should not consider using node labels for queued clusters.
	- Ad hoc cluster, apricot cluster. We can afford node labels on ad hoc cluster for single-tenancy 
	- Decommission every 2 days, only works for queued cluster. Not working for adhoc cluster with no queues.
	- Ad hoc: we do not expect the users to plan capacity up front.
	- Sharing adhoc and scheduled workload in team-based queue is not feasible now because of ICP
	- Dmitry: add a prototype with capacityscheduler. From implementation point of view.
- Decisions
	- Plan to run two projects under one umbrella, Yi is the DRI. We use the project's slack channel.
	- Yi to decide if we need extra headcount for CapacityScheduler prototyping
	- Yi to come up with project outline and design doc, with milestones and justifications for headcount.
	- Follow up on Thursday morning.
## 2023-08-25
Meeting with Jordan: Data Platform Control Plane
- Service Config: config change (like queue size) in amp UI, pushed to config srv.
- Storage in DynamoDB.
- Use Workflow Engine (temporal) to listen to changes in configs (config srv) and apply that change. The workflow will replace the runbook scripts.
- Not sure if there are existing puppet support in the workflow.
- This is very encouraging for me (Jordan). My challenge is to use my design, and if something doesn't work, I would change my design. 

Meeting Data Processing Staff Sync
- Dmitry: Pryanka's work with users directly is huge related to capacity management (backfill? recon team?)
	- CapacityScheduler, use node labels to true up the cost (nodelabel as the team), 
	- Queue: it is still easier for cost attribution.
	- recommission host?
- Gaurav: backfill jobs should be moved away from appricot, isolate them.
- 

## 2023-08-24

Automate Capacity Management
- Meeting with LinkedIn. [Meeting Notes](https://docs.google.com/document/d/1aUYUk3wdgiFZ4I-U5d1uxgwvj5I9wULtW64oum154PQ/edit#heading=h.5pmckgnm6s65).
- Regarding puppet: looks like there is a way to [automatically run puppet](https://confluence.corp.stripe.com/display/OS/Automated+Puppet+Rollouts).  Our hadoop hosts have opted out of automated puppet runs. A200 services the box would get puppeted "<3 business days" after merging a change. config-svr agent may need to be installed on my host type. See [puppet channel thread](https://stripe.slack.com/archives/CDMH18D19/p1692898594842619?thread_ts=1692834595.737949&cid=CDMH18D19).
- 

Meeting with Zhen
- We could have a process running on ResourceManager, run by a cron, which pull down the XML config file from S3 or somewhere else.
- It will be difficult to figure out how to access and update XML from outside of ResourceManager. 
- We have an example cron job today on ResourceManager:  https://livegrep.corp.stripe.com/view/stripe-internal/puppet-config/modules/hadoop/manifests/rm_monitor.pp#L40
- Do we need to restart ResourceManager? need to check sc-puppet --ssh log. 

Meeting with Gaurav
- I believe scaling down do decommission the oldest nodes.
- Be super clear on the goal. It may be enough to improve the UX, reduce the team toil. You may not want to over complicate things by achieving cost saving as well. I would stay clear from money saving.
- I recommend having the goals super clear. If you do this project, how to measure success. What success looks like. If the goal is saving cost, I will approach it differently. If reduce toil and improve UX, I will approach it differently.
- Dmitry may want cost saving
	- Gaurav: if it is a goal, then list it explicitly. I am not saying we should not listing cost saving as a goal. I am saying it very explicitly. 
- Does config-srv have a way to apply the XML locally on RM nodes?
- Look at Sapphire. There is a UI. Look into how it solves this problem and generalize it. Helen write it with Jon Bender. Joy may have some context. Note that Sapphire is using Capacity Scheduler. Make sure we can do that with FairScheduler. Sapphire keeps the capacity in database, not in git. 
- May need to integrate with CIA platform so users cannot change other team's queue.
- Think about how preemption work.

## 2023-08-22
Meeting with Dmitry
- Automate Capacity Management
	- We have statistics in signalfx from Shahyar for decomission time. We can get a counter by nodes, over a month, to get a overall cost of decomission. We decommission all host once every 21 days. Calculate the overhead in percentage, to calculate the cost saving opportunity.
	- What about implementation?
		- SPICE:
		- Dmitry: I am not aware of anything we can reuse to automate. I do see we can leverage some common infrastructure from change management, but I am not sure if that's that's what we want to do. I want to be super programmatic because we have a very short time line. If 5% of things can be borrowed from shared infra (like SPICE), it does not worth it.
		- If aligning with SPICE takes a month, it would not worth it. 
		- Dmitry: We need a transactional and relational database, we could use PostgreSQL, but I don't know the current state. 
		- It may worth having a meeting with the CORE COMPUTE team (infra platform), and Fleet Management to explain what we are trying to do, and see what they recommend. It worth explore what tools we have (but if not enough value, don't need to use it)
	- Dmitry: I am really look forward for this. I also recommend looking at Jordan's "[programmabile control plane](https://docs.google.com/document/d/1dFIN9j5Yq1aATKOBSnhfIZcZr6sjjUi7aTAXx5h8IWk/edit#heading=h.fpmk99277na9)" It may have some resources. I recommend get on board with this to get more visibility of this project.
	- It may worth schedule office hour with Jordan after I have an initial plan. He may be super excited about this. This will create more peers and contribute to data platform strategy. You can get more visibility and alignment and appreciation from doing this work. This helps with performance review.
	- I also recommend start with a [project brief, project outline](https://docs.google.com/document/d/1-tT3R4aSD7knIFQZO3lI90wqDTMfIP9B7T2CTtM05Ko/template/preview)
- **We already have something in apricot.*? 
	- Dmitry: i meant sapphire. We want to use sapphire infra and leverage it in other clusters, including blueberry. 
	- We mainly want to automate the team toil for weekly/biweekly true up of blueberry and other shared clusters.
- Feedback on operations.
	- We still need to figure out ways to approach things **consistently**.
	- E.g. we got paged, we just execute the runbook, instead of looking it deeply.
	- I like to see a bit more of root cause analysis for operational issues.
- What's the plan for low ROI Spark job deletion?
	- I don't have a plan.
	- The project scope creeps. 
	- It will be useful: in contrast to follow up, be super clear on what we will do. That is, closing the door. 
	- Dmitry: let's talk with Habib after he is back. In my opinion, we need a lot of observability, need to align with many parties. A lot of it is narratives and how we present it. I am pretty interested in follow up, feel free to loop me in.
	- 

## 2023-08-18
Meeting with Vein
- **We already have something in apricot.**? 
	- A: we have something for sapphire. Vein believe this is the model we are looking for (instead of the apricot model below).
		- Sapphire is managed with http://go/hadoop-adhoc
		- For cost attribution in Sapphire, cost attributed to the team from UI.
	- A: we have a cron-based scale up and down for apricot. 
		- The cron job is built-in from fleet management. We don't have much control unless we tell them (fleet management). We use this framework to define our policy: https://trailhead.corp.stripe.com/docs/edge/runbook-autoscaling-policies. This is the policy we defined: https://confluence.corp.stripe.com/display/BATCOM/%5Brunbook%5D+hadoop-apricot+true+up
		- We can't allow creating/deleting queues in apricot.
- How does ODCR work with our scale-ups and downs? Looks like we just use it to cover existing capacity so we can recycle hosts safely.
	- Vein: efficiency team added some new API, may need to talk to them.
	- Vein: ODCR usually have 1 to 2 weeks of notice. It's more a long term planning, you can't expect it to work in 2 hours.
	- Vein: for long term, we may be able to notice users that we can't guarantee the capacity. ICE: Insufficient Capacity Exception. This ICE is being tracked in splunk and also somewhere in Hubble.
- What happens when I merge two scale ups and downs with different CAPACITY tickets.
	- Vein: this does not affect cost graph. mostly used by finance to ensure that the capacity ticket has been approved.
	- Vein: we also need to add time constraint: we don't want people to scale down 10 minutes after scale up, because batch-compute team may eat the 2-day decommission tie.
	- Vein: we should allow people to plan monthly scale ups and downs and do it automatically. It's a nice to have.
	- Vein: daily scaling ups and downs sounds right, it could be even 2 days. for automatic frequency.
	- 
- What's the current infrastructure that can be reused?
- What's the difference between puppet and sync and the significance of their ordering?
- SPICE vs. config-svr?


## 2023-08-16
Automate Capacity Management
- How to determine if we need to scale up or down a cluster (e.g indigo)? See [doc](https://trailhead.corp.stripe.com/docs/canonical-schema/run-rotation/scaling-the-hadoop-indigo-cluster).
	- see DSCore's signalfx [dashboard](https://hubble.corp.stripe.com/viz/dashboards/22199-cluster-utilization).
- 


## 2023-08-11
### Meeting regarding deleting low ROI jobs
Avinash: Hey folks, sorry had to jump of for another meeting. Capturing my 3 asks here  
1. Continue building out a plan for sustainably tracking the usage metrics to build a good data lifestyle roadmap. Please work with efficiency and the Data lake team to build this.
2. Short term analysis on total opportunity size (not just the leaf node but recursively go up the chain)
3. Lets collaborate with the CATS team wherever possible to ensure there is one Stripe Analysis being done instead of multiple ones. I am curious to know what i the analysis the Cats team is doing and what are their findings.

## 2023-08-09
Understand Hive Metastore, data registry, airflow task outputs, annotated inventory
- Looks like Kevin Wang used hive.tbls, hive.table_params to identify orphan iceberg tables and applied proper lifecycle policies. [shipped](https://groups.google.com/a/stripe.com/g/shipped/c/ZB3e3V3WSQU/m/gDJLm1D9AwAJ).
- Looks like the tables hive.dbs, hive.sds, hive.tbls, hive.table_params were exported to Trino in [2021](https://groups.google.com/a/stripe.com/g/shipped/c/nC21m81nl_E/m/KXQzWaahBAAJ).

Meeting with Joey
- What's wrong with non-iceberg, non-presto import datasets.You mentioned that some Parquet datasets are not declared in data registry. How bad is this, at what scale? 
- Usage cost
	- Mongo snapshots is attributed partially. Owned by data movement team. We attribute cost to read usage. They own 100s of snapshots.
- What are all the current source of truth and what's missing?
	- hive metasta dump, dashboard query log, etc?
- [Data Privacy](https://docs.google.com/document/d/1xeS_b6lqyZxHo6bIt6wi0B8JPLZm_qPFQheZn-k2v6Q/edit#heading=h.lnqfcyy21mit)
- redshiftdb.queries  records all Hubble queries. redshiftdb.query_stats.
	- See `queryattributionmetadata` column. It contains metadata like query invoker (e.g. dashboard), dashboard ID
- prestodb.query_stats
- The hubble query hash instrumented in S3 access log can lead us back to the impressions.
- indirection of query ID through a view. It's not a problem if we have the query ID/hash propagated to S3 access log.
- Trino Views: 
	- We don't access the underlying Iceberg table directly.
	- vs Presto imports? The presto imports will make a copy of data. Where Trino view is a view.
- What else need to instrument:
	- PyTask
	- Databricks.
- airflow.task_output
	- It has daily dump, so we can detect deleted jobs
	- This is a low hanging fruit to detect. We already have this code somewhere, as it is recorded in PR for deleting a Airflow task.
- Fine grained data registry. Where is the data registry table in Iceberg?
	- See data_registry.s3_datasets
	- Data Privacy is also blocked on this. They need to set property on dataset level (eg. PII).
	- Ideally the Parquet datasets will be migrated to Iceberg. Joey does not know the current state of it.
	- How many datasets are missing in data registry for Parquet dataset? See query https://hubble.corp.stripe.com/queries/joey/bee2de08 Only 4031 datasets are correct in data registry, although the data size wise its about the same.


## 2023-08-08
Meeting with Habib (Mid-Year Perf Review)
- Drive clarity
- 

## 2023-08-07

Meeting with Dmitry
- Your impression of low ROI spark job deletion?
	- Complex. Lots of confusion to understand what's possible, what's not.
	- People want to have more clarity. If we can't do it now, how do we do it in the future. 
	- 
- Automate capacity management: 6 weeks for me, 1 week for Vein, 1 week for Dmitry
	- KR: understand how other companies are doing that. Maybe worth reaching out to Netflix and Uber. See if there are common ways, or custom solutions.
	- KR1. we understand how peer-companies manage UX, capacity and entry points (Uber, linkedin, netflix, airbnb) (2 weeks) KR2. Autoscaling design is gaveled KR3 queless/clusterless spark design is gaveled
	- Q4:
		- Ideally, we don't need to manually scale up and downs. Users can change capacity without PRs (still PR for change queues). We need to discuss with efficiency team.
		- Example: ad hoc sapphire is working well, we may not need to build total new systems and processes. Vein may be the most familiar person but probably 
- Launch API: custom scheduling by the expected data landing time.
	- There are some Yarn schedulers that may be able to afford that.
	- Dmitry: I don't think we need to route jobs between queues.
	
## 2023-08-06

Deleting Low ROI Spark Jobs Data Analysis
- July datasets, all reads and writes in July 2023
	- S3 datasets
		- dataset list: `usertables.yichen_s3_datasets`
		- reads: `usertables.yichen_s3_reads`
	- Iceberg
		- datasets (including creation Spark job): `usertables.yichen_iceberg_datasets`
		- reads: `usertables.yichen_iceberg_reads`
		- Mapping from iceberg_sha to iceberg table_name:  `iceberg.cash_and_transaction_speed.iceberg_datasets` (table_name, iceberg_sha)
		- To determine leaf-level dataset, make sure the task has no downstream, check airflow.updatream_dependencies
		- Map from task to cost: `usertables.joey_airflow_costs` (this is not an iceberg table)
		- The opportunities per node (without thinking about leaf node) is now in the table `usertables.yichen_iceberg_opportunities`
		- 
		- CURRENT STATUS: 
			- Note that there are many tasks that generates multiple datasets, so the spark cost is duplicated in this table: https://hubble.corp.stripe.com/queries/yichen/57c0e95a
		- 
- 

## 2023-08-03

Learn from [Sequins Repartitioner migration to Spark shipmail ](https://groups.google.com/a/stripe.com/g/foundation-shipped/c/ZrOoX-E6k5s/m/NL2njc1fAAAJ)
- Sequins is a high performance read-only key-value store. Batch jobs generate datasets and update them to S3, then query individual keys in realtime from Sequins.
- Teams run this job as part of their own Airflow dags. We see 3-4k distinct instances of the repartitioner job run every week.
- Minimally-invasive translate of the job from Scalding to Spark. Problem: scalding job didn't have any integration tests. Solution: generate a number of "golden tests" with known-valid inputs and outputs, run Scaling and Spark version side by side, writing to different locations, and compare. But, the output are not identical due to random identifiers. We have to write equivalence-checker that computes an order-insensitive checksum of the records in a given partition.
- To avoid the risk of multi-hour rollback, we built tooling to allow dynamically switching which version of a dataset is active. Sequins management plane now supports a config-srv powered per-dataset configuration which controls which version of the dataset should be served. This allows us to incrementally switch datasets from the legacy output to Spark output on our own schedule.

## 2023-08-02


Meeting with Joey
- `https://hubble.corp.stripe.com/queries/joey/88b51218`
	- shows the parquet dataset prefix pattern.
	- SAL output considered consistent prefix format.
- `iceberg.cash_and_transaction_speed.iceberg_datasets
	- Interesting columns: table_name, size, in_s3, iceberg_sha, in_hive, last_ddl_time, in_dataset_registry, in_cost_graph, cost_last_month
	- Question: where to find Spark cost to generate that cost?
	- in_hive: to gain context about the table. Similarly, for in_dataset_registery and in_cost_graph.
	- The cost here is true cost.
- `iceberg.cash_and_transaction_speed.iceberg_s3_access`
	- Interesting columns:
		- iceberg_sha
		- workload_type (airflow, service)
		- workload_task (iceberg.DataFilesJob6, airflow, iceberg.ExpireSnapshots, archiver.GroupedDailyArchiverForPayserver)
		- operation (REST.GET.OBJECT)
		- total_requests
		- max_hour
		- day
- Vast majority (2/3) of data from Stripe are parquet dataset. They are also generated by Spark jobs. When you define a dataset with SAL. 
	- Presto import S3 prefix mimic source path.
	- Presto imports both iceberg and parquet datasets.
- `iceberg.cash_and_transaction_speed.s3_datasets`
	- Interesting columns: bucket, dataset_prefix, size, approx_cost, hive__last_ddl_time, dataset_registry_owner, last_modified_date, hive__table_name
	- many columns show cost $0
	- approx_cost: it is approximated. It is not true cost. A&A team only attribute cost defined in data registry. We look at S3 inventory, using accurate size to attribute the cost. It is good enough for measure cost with no transfer cost. That is, this column does not include S3 data transfer cost.
- `iceberg.cash_and_transaction_speed.s3_dataset_usage`
	- Interesting columns
		- i
- `iceberg.cash_and_transaction_speed.dataset_usage_from_trino`
	- Interesting columns: 
		- queried_table
		- query_id
		- query_username (service_treasury_admin, service_close_tracker, floriansanz)
		- principal_user
		- query_time
		- service (hubble)
		- host_type (eg. airflow)
		- query_invoker (dashboard, query-box)
	- What is "query-box" query_invoker?
	- It is possible this table is not complete, compared to S3 access log.
	- DEFAULT locality view, will be registered in S3 access. But in Trino, you won't know it is an underlying iceberg table.
	- 
- `iceberg.cash_and_transaction_speed.iceberg_s3_access`
	- 
- In S3_datasets, some prefix starts with `/presto`. Is all presto datasets stored under this prefix? Let's say somebody do an presto exports, either snapshot or incremental. Are the output all sstored under /presto as a S3_datasets?
	- Yes presto imports are all under /presto prefix.
- Where is the Hubble queries goes to in S3 log. Let's say somebody query Iceberg or Trino in Hubble. Iceberg queries will access the S3 icebreg_warehouse prefix.
	- Yes if the query is against the Trino view of Iceberg table, the access log will go to /presto prefix.
- PrestoImport, it drops the /presto prefix.
- What about PyTasks? 
	- We can't tell the difference between a SAL or Pytask from S3 access header.
- The airflow sensors usually poke the _SUCCESS file.
- cost-graph has job/task level cost. The current mapping from task to spark cost is still the same usertable.
- It is difficult to solve the indirection. See when you query a view (e.g. Locality default) in hubble, you can only see that in S3 access log. It is not captured anywhere else.
- The leaf level S3 cost, $7k/m for iceberg, and $70k/m for non-iceberg. How do you get this number? Do you use the last_modified_date column?
- Given a airflow task, how is its cost calculated? I believe the cost-graphy only have queue level attribution? How do you connect an airflow task with the monthly cost?
	- This is the no-code [pipeline](https://hubble.corp.stripe.com/viz/pipelines/edit?pipelineId=e3f09022-a212-4df3-92ce-1b5776a11223&type=prod) to generate the [Spark cost](usertables.joey_sparok_costs) data.
- How do I exclude non-business queries like checker script? What are other things to exclude?
	- We can't tell the difference between traffic from checker, dashboard auto refresh, and human 
- How to deal with tasks generating multiple datasets, like archiver?


Meeting with Habib

- what percentage of access is iceberg data, and what percentage is non-iceberg.
- From there, given a day, what percentage of iceberg and non-iceberg access.
- The next thing is, of iceberg datasets, how many leaf nodes, how many of them not accessed in a period of 1 week, 2 weeks, a month. We need to figure out how the access pattern work. Is there something in hadoop library that we also reads 
- Do we have a mapping from ip address HLM may have it.
- I expected more progress. We need a quick and dirty system. Can we build a framework we can leverage. 
- If Joey is doing great, we need to convince our leadership that Joey is doing the right thing. They are a, b, c, d, e etc. We need to provide that level of clarity. We only know that they are doing it, but we don't know if they are doing the right thing.
- Focus on methodothly and goals first. 
- To begin with, we have confidence on the removing leaves cost, that will help build confidence.
	- Let's review with Patric and Mike with the methodology with leaf nodes.
	- Then the size of non-leaf jobs and data.
	- Send a query PR and ask for feedback from Patric and Mike (I want eyes on this and make sure my methodology is right)
	- The goal of this exercise (code review PR for methodology):
		- It is important for clarity. The goal
		- 

## 2023-08-01

Meeting with Yashiyah @sylvester
- HoneyComb
	- Outcome: we have something like go/spark-jvm running on honeycomb. 
	- Plugin or event log for more instrumentations and tracing: 
		- Probably plugin.
	- opentelemetry: the OSS version is banned at Stripe. Need to change something in bazzle. 
- Efficiency
	- Can we claim the unused resources in a queue?
		- Indigo: higher queue utilization.
			- https://hadoop-indigo-resourcemanager.corp.stripe.com/cluster/scheduler
	- Can RM automatically use unused resources in reserved queues?
		- 

Meeting about Deleting Low ROI Jobs and Data (Dmitry, Patrick, Habib, Mike)
- Next step, be crystal clear about what Joey is building.
- Explicitly calling out what dataset we need with Joey, that can help us answer the question of "understand the opportunity to decide if we want to continue investigating".


## 2023-07-27
Meeting with Sesh
- Regarding Honeycomb, observability, should talk to [@mcowgill](https://stripe.slack.com/team/U036VJKMFSL) - Observability Monitoring. His team owns prometheus infrastructure.

Meeting with Zhen Yu
- Already have plan to deprecate Blueberry.
- Blueberry is charged at a lower rate. 
- Planning to move Blueberry into a queue in Indigo, with low reserved resource, but larger burst resource. Mainly to move jobs not compatible with graviton to Indigo.
- We have talked about mage clusters before.
- [Graviton dashboard](https://hubble.corp.stripe.com/viz/dashboards/31686--hadoop-graviton-migration)
- [Blueberry clean up plan](https://docs.google.com/document/d/1ypiS5IdxJHxcqm1umaEjpT1jDIS0_b5nBzKlnmCPwfs/edit)

## 2023-07-25

Meeting with Airbnb
- Airbnb: migrating from Spark 2.4 to Spark 3. 
	- Scala version upgrade. Library version upgrade.
	- Stripe: we use bazle.
- What kind of benefits you get from EMR?
	- reduction operational load
- Airbnb: should we stay on EMR, or come off, or k8s.
- Dynamic routing: punt autoscaling and use available resources.
	- We leverage routing mainly for adhoc jobs, not for scheduled jobs.
- What efficiency projects have helped you?
	- Swap incident types using gp3 (replace gp2)
	- Do you need to be on i3/i5? Airbnb: we use m5.
- Disaggregated storage
- AQE at Airbnb
	- Used in minerva, ingestion, etc.
	- In the past tuning configuration may not scale. AQE helps changing the query plan dynamically, especially partition coalesce. Sometimes we see 40% improvements. 
	- We are prioritizing Spark 3 adoption first.
	- https://medium.com/airbnb-engineering/upgrading-data-warehouse-infrastructure-at-airbnb-a4e18f09b6d5
- Are you thinking about Spark Connect?
	- Tom Gianos: databricks is hand-wavy. You still need an orchestration layer. There are many different ways to run spark, Spark Connect is one of them. We are thinking about an abstraction layer. For example, Jupyter. A way to decouple user expectation and underlying infrastructure. 
- CapacityScheduler vs. FairScheduler
	- Jian: we switched to CapacityScheduler because it is easier to set priorities.
- Spark job, client mode vs. cluster mode
	- We use client mode to avoid zombie jobs in cluster mode.
- Converging Spark and Flink, k8s
	- Tom: feel like the right thing to do, but the community hasn't converge on many subjects, e.g remote shuffle, manage queues. It's hard to go all in at the moment. Netflix attempted it. Apple has gone in. The infra team liked it, the user team (from apple) doesn't like it. Among other priorities we are not pursuing it now.

## 2023-07-24

Meeting with @yibojiao Yibo Jiao
- dis-aggregated shuffle, **David Corbo**. This can help auto-scaling of Hadoop.
- DP did auto-scaling over weekends in 2020, Jon Bender 
- Doppler to run small tasks on spot instances, hadoop-spot. Can we move short jobs (just a few minutes) on to Doppler. 
- Why deprecate spot? Because datasets are not iceberg. Now most tables are iceberg, no need for hadoop-spot.
  
## 2023-07-21


Understanding what exactly we will get out of HLMv2
- Larger scope thread from 24 days ago: https://stripe.slack.com/archives/C7WFBDACC/p1687907053680249
	- https://jira.corp.stripe.com/browse/DEP-4435
	- list of paint points with HMLv1: https://docs.google.com/document/d/12tQWib2mLjfC0xPNF8bLuNNrHZIFtScU7c6-vfl98qA/edit#heading=h.7c91d2de7ac4
	- Problems
		- Lose capacity because HLMv1 batching will make a large number of nodes not available for RM but during the long wait, new nodes are booted up. Can we boot up new nodes before terminating? 
			- @jzhou: HLMv2 will support [Launch-before-Terminate](https://groups.google.com/a/stripe.com/g/compute-shipped/c/sVll6ln-WpI).
		- Time-based decommissioning instead of percentage based. We want to use a time-based heuristics to be able to consider what hosts to decomission to cover SOX hosts.
		- asg sync on github merge
			- @jbrown: Infra Platform is migrating ASGs to SPICE
	- Spice ASG migration may solve some of the Vein's ask
	- Vein ask: pain points of scale up and downs with asg yaml file through git then asg sync. 
	- @jzhou recommend autoscale-srv or auto scaling groups ([shipped](https://groups.google.com/a/stripe.com/g/foundation-shipped/c/A3LpjTEUTTc)). Also mentioned [dynamic scaling](https://groups.google.com/a/stripe.com/g/dev-productivity-shipped/c/c1Z9nKWXaFU).

Meeting with Richard
- Trying to figure out putting on a pause on usage because its getting more expensive.
- Hourly job , data freshness company initiative. Real time datasets is talking about data freshness.
- Meeting with Tony, big projects keep failing. Eg. Caribou. 

Meeting with Vein (@vkong)
- This [doc](https://docs.google.com/document/d/12tQWib2mLjfC0xPNF8bLuNNrHZIFtScU7c6-vfl98qA/edit#heading=h.kxnpk29wt4ic) kind of kicked off the conversation about my KR of automatic capacity management
- This conversation started when I was on vacation with Dmitry
- AWS (insufficient capacity) error `Server.InsufficientInstanceCapacity`. See https://hubble.corp.stripe.com/viz/dashboards/21034--data-platform-ops-review?subTab=%5Bignore%5D+ec2+availability&tab=Batch+Compute
	- It is getting better.
	- When we see this error, we should start creating OCDR automatically (work with efficiency, because if we give up the nodes, we won't get them back because of HLM.


Meeting with Alex (@ar)
- I've talked to Habib
- In last Q4 and this Q1, we abandoned and put on hold in efficiency related projects within the A&A team. It is because we didn't reach the efficiency goal we anticipated, and then there is a re-org, so we start to focus more on storage side of things.
	- We were focusing on unused data, look at the data first, and delete them, and delete the jobs that produce them. We didn’t come to the stage of deleting jobs of this project. We found the unused data, but the naming seem to be important, and we are not comfortable deleting them, so we ended up pushing them to cheaper storage instead. 
	- We created a dashboard to identify the opportunities. [https://hubble.corp.stripe.com/viz/dashboards/29802-s3-efficiency?tab=Unused+S3+Data+by+Team&team=batch-compute](https://hubble.corp.stripe.com/viz/dashboards/29802-s3-efficiency?tab=Unused+S3+Data+by+Team&team=batch-compute)
	- The next step is to find the jobs that is writing to these data set.
	- Jon Bender was the person who was working on this.
- Instead of continuing efficiency projects, we instead are addressing the data ownership right now, with privacy engineering team. We burned our fingers by deleting user’s data which triggered incidents.
	- We are building data catalog (POC in Q3, more in Q4), give teams opportunity to identify SLA. SLA as the measure of ROI.
	- We have deprioritize the efficiency job. We’ve tried manual leg work, we don’t get back much return, those asks become low priority on user.
	- My senior staff  Emili ([@emil](https://stripe.slack.com/team/U042HP3QL5C) and [@dannylane](https://stripe.slack.com/team/U02306RDZ8B)) is aware of column level lineage, based on schema and jobs. Regularly reporting requires that.
- TODO: find docs related to prior projects and share them with me by next Monday.


## 2023-07-18


Meeting with Habib
- TODO: write a document about future vision of Spark infrastructure.

Meeting with Dmitry

- Follow up with FM about HLMv2 immediately
- We use read ahead buffer too small for shuffle
- Our main objective is to find cluster of things nobody care about.
- We need to identify unused spark jobs and datasets to delete sooner than later
- What observability we need to build. Do we have an observability gap? 
- We can do more sampling, and trace and see what looks like.
- Removing unused job is high leverage.
- Short-term question to answer: 
	- How many potential user work flows can be removed.
	- That is, optimization configuration is not as important.

2023-07-17


Meeting with Patrick
- CPT - cost per transaction, marginal cost per transaction.    
- My lens: first step is to measure and understand
- I talked to Habib.
- For batcom: it is important to know how to save cost.
- We need to understand if it is possible to achieve similar result with what Mongo did (deletion to save)
- December, $86m/year, now, $30m/year, and another 20% in H2. This is an astonishing, such much low hanging fruit. You can’t hope to drop 70% in cost (like in Mongo).
- Finding: if you just push a little bit, you can find a large amount of cost saving. Few comes from [usage consumption](https://hubble.corp.stripe.com/queries/eugen/fa3584f5/barchart). 
- Savings come from matching workload with scale, not keeping too much backup, 
- What’s needed for batcom: accounting these sort of thing (low hanging fruit, without impact.) Where are we spending money today and what’s the value we are getting for that money? Are those job delivery businessing value? Are those queues well-utilized? Where do we need observability to help understand this

**

Meeting with Mike

- types of cost for efficiencity:
1. [batcome]Single job level optimization (compression, configuration etc)
2. [a&a] Deprecating low ROI jobs and data (require understanding how data are being used, lineage). Patrick explode in kafka side
3. [archana] Incremental data (finding things that being used in a snapshot way instead of incremental way)

Suggestion:
- Put together a really clear high-level framework explaining hadoop cost, what opportunities, and initiatives to staff. I can meet you more on how to structure this.
- Solve the problem that attribution cannot solve, build instrumentation for Spark to really understand data lineage, and come up with a plan.
- Nobody have answer this question: which spark job is reading what tables. In theory, 
- Have A&A done any analysis?
    

Find the table in iceberg that A&A maintain (s3 access log), find mapping s3 prefix and airflow task mapping, identify which iceberg tables are not accessed at all or low. [Joey Pereira](mailto:joey@stripe.com) Identify Spark jobs**

2023-07-11

Reflection:
- What I did with the incident?
	- I followed up the investigation, mainly contributing as an IC.
	- I came up with a query, which is still a good IC work.
	- I asked if Shahyar needed help.
	- I asked if we should re-open the incident with Fleet Management.
- What I didn't do?
	- Ask: who is doing what? Is Helen or Shahryar doing RCA?
	- Ask: what is the impact?
	- Move on after the incident is mediated, and let the current owner to drive the next steps.
- Me doing IC level of work, for example, root cause analysis, is not important. What's important?
	- Drive the investigation. Knowing who is doing what at any moment.
	- Ask questions. Think about what questions Gaurav and Habib would ask.
		- What's 

Meeting with Habib #meeting/habib
- I am not satisfied with how you handled the incident ir-octagon-whirl.
	- You did analysis, but the team is looking for you to provide leadership. You need to take control. 
	- Gaurav was the one driving this incident, and he is not even in the team.
	- I'd like to see more impact, more judgement.
	- For data deletion and capacity management, they are potential high impact projects. I don't want to be involved. You should be able to do handle everything.
- Ted Gooch may reach out to me about data 
- Feel free to give Shahryar: decom regression, he should know the risks (what we don't know) before roll-out.
- [@neerajjoshi](https://stripe.slack.com/team/U01TW7X2WJJ) is the Mongo TL

Meeting with Avinash #meeting/avinash
- Mongo from 90mil to 20mil. First millions by deleting. So highest opportunity is can we find things that we can delete, and we make sure we went through this exercise. It will be very bad if we prioritize large engineering effort when somebody ask if we have    
- Data life cycle TPM: Joyce Xu [https://home.corp.stripe.com/people/joxu](https://home.corp.stripe.com/people/joxu)
- Where to find QBR regarding Mongodb deletion [https://docs.google.com/document/d/1fb265ZVvcaLGPJAIawZ6-pkDTqwRpaInqEUfoLm64nQ/edit](https://docs.google.com/document/d/1fb265ZVvcaLGPJAIawZ6-pkDTqwRpaInqEUfoLm64nQ/edit)**




2023-07-05
TODO:
- 
- Can I find low ROI from s3? See https://viz.corp.stripe.com/efficiency/solis?pageType=consumer&team=%5B%22batch-compute%22%5D&tab=drill&env=&activeTab=consumer&platform=s3&breakdownPivot=byUsageType&resource=s3-stripe-data&invisible=denormalized.gatewayconversations_raw.backingstore_default

Done:
- [S3 form](https://docs.google.com/document/d/17z-P5BDJtHUGYsoV3P6TWwmvgv_KlbafXvLqE35ey34/edit) Looks like I can edit my response

- [Tokenizing Data Access in Spark jobs](https://docs.google.com/document/d/1sTknk5PLMfGcJiIa9a3FF_TDvYcoBTgiy8_j4rgyxUY/edit#heading=h.tuyiytrmleu)
	- Related batcom [question](https://confluence.corp.stripe.com/display/BATCOM/questions/715949496/please-edit-can-someone-share-the-roadmap-around-secrets-support-for-spark) and also [this one](https://confluence.corp.stripe.com/display/BATCOM/questions/583140217/using-secrets-in-a-spark-app) answered by Dmitry.
	- Related [shipmail](shipmail regarding [fake data generation.](https://groups.google.com/a/stripe.com/g/dev-productivity-shipped/c/dxwLqWMDGhE/m/BmVMjyL6AwAJ))
	- Does it mean we are only concerning reading from Spark? Looks like it: `by making tokenized data recoverable in data land.`
	- What's the experience for Spark infra?
		- Looks like we need new access control. May require a distinction for manually invoked jobs and checked in jobs. For manual jobs, use the metadata about the team that is running the job to do access control. For jobs in prod (scheduled jobs), we opt to not do additional access control.
	- What's the experience for Spark users?
		- How users opt-in?
	- Purpose: how tokenized sensitive data can be made available to Spark jobs and Trino queries.
	- What is the `Tokenization Library` do, and how is it being used today?
		- See [doc on trailhead](https://trailhead.corp.stripe.com/docs/tokenization/getting-started/using-the-tokenization-library).
	- What is `privacy-tokenizer`?
		- Looks like it is an independent service running on horizon. 
	- What's prior-art MTS?
		- MTS stands for mainland token service.
	- What are the 3 potential approaches?
		- Distribute secrets to Spark and write UDFs that depends on the `Tokenization Library`.
		- Make RPC calls to `privacy-tokenizer` in UDF on each row of data.
		- Create a method that is invoked by other jobs and handle batch calls to `privacy-tokenizer`
	- What's the proposed approach?
		- Recommended approach is (3) above, and (1) as the last resort.
	- Questions:
		- Perf impact: looks like UDFs need to flatten the nested data structure before it can pass it to UDFS. This flattening process adds overhead.
		- For the use case when you make the tokenized data accessible for ML/DS use cases, why they need to use this tokenizer? Does any users have access to the original data without using the detokenizer? If so, why can't we just give the ML/DS users the same permission with those users?
		- Currently there are two services creating tokens so the amount of data actually being tokenized (and need to be detokenized) is small today. Does that mean for these two services, there are no "original raw data" stored in dataland and all users need a way to access them? Can't we add the detokenizer at the data ingestion layer?


2023-06-27
#### DP Q3 QBR
- Rahul Patil
	- I'd like to learn more about the "incremental processing" in the learning section.
	- Intuitively incremental processing is better than processing the world. I've love to learn why an intuitively true understanding does not result in actual improvements.
	- Real-time is better. Any learnings from this space?
	- Regarding moving docs to trailhead, do we know how it is affecting users, how to measure it.
	- Anybody felt that the Hubble ownership is sufficiently addressed? 
		- Derek: I think Hubble means different things to different people. Some folks think Hubble is the dataland. 
	- Is the Zookeeper issue resolved? What is the resolution?
	- Anybody else that have questions for this group?
	- I appreciate the learnings from each project. We should operate like a scientist, keep learning, learning result in happiness, but that is not important: happiness is overrated.
- Meeting with Gaurav
	- What's your opinion about the incremental processing? Is it stopped? Were you surprised?
	- What's real-time dataset? What's the significance for real-time processing?
	- What's flink-as-a-service?
	- My take on capacity management: it is not toilsome if you upscale with enough headspace.
		- Our users's SLA are more aggressive.
		- The need for capacity management is to stay in SLAs.
		- Maybe auto scaling can help.
		- apricot is the only auto-scaling we have now based on time. There are saving plan and autoscaling does not make much sense. It may make sense to do auto scaling not for efficiency but for toil reduction.
		- Can we reduce the toil about PR and tickets, build some automation around it.
		- Can we further automate it that the user don't need to create those scale up and down requests?
		- Queue-less: instead of thinking about queue, think about criticalness and landing time.
		- It is important to define what's good enough.
		- Airflow SLA mainly to allow user to generate an alert.
		- A source of toil: user create a queue, merge the queue, go through cost, then another PR for capacity in the queue.
		- Capacity Scheduler vs. FairScheduler? The only place to use capacity scheduler is in sapphire. I don't know the choice of schedule affect our capacity management. Maybe Helen knows more.
- Meeting with Habib
	- Any information to share about the batch compute roadmap discussions?
	- There is a batch development user workflow item under the data productivity section in the QBR. Who is driving this effort? How does it involve batcom?
	- A lot of opportunity for efficiency? Hadoop and Mongo. Two areas you can help:
		- Capacity management, we have a KR. Auto-scaling. You completely own that (e.g. drive a shared KR with the data science). The goal is to have a proper design by the end of this quarter.
		- Immediate: is there opportunity for identify the jobs? Try to find a very pointed answer. Is there an opportunity? How large is the opportunity? Involve Patrick McBryde since he was the DRI for data retention. The goal is to get a quick answer in 2-3 weeks.
	- Operational: I am relying on you for the operation to be smooth. You are on top of the operation (and other staff engineers). How do we address the operational issues? I'd like you to keep your eyes on the ball of operation.
	- PySpark alignment: Rahul is driving the alignment on PySpark, for solid recommendation. We can delay/deprioritize the investigation Spark/PySpark centered 
- Meeting with Dmitry
	- How to get the people involved with contribution?
		- Think about the users needs, their users?
		- We as infra providers, we are interested in providing tools for all users. This is one of the opportunity to reduce cost.
		- Efficiency owns solis, cost graph.
		- The outcome we are looking for is that how much opportunity of improvement, by finding specific datasets and pipeline to remove. X weeks of investment to get Y million dollars of savings. To understand the size and cost of this opportunity. A quick and dirty data collection, with a specific proposal to include in OKR.
		- There is no existing OKR/KR, the goal is to get the size and cost of the opportunity, and it may turn into a future KR.
		- What other datasets/tools that will be helpful?
			- `recursive_dependencies` in `airflow.tasks`
		- What's your context with Engue?
			- Attribute cost recursively.
			- Propagate cost recursively.
			- Solis does cost attribution on one layer. 
2023-06-22
- Understand Great Expectations
	- [Jeff Wang's doc](https://docs.google.com/document/d/1z4r05zT5KCgobYHJs3XZgrdWF5ch6rOGYQACRQsnrGM/edit#heading=h.pfo0k1txy0cw)
		- 2023 Q2: directionally aligned that Great Expectations is useful but low priority.
		- GE is a python based data quality framework for building dataset validations.
		- PySpark is the only unmet dependency (how does it depends on PySpark?)
		- Proposal: connection to a datasource using YML, building an Expectation Suite using YAML, and running validations through a Checkpoint.

2023-06-21
- [Dataset deletion ](https://stripe.slack.com/archives/C01G6NYRNBH/p1686582250641099)
	- Yi's understanding
		- Yi: looks like the idea is to figure out a system and process to depreciate dataland artifacts, including both datasets and data jobs. The datasets may involve iceberg tables, S3 datasets, and trino tables. The jobs involve airflow tasks and their underlying jobs (e.g. Spark jobs).
		- Consider this a GC issue, how to "mark" the items?
			- @joey is using S3 access log to tell if a dataset is used or not. He calls for a better way, a measure of "utilization" for jobs because S3 access log may not be accurate becaues they may be "used" by other legacy code. In GC world, we need a way to mark those legacy code as well.
		- Who should be driving this? Looks like Dmitry has discussed with Eugen from cost team, so likely the DRI should be between cost and DP, but shouldn't 
	- The ask: deprecation has looked like once-a-half adhoc, one-time purges of low-hanging fruit in the spirit of fighting tech-debt. I’m curious if anyone has found a successful way to manage the sprawl, ideally an ongoing, automated process of detecting and managing unused datasets.
	- Ideas
		- juliannadeau: I'd rather it just have an "expiration registry" that I can click a button and re-verify, after being spammed with automated tickets. And not delete right away but pause and wait n months (to avoid unnecessary backfill)
		- rfleisher: I was spitballing some sort of process that given some heuristics (ie, threshold of # queries made against table, last query date, N job failures in M weeks, etc) to generate a report with who queried the data last and maybe some metadata around the job itself to give us a head start on plotting out deprecation. and maybe with enough confidence / cycles of this we can more strictly automate the killing of airflow tasks / revoking access of datasets.
		- jeffwang: [doc](https://docs.google.com/document/d/17APlQiIyKOaLVXVaHrFIpsjFDO9Sn1pV1ipmULauPv0/edit#heading=h.v44acomd8rmt). not prioritized
			- Propose: periodic review of some data pipelines, verify ownership, disable unused jobs, affirm IDL and SOX. Unreviewed pipeline will be disabled or automatically escalated.
			- Pain Points
				- Stripe does not have any ongoing systematic processes for reviewing the cost of a data pipeline.
				- Cost of a data job is not easily surfaced, raising the barrier to action.
				- Teams have poor visibility into which jobs they own.
			- Proposal
				- Period review considers the selection criteria to avoid friction to users, by defining rigor levels.
				- Affirm ownership of the pipeline
		- joey: 
			- I was also independently putting together many of those stats to dig into jobs across all of dataland, as [@akshay](https://stripe.slack.com/team/U0AAPFW4T) & I started to poke at a variety of efficiency wins in dataland. Right now the main metric we've been sifting through is S3 data access as a "used" or "unused" metric, and we haven't spent too much time on collecting other things - soon!What I've wanted is spot on to what you said - an measure of "utilization" for jobs so we can find not just unused ones but those which are not necessarily worth the cost. Things like tables that may be getting accidental hits from other legacy code. (The worse offender I found was a checker that just booped a table which cost 200k/mo, made it look used, and put it in the expensive S3 tier!!)
			- As I see it, the S3 access metrics are the "go/no-go" for whether or not it's unused or not. The remainder is just provenance to help identify any usages, either for chasing them down or making an informed decision about deprecations (or reducing job cadence frequency re: the cost vs benefit argument).
			- To add on to the point about missing the upstream costs, it is very difficult to look at costs associated with jobs at all! As an operator, I can't sort jobs by cost because I can (1) look at compute costs, or (2) look at _some_ storage costs. The storage costs are very often incomplete because the data is pretty low quality - S3 datasets are often top-level prefixes, we've previously missed related outputs (e.g. Sequins intermediates). It's not possible see that, as well as any other closely related costs (Sequins compute, Presto import, etc.).I had a table to try to surface that holistic view of pipeline costs, but it's built on a pile of my usertables that has gaps in results (eg: unidentified Airflow output, so on) [https://hubble.corp.stripe.com/queries/joey/076600de](https://hubble.corp.stripe.com/queries/joey/076600de) I haven't touched this in a few weeks, but we're probably going to iterate on it more as a guide for actual pipeline costs
			- there's about a dozen different tables behind the scenes to stitch together various parts, but a majority of those are collecting stats about Iceberg datasets and non-Iceberg S3 datasets from places (S3, Hive, DataRegistry, cost graph). The Hubble pipelines page is also pretty hard to search but you might be able to lookup `usertables.joey_` to find them. e.g. the pipeline for that job:
			- The key tables for the datasets are:  
				- `usertables.joey_s3_datasets_tiering_flattened` - [pipeline](https://hubble.corp.stripe.com/viz/pipelines/edit?pipelineId=02e6d17a-9f51-4bfc-9b94-76bf641fdd67&type=prod). I had a query from November that also pulled in data about any Trino tables (from Hive and/or `s3://.../presto/` data) but that's not in the pipeline yet.
				- `usertables.joey_iceberg_table_stats` - [pipeline](https://hubble.corp.stripe.com/viz/pipelines/edit?pipelineId=43d38367-1816-4263-b434-7286eeba52c8&type=prod), which has each of those data sources I mentioned squished together for any Iceberg tables. Most of the effort there is to actually correlate a table name to the S3 prefix/Iceberg SHA due to situations like orphaned tables (e.g. removed from code, not dropped)
		- borovsky: we would be happy to help move it forward. Perhaps we can do a quick and dirty evaluation of existing jobs in the next few weeks, so we can materialize some cost savings in the short term and evaluate the impact of implementing a governance process to prioritize as a longer-term solution? I’d be happy to schedule some time to brainstorm ideas (please use ) emoji if you want to participate), or let me know if you have any other preferences.
		- eugen: I would imagine we can have some sort of periodic review process. For example once a year, the system would ask owner teams if the resources are still needed/used. If not, they would be marked for deletion. I am thinking a process similar to periodic LDAP group permissions renewals but for various resources

2023-06-21
- [H2 OKRs](https://docs.google.com/spreadsheets/d/1juh7-Z9EQX9TWFtRQ4C1nV5YheAdndy6_1QUqgWsQ2w/edit#gid=1210356499) #batcom/2023h2
	- Batch Compute is under Data Infra
	- What's scheduled for Batch Compute in H2, in which quarter, and HC estimate?
		- Q3, 0.25 quarter, develop a process to continuously learn about users needs
			- introduce user support funnel for all inputs
			- create metrics to categorize and quantify user support in batcom ops review.
			- support metrics (time-to-respond)
		- Q3, 0.5 quarter, enable PySpark
			- major alpha blockers
			- Iceberg/SAL
		- Q3, 0.25 quarters, documentation
			- User facing docs in trailhead. Comms to users to use trailhead exclusively.
		- Q3, 0.25, Enable NRT metrics and detectors at app level
		- Q3, 1, Decouple hadoop storage and compute (Disagg)
			- KR: options are evaluated (RSS, Magnet, S3 shuffle plugin) and design gaveled. Depends on Spark 3.2, depends on efficiency team to commit 2 people
		- Q3: 1.33, Graviton migration
			- materialize $400k-6m/year in cost savings. Efficiency team commits 1 person
		- Q3: 0: Spark 3 migration.
		- Q3: 0.33: Spark AQE
		- Q3: 0.75: enable Spark 3.2+ to unblock DI, DEP-4222, and allow disagg evaluation for push based shuffle.
		- Q3: 0.67: Managed Spark: automatic capacity management
			- Understand how peer companies manage UX, capacity, and entry points
			- Autoscaling design is gaveled.
			- queless/clusterless spark design is gaveled
		- Q3: 0.42: ML: develop vision for ML workloads and a roadmap
			- Doc is gaveled with DP leadership and ML infra
		- Q3: no silent data corruptions
			- Plan for committer silent data corruption is gaveled
		- Q3: 0.42: operational excellence
			- Migrate batcom services to MSP
			- peoplefe
			- shaded-spark for apache-livy
			- decom scalding
		- 

2023-06-20
- Habib expectations for me in Q3:
	- KR1. we understand how peer-companies manage UX, capacity and entry points (Uber, linkedin, netflix, airbnb) (2 weeks)  
	- KR2. Autoscaling design is gaveled  
	- KR3 queless/clusterless spark design is gaveled
- Don't care about exact wording of these KR, but the plan is to figure out how to solve the capacity management problem at Stripe.
	- Can potentially leverage some data science magic (work with 1 ds who is interested in this)

2023-05-16
Lateral Join
- allows you to join a table to the results of a subquery. This subquery is evaluated for each row in the outer table, and the results are joined to the outer table.
- This can be useful for performing calculations on the outer table and then joining the results of the calculation back to the outer table.
- Lateral join is used to
	- calculate values for each row in a table.
	- joining a table to a list of values
	- joining a table to the results of a function
- Lateral join can be used in the FROM clause of a query. 
- Subquery can access the columns of the outer table.
- The results of the subquery are joined to the outer table row by row
- Performance depends on the size of tables involved. 
	- Left lateral joins can be more efficient than traditional joins when the tables are large and there are indexes on the columns that are being joined: optimizer can use the indexes to avoid scanning the entire table for each row in the outer table.
	- Left lateral joins can also be less efficient when the tables are small and there are no indexes on the columns being joined, because the optimizer may have to scan the entire table for each row in the outer table.


2023-05-10

Incident ir-distance-tangible
- RCA: https://docs.google.com/document/d/1pnIxhiGy7jYrYtZR-reQMyzqAad3HpNR6UxCqCube64/edit
- What is decom srv and how does it work?
	- It is responsible for decommissioning and recommissioning nodes with the RM and NN. 
	- There is a CLI for decom-srv, to manually invoke commands. Before CLI, use grpcurl.
	- Decom Srv has a scanner component (like a cron), which runs through the decommissioned hosts in the database, remove any hosts which no longer exist in the ASG (they have been actually terminated). 
- How to find the EC2 node history? For example adoopdatanodei--0f0823f3c543f8adb.
	- 

2023-05-05
TODO: write an email explaining the data loss issue, potential fixes, and risks of each fixes. Advise the next steps. Make sure to cover multiple risks (more than the case we saw) of the v2 FileOutputCommitter.


2023-05-04
- AAR expectations
	- Ask the following questions:
		- What was planned?
		- What actually happened?
		- Why did it happen?
		- What can we do next time?
		- Was this detected with our existing monitoring infrastructure? (ticket it if we need to add monitoring)
		- How could we have caught this issue sooner?
		- How could we have mitigated this faster?
		- How could we have prevented this category of issue?
	- Open the incident JIRA
	- Anything else 

2023-05-03

Fix incident ir-dinner-current
- [Tracking google doc](https://docs.google.com/document/d/1E-oNznv0pBx4UuY4j03jbyAA7H_J7-gBzWzi4ZGxQHM/edit#)
- FileOutputCommiter V2
	- Support speculative execution: multiple instances of a task can run, only the first task's output will be committed.
	- Fault tolerance by atomic renaming by HDFS: a temp directory for staging the output per task, and an atomic rename to commit the output files.
- MAPREDUCE-6275: Race condition in FileOutputCommitter V2 for user-specified task output subdirs.
	- If the outputs of reducers have directory structure with the same name, it may have roblems.  That is, the task output to an extra subdir instead of doing any renames. mkdirs does not throw exception if the directory exists.
- MAPREDUCE-7282: MR v2 commit algorithm should be depreciated and not the default
	- Won't fix.
		- [Jason's comment](https://issues.apache.org/jira/browse/MAPREDUCE-4815?focusedCommentId=14271115&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-14271115)
			- It is a better approach that doesn't use an alternate top-level directory.
	- The issue: v2 MR commit algorithm moves files from the task attempt dir into the dest dir on task commit, one by one, and this is not atomic
		- If a task commit fails partway and another task attempt commits, unless the filenames are exact same, the output of the first attempt may be included in the final result.
		- if a worker partitions partway through and later continue...
	- Both MR and Spark assumes that task commits are atomic.
- [Understanding the difference between committers](https://hadoop.apache.org/docs/current//hadoop-mapreduce-client/hadoop-mapreduce-client-core/manifest_committer_protocol.html)
	- mrv1: resilient to all forms of task failure, but slow when commiting the final aggregate output as it renames each newly created file to the correct place in the table one by one.
		- task commit: renaming per task
		- job commit: treewalk by dir, rename performance can be O(files)
	- mrv2: not considered safe because the output is visible when individual tasks commit, rather than being delayed until job commit.
		- task commit: files under task attempt dir are renamed one by one into destination directory.
		- job commit: simply write a \_SUCCESS file
	- Why v2 is not safe?
		- because task tempt files are renamed after task, it is possible that a task may fail (e.g. preemption) during commit, and some files have been written to destination. If the next attempt is writing different file names (the task output is not an exact match with first attempt), so the output may contain both tasks' output files.
	- What about StagingCommitter by Ryan Blue of Netflix?
		- Working dir of task attempt is the local filesystem.
	- S3A Committer
		- S3A offers an atomic way to create a file: the PUT request. The final POST request can be delayed until the job commit phase, even though the files are uploaded during task attempt.
	- Magic Commiter?
		- It a purely-S3A and take advantage of the fact that the authors could make changes within the file system client itself.
		- It needs S3 with consistency. It does not need HDFS or any other filesystem with rename()
	- S3A committer is considered correct.
		- Nothing is materialized until job commit.
- [Understanding S3A Committers](https://hadoop.apache.org/docs/r3.1.1/hadoop-aws/tools/hadoop-aws/committers.html)
	- Since Hadoop 3.1
	- S3's "multipart upload", allows S3 client to write data to S3 in multiple HTTP POST requests, only completing the write operation with a final POST to complete the upload. This final POST consisting of a short list of the etags of the uploaded blocks.
	- Algorithm
		- The individual tasks write their data to S3 as a POST within multipart uploads, yet do not issue the final POST to complete the upload.
		- The multipart uploads are committed in the job commit process.
	- Looks like it is improved in Spark 3.2
		- Magic S3 committer is easier to use, and recommended as default (unless users is using iceberg, delta, and hudi)
		- Spark 3.2 builds on top of Hadoop 3.3.1, which included bug fixes and perf improvements for the magic committer. 
		- https://issues.apache.org/jira/browse/SPARK-35383
	- S3 is strongly consistent since December 2020.
	- S3A committer can improve Spark performance, especially if a large portion of the Spark job is writing data to S3.  Some say 15-50% improvements for write intensive jobs.
	- There are three S3A comitters ([cloudera](https://docs.cloudera.com/HDPDocuments/HDP3/HDP-3.1.4/bk_cloud-data-access/content/s3-introducing-committers.html))
		- Directory Committer (directory staging committer)
		- Partitioned Committer (partition staging commiter, spark only)
		- Magic Committer
- What do Spark community think?
	- [SPARK-33019](https://issues.apache.org/jira/browse/SPARK-33019): use version=1 by default since Spark 3.0.2 and Spark 3.1.0
- Stripe looked at S3 Committers before. See [paper doc](https://paper.dropbox.com/doc/S3-Committer-Research--B3kcFXI~MU~IMNd1BBG1lUOJAg-KsnoiK7REaPJjA3dw5RJI)
	- According to @jonny, the S3 Committer, at the commit phase (the final POST command) has a brutal time-complexity. It will spin up a number of threads to commit thousands of files. If there are 10 threads for 100 files, the complexity is O(files/threads). He tried ways to increase the number of threads, but resulted in a bell curve. Not sure why threads can't be increased further. The final POST command may need to list all task files (100k files in the worst case)
	- This doc details Jonny's test for S3A committer: https://paper.dropbox.com/doc/Direct-Commit-To-S3-research--B3nAx7VYPsGQgTQrrLsF9hObAg-9WyAn0GFa0A21Bm0fuLE6
- What's the difference between the v1 and v2 of the FileOutputCommiter?
	- See [blog](http://www.openkb.info/2019/04/what-is-difference-between.html).
	- v1: the AM is responsible to commit the job. It will first need to wait for all the reducers to finish, and then use a single thread to merge the output files. The number of the output path is the number of the reducers for the job.
	- v2: the reducer is responsible for mergePath. Because there are multiple reducers working in parallel, it is much faster. 
- v1 FileOutputCommitter
	- Reducer will save output at the location `joboutput/_temporary/{appAttemptIdId}/_temporary/{taskAttemptId/`
	- When task is being committed, the dir was renamed to: `joboutput/_temporary/{appAttemptId}/{taskAttemptId/`
	- When job is being committed, AM waits for all reducers to finish, then all `taskAttemptId` subdirs got renamed to `joboutput/{taskAttemptId}`, and cleanup happens (delete `joboutput/_temporary`, and then a SUCCESS marker is written
- v2 FileOutputCommitter
	- Reducer will save output at the location `joboutput/_temporary/{appAttemptIdId}/_temporary/{taskAttemptId/`
	- When Reducer finished and ready to commit tasks, the rename happens to `joboutput/`
	- commitJob deletes `joboutput/_temporary` and writes SUCCESS marker.
- Potential Fixes
	- Since Spark 3.0 and 3.1, the default is set to version=1. See [PR](https://github.com/apache/spark/pull/29895).
	- Looks like Steve Loughran suggested to allow the Spark driver to trigger a failure (task failure or job failuer?)
Questions:
	- can we change the committer on bad jobs only?
	- Should we consider using **HDFSOutputCommitter** instead of FileOutputCommitter v2?
	- v2 fail mode is to have more files. Is this the right solution?
	- Should we consider S3A committer? 
	- What about StagingCommitter by Ryan Blue of Netflix?



Understeand Brian Tang's [Future of Training](https://docs.google.com/document/d/1-LFRyQvOaC8DvkYwAb-mS71GR_tIuzc58Z_j8xRO6HA/edit#)
- How did he go about writing this doc? He interviewed the users, come up with a meeting note for each user interview, and consolidate them into a main user pain points themes. He then come up with a proposal.
- What are the main themes of user pains for training?
	- velocity
		- itreation on railyard is slow, every change requires CI builds.
		- the path from notebook to production is not easy.
		- no autodeploy
		- 
	- documentation
	- monitoring and observability
		- OOM in railyard
	- integration
	- resources
		- Training is wasteful in terms of resource usage.
	- Missing:
		- distributed training
		- autoML
- How using Flyte for Railyard is a solution?
	- FI use flyte to improve iteration speed.
	- Automation with auto-training and deployment.
	- Consolidate two k8s clusters into one: use Flyte's k8s cluster.
	- Railyard today is more opinionated with static DAGs. The solution calls for a more flexibility, with Flyte.
	- Today, Railyard uses Dask. For example, Railyard can read data larger tham memory from Dask.
	- Railyard executes on a single instance host
- [Batch Scoring](https://docs.google.com/document/d/1-LFRyQvOaC8DvkYwAb-mS71GR_tIuzc58Z_j8xRO6HA/edit#heading=h.8lu4onp398k2)
	- The alternative to PySpark: Flyte tasks. The advantage of Flyte tasks is that users can bring their own environment (as in Docker dependency and GPU scoring)

2023-05-02
- Data Archiver. We need to have a good risk management story for onboarding new users and workload.
- Spark 3 Migration.
	- If we let user to migrate, we may get stuck with 2.4 for a long time.
	- By next friday, discuss in batcom-staff. We need to have clarity on this into H2 planning.

2023-05-01

How to understand Minasij's PySpark feature engineering [PR](https://git.corp.stripe.com/stripe-internal/zoolander/pull/244728)?
- authz/generated/policies/query-auth/sql/hive/apollo
	- Generated by go/datasets-admin. TODO: learn what this is.
- What is zoolander/datasets/all_datasets.bzl? 
	- What is `../growth-intelligence/.../.namespace.yaml?`
- Main source file `existing_user_model_monitoring.py`
	- Compute accuracy metrics (average precision score, precision at recall 50) on product upsell propensity scores. 
	- It requires 90 days for labels to mature, so these metrics are always lagged by 90 days.
- Looks like it reference a Python method under railyard workflow path. TODO: understand how it uses Railyard. 

Study [Spark 3 USM PR from Jon Bender](https://git.corp.stripe.com/stripe-internal/zoolander/pull/244742)
	- https://git.corp.stripe.com/stripe-internal/zoolander/pull/244742 (Enhancements to USM for Spark 3 Migration use case)
	- https://git.corp.stripe.com/stripe-internal/zoolander/pull/242413 : Add Spark migration ETL job for diff results

2023-04-27

ir-pink-paragraphrase
- Offending PR: [S3 Custom Signer for AWS SDK v2](https://git.corp.stripe.com/stripe-internal/zoolander/pull/239244/files)
	- added new dependency for //third_party/java/software.amazon.awssdk:utils
- Sympton:
	- java.lang.NoSuchMethodError: software.amazon.awssdk.utils.IoUtils.closeQuietly
- Related:
	- https://github.com/aws/aws-sdk-java-v2/discussions/3688
- Failed jobs
	- https://hadoop-qos-jobhistory.corp.stripe.com/jobhistory/logs/hadoopdatanodei--07e3aa8a5ce3560f3.northwest.stripe.io:8039/container_e104_1682263213054_28835_01_000001/container_e104_1682263213054_28835_01_000001/root/stdout/?start=0&start.time=0&end.time=9223372036854775807
	- [splunk link](https://splunk.corp.stripe.com/en-US/app/search/search?q=search%20%22java.lang.NoSuchMethodError%3A%20software.amazon.awssdk.utils.IoUtils.closeQuietly%22&display.page.search.mode=verbose&dispatch.sample_ratio=1&earliest=-7d%40h&latest=now&display.page.search.tab=events&display.general.type=events&sid=1682622220.146310_82EEB3BC-98D1-4557-9E48-201C1C677787)

- Looks like `pinot_s3.jar` is the one that directly triggers `NoSuchMethodError: software.amazon.awssdk.utils.IoUtils.closeQuietly`, which is a AWS SDK V2 only, comes from `aws-sdk-java-v2`. How does it relate to the AWS SDK?
- Pinot depends on [aws sdk v2](https://git.corp.stripe.com/stripe-private-oss-forks/pinot/blob/master/pinot-tools/pom.xml#L36), including:
	- sdk-core
	- s3
- Then, the Spark ingestion job called by Pinot depends on:
	- pinot_batch_ingestion_spark_3_2, pinot_spi, pinot_tools
	- With spark31 stripe_dep_universe
	- additional_classpath_allowlist_prefixes includes everything under third_party_jvm/3rdparty/jvm/commons_
- Pinot BUILD
	- import `//third_party/java/software.amazon.awssdk:s3`

2023-04-26
Beam with Spark for data scientists
- [Machine Learning with Python](https://beam.apache.org/documentation/sdks/python-machine-learning/)
- You can use Beam with RunInterence API to use ML models to do local and remote interence with batch and streaming pipelines. It supports PyTorch and Scikit-learn and Tensorflow frameworks.
- RunInterence API take advantage of existing Beam concepts, such as the BatchElements transform and the Shared class, to enable you to use models in your pipeline for ML interence.
	- BatchElements PTransform to take advantage of the optimizations of vectorized interence.
	- Shared class within the RunInterence makes it possible to load the model only once per process and share it with all DoFn instances created in that process. This reduces memory consumption and model loading time.
- Modify a Python pipeline to use an ML model
	- It just means adding the RunInterence<model_handler> to the pipeline.
	- ModelHandler is to wrap the underlying model.
- Use pre-trained models
	- PyTorch: provide a path to a file that contains the model's saved weights. The pipeline must have access to this file. Pass the path of the model weights to the PyTorch ModelHandler
	- Scikit-learn: provide a path to a file that contains the pickled Scikit-learn model. Pass the path using ModelHandler
- Use custom models
	- Create your own ModelHandler or KeyedModelHandler with logic to load your model and use it to run the interence. 
- Multi-languageg Interence Pipeline
	- Cross-language Python transform
		- Any Python transforms defined in the scope of the expansion service should be accessible by specifying their fully qualified names. For example, you can use Python's ReadFromText tranasform in a Java pipeline with its fully qualified name apache_beam.io.ReadFromText
	- Custom Python transform
		- In addition to running interence, we also can perform preprocessing and postprocessing on the data.
- Data Exploration
	- Beam Python SDK provides a DataFrame API for working with Pandas-like DataFrame objects. You can build complex data processing pipelines by invoking standard Pandas commands.

[Spark Runner](https://beam.apache.org/documentation/runners/spark/)
- Native support for Beam side-inputs via Spark's Broadcast variables.
	- Allow you to incorporate additional data into your transformations without needing to join or merge the data directly into main input.
	- Any transform that accepts a function, like Map, can take side inputs. If we only need a single value, use beam.pvalue.AsSingleton and access them as a Python value. If we need multiple values, use beam.pvalue.AsIter and access them as an iterable.
- Three runners
	- Legacy: only support JVM based on RDD/DStream
	- Structured Streaming Srunner which supports only JVM and based on Spark datasets.
	- Portable runner
- How to use DataFrame API with Spark runner?
	- Full name: Apache Beam Spark Runner DataFrame API, built on top of Spark SQL API. 
	- beam.io.ReadFromDataSource and beam.io.WriteToDataSource
	- DataFrame operations: filter, groupBy, agg, join, select
	- Currently support Spark 3.1.x
- Pipeline options for the Spark Runner
	- runner
	- sparkMaster: the URL of Spark Master, 'yarn' to connect to a YARN cluster.
	- storageLevel: when caching RDDs in batch pipelines. The Spark Runner automatically caches RDDs that are used repeatedly. This is a batch-only property.
- [Getting Started with Spark](https://beam.apache.org/get-started/from-spark/)
	- 

Reorg: Data Lake Structured Data Team
- Merge the Data Governance and Data Optimization Team, now called Data Lake Structured Data, to deliver together on improving experience of Iceberg.
- Pausing work on Datahub, data tiering and data registry, to focus on infra integrations and revisit the strategy of Data Catalog.
- Data Optimizations: delivered on the first set of incremental processing pattern with data ingestion team and continue the effort. Addressed Iceberg orphaned data file deletion.
- Data Governance: improve experience of Datahub.
- Structured Data: requested Iceberg features, Iceberg upgrade and dependencies. 

2023-04-25
What's BentoML and how does it work with Spark?
- BentoML excels at serving models in real-time.
- BentoML has developed a new batch inference API that uses Spark


2023-04-24

Prepare for Meeting with Jonathan Gruhl (@jgruhl)
- He is involved with Apollo
- How is Apollo used?
	- Product recommendations during onboarding
	- product recommendations in targetted insights.
	- nurture campains through marketing emails.


2023-04-18
#### yichen/ir-cornered-concise
- s3://prod-stripe-financial-data-us-west-2/iceberg_warehouse
- Dmitry's chart of the S3 access log: https://hubble.corp.stripe.com/queries/borovsky/49e9b87e/linechart


How to test local branch of puppet in hadoop?
```

`# this will ensure that new hosts will spin up with the puppet environment on the test branch (for example when you replace)`

`sc-asg sync hadoopdatanodei.northwest.qa.stripe.io/test --branch`

`# the output of this command is useful to check what branch the config is set to currently`

`# this will puppet the change to the existing hosts`

`sc-puppet --yes --ssh --host-set test -Sqt` `"hadoopdatanodei"`

`# this will restart the services on the hosts to start using the patched jars`

`for``-servers --host-set test -Sqt` `"hadoopdatanodei"` `"sudo svc -t /etc/service/hadoop-nodemanager /etc/service/hadoop-datanode"`
```

2023-04-17

Where to look for S3 access log?
- See `iceberg.access_and_attribution.s3_server_access_logs_v1`

2023-04-11
Questions about using Apache Beam at LinkedIn
- Your example is an ML use case. Do you anticipate ML use cases being the first batch of your use cases?
- What language SDK do you use at LinkedIn (Scala/Java/Python)?
- How do users debug their jobs?

### 2023-04-05
- Rahul Patil is the head of Infrastructure. Data Platform team is one of his org, headed by Derek. Rahul runs QBR at his org level, so there is a QBR for the whole Infra level (Rahul), and also QBR in each of his orgs including Data Platform under Derek.
- Rahul
	- Speak only, don't tiptoe, be respectful, speak freely, voice your disagreement. We aim to make most of the decisions today.
	- Let's go page by page. Any questions for page 1? page 2?
	- Is there enough ROI?
	- For SLA, what timeline do you have in mind?
- Yuan: what's the trajectory for notebooks and databricks? Ask if you need help accelerate that?
	- Richard: we have a good strategy, risk, we have a good amount of work in front of us. You should see 
	- Jordan: I heard from PySpark team that we are anticipating many users but people are reluctant to try PySpark. I'd like to find out what's the gap.
		- Yuan: ML engineers are tectical support, now quite a few ML engineers are trying that out. Flyte just landed this Monday.
	- Rahul: does anything need to change?
- Rahul: we have a date for that, we have a tracker for that, sounds good.

### 2023-04-03
How to use Conda to manage PySpark dependencies?
- Create a Conda environment using conda create
- Activate and pack the Conda environment using conda activate, and conda pack. The result of conda pact is a tar ball.
- Ship this tarbar with spark.archives so that it can be distributed to executors from spark-submit.
- When run spark-submit, set the path to the python interpreter. If using cluster mode, only set PYSPARK_PYTHON
	- PYSPARK_DRIVER_PYTHON
	- PYSPARK_PYTON


### 2023-04-02
[Beam Summit 2022: Unified Streaming and Batch pipeline at LinkedIn using Beam](https://www.youtube.com/watch?v=rBfwjbrMJTE&ab_channel=ApacheBeam)
- The main problem is that backfill is the challgen, take a week to backfill
	- Our infra doesn't like the bursty resource request
	- Backfill is a stress test to our patner teams. Noisy-neighbor for streaming pipelines. Manual start/stop of backfill
- We are essentially switching back to lambda architecture from Kappa archicture
- Most batch jobs at LinkedIn are Spark SQL jobs, so one solution is to develop Spark SQL jobs for the backfill case.
	- This means our users have to maintain two code base.
- Use Beam for unified pipeline
	- Unified PTransform: provides a unified interface to users but allows different implementations according to pipeline type
	- Unified Table Join
- Outcome
	- Resource is less than half of using streaming pipeline for backfilling
	- Backfill duration is reduced signicantly, 7 hours of streaming => 30 minutes of batch job
	- 

### 2023-03-29

Legal NDA when talking to LinkedIn
- talk to @jweber in slack
- We'd prefer to use Stripe's NDA if at all possible. Alternatively, we can add LinkedIn to the Microsoft SSA which includes privacy provisions as [@apeyser](https://stripe.slack.com/team/U02BCMV92A0) mentioned.  Hopefully the nature of the discussion will not require an NDA.  Let me know.
- I'd recommend waiting to hear back from them.  Happy to help with the NDA if that is a requirement.  It's more of a Stripe starting position that we should be using our NDA.  There is flexibility but we should try to preserve legal resources.

### 2023-03-02

Perf Review Feedbacks (#perf)
- There is a lot of ambiguity for PySpark. You have to know exactly what impact you want to create for what users, on what schedule with the roll-out plan, how to verify it works with the users. How everything is going to work. Think from all angles. 
- Be decisive. We will be short on time if we draw it out.
- Be forthright about your struggle.
- Visualize how the end of year looks like for PySpark. What everybody will say about PySpark. Have intimate awareness and fluency about users. Make decisions.
- Be crystal clear.
- Draw a distinction between seeking feedbacks and making decisions. Get feedbacks, but own the decisions yourself.
- PySpark is a big thing, it's on your shoulder. Be forthright. 
- You have to have your successful delivery statement for PySpark. Do we need a testimonial from users? That helps you work through the ambiguity. Know crystal clear, shiningly clear, forthright about everything. Have everyone aligned on exactly what it is. 

### 2023-02-23
- Zhen
	- use this node to try out Python dependencies on Graviton
		`ssh [qa-hadoopdatanodei--039e9e266252e3a16.northwest.stripe.io](http://qa-hadoopdatanodei--039e9e266252e3a16.northwest.stripe.io/)`
	- Current CI box cannot build graviton because the host (on Graviton) is not compatible with the Docker base image. Tracking ticket: https://jira.corp.stripe.com/browse/RUN_ZOOLANDER-5536

### 2023-02-06
- Rahul Patil
	- Risk has $500m a year budget, bigger than AWS.
	- Three things that stood out for QBR observations:
		- Feel we are 15 people short from QBR
		- Not leverage and best serve ML
		- We used to have deep dive on user experience for every new service in my first year. We may have taken our eyes of user experience (due to efficiency etc). What's the get started guide, how do they get started with data set. We used to talk a lot about UX in QBR. I am fearful of the user experience. I know you do surveys, but I feel I have a knowledge gap for the accumulative user experience. 
		- I feel there are postive conflicts here, for making good trade-offs. Sometimes you are solving problems through services, engineering, sometimes through processes.

###2023-02-02
What happens when I run `bin/run-spark` to start a PySpark job?
- `bin/run-spark` is a Python3 script.
- Looks like there is also a pay/src/zoolander/src/python/bin/run-spark.py file. It is to build and run spark jobs.
- The jobs are launched using `job_launcher.py`
- 


2023-01-25
- Meeting with @shahyar
	- The data produtivity team wants to support PySpark using static YAML, in parallel with airflow-based PySpark. Yi: should we do both or choose one?
- Meeting with @pb
	- Risk of Peppadata sending metrics to their server: Stripe made exception of sending data to SignalFX and now we are backing out of it. So this can be a blocker for Peppadata. Databricks work differently, it can run fully in our AWS account.
	-  If we were to push for the case for security review, we should not drive the case by saying how it would reduce the BATCOM team's toil and KTLO load, because they wouldn't care. What you should focus on is how it would help our critical users in critical data pipelines, which is a Stripe-level impact that security team also care about. 
	- Paul think Graviton is more prioritized than EMR because of the guranteed cost savings.
	- What's the theoratical saving opportunity for Peppadata's Capacity Optimization tooling? My guess is 10% because if it is 50% they won't need to do any selling.  Paul: in that case, it is single-digit million dollar potential saving, which is a lot less than Graviton.
	- Regarding we potentially don't want to use Capacity Optimization but Peppadata wants to bundle it up.  Tell Peppadata: we don’t have time for capacity optimization because of Graviton until H2, we’d like to separate the conversation for observability alone. 
	- On PySpark work, Paul also wants the PySpark to be a model project to provide long-term solution instead of short-term, which is similar to what Richard wants. Paul says please spend time talking to Sesh how you two can both add a lot of value to PySpark. Sesh can go broad, and you (Yi) can go deeper.
	- 
- Meeting with Avinash. 
	- Gaurav's questions:
		- what's on your mind/plate?
		- What do you want us to think about?
		- What do you think our biggest challenges are for our team?
		- What's the forum to surface our forward-looking roadmap (we've done that in QBR)? Answer: SOKR discussions.
		- What's your take in terms of user experience?
	- Dmitry:
		- How would we comminicuate the risks?
		- How would that align with other teams?

2023-01-23
- Ben / Yi
	- Core Data. (Info org -> growth and core data (Vlad) -> ML)
		- Data Science is within Core Data
		- Data Productivity.
		- Data Scientists are centralized in one org, but embed in other teams
	- Interesting challenge: operational.
	- data skew issue causing
	- Use minerva to pre-join datasets for 
	- Ben H1: CDM, customer data master, remodel data sources around merchant. for most of H1.
		- FDW: financial data warehouse, pubic facing numbers. Two parallel source of truth. 
		- 
	- Yi H1: continue
- How to find S3 location of iceberg table?
	- pay up and pay ssh to mydata box
	- on mydata box, run command `bazel run src/scala/com/stripe/iceberg/cli --show-metadata -t events.spark_jvm_profiler_report_v2_raw`
- How to explore data using Hubble Scala Notebook?
	- Go to https://hubble.corp.stripe.com/viz/hosted-notebooks/notebook/22080?view=executable&hostType=mydata-big
	- Use the following cell:
```
%%spark 

val df = spark.read.iceberg(tableName="events.spark_jvm_profiler_report_v2_raw")
val recent = df.filter(df("day") > "2023011000").show(false)
```


How to track Driver GC issue from splunk?
- Looks like I can search for splunk for the following fields:
	- thread=Driver
	- sourcetype=spark-executor-errors
	- thrown.cause.name=java.lang.OutOfMemoryError
	- thrown.cause.message=GC overhead limit exceeded
	- loggerName=org.apache.spark.deploy.yarn.ApplicationMaster

#perf #stripe/perf Dmitry's feedback on my perf review:

**Strength**  
Yi joined our team in early August and already took ownership of Spark debuggability, one of the critical areas for BDI timeliness. Yi **prioritized users** by developing a JVM dashboard to be user friendly in contrast to faster but more obscure infra-targeted dashboard. Users shared positive feedback about this work on multiple occasions.  
Yi consistently **seeks feedback** on initiatives he is working on. For example, he presented a spark JVM dashboard to the team to collectively make it better. He also seeked feedback [for a prioritized list of spark observability and debuggability opportunities](https://docs.google.com/document/d/1uPtZlYiMPk52hiJ7eiLhh1P2E4m8rxTlRI6Nw8j8PTg/edit#heading=h.cz1xkpga7giy), and used it to **gain more context** and refine priorities.  
Also Yi doesn’t hesitate to **make decisions and be accountable** for these decisions. For example, I was advocating for simple GC metrics collection to mitigate the major pain points. But once evaluated, Yi demonstrated its suboptimal solution on the long term and decided to use a JVM profiler. Even more, Yi made a right strategic decision to ingest all the GC events as-is to dataland so we don’t need to do any changes in future. These decisions were right and allowed to expose way more GC telemetry and build a comprehensive [JVM profiler dashboard](https://hubble.corp.stripe.com/viz/dashboards/28636-spark-jvm-profiler-gospark-jvm?appid=application_1670092740942_10981&tab=App+Profiler), and unblock additional improvement in future for freeOverall, despite being new, Yi **elevates** our **ambitions** by identifying new opportunities**Development**  
But We’re very resource constrained and we need to be laser focused on the initiatives with the most ROI for Stripe. The [list of opportunities](https://docs.google.com/document/d/1uPtZlYiMPk52hiJ7eiLhh1P2E4m8rxTlRI6Nw8j8PTg/edit#heading=h.cz1xkpga7giy) definitely **elevates** our **ambitions in the area of debuggability** but to evaluate it in context of our roadmap. For example, we have a major Gravition migration and it’s pretty scary to do this migration without sufficient observability and debuggability. I believe you can play a significant role in de-risking this migration by identifying the most ROI opportunities to make the migration safer, and influencing the direction and managing up to get sufficient funding to implement it.

Habib
- started in India, building automation frameworks.
- in a data warehouse startup, 6 month, small team.
- Amazon Kindle team in India, mix of PM, dev work.
- Moved to Seattle Amazon. Ad services, linear programming for fulfillment network as tech lead. Used Spark to analyze dataset, find anomaly. 
- Moved to London. Joined Kafka team as engineer, senior, then EM, build a team of 40 people.
- Moved to Twitter. 1 year.
- Preference: I would like to be candid, frank.
	- I like to connect UX with nuts and bolts.
- I am on the same page with Avinash:
	- A team not improving tooling well  is not doing a good job.
	- Natasha: engineers are not incentivised to build tools.
- Match what we are doing with user experience. 
- Strong processes.
- ASK: Send a list of top customers

### 2022-12-18
List all facts and opinions I can extract from Dmitry's [Hadoop efficiency 2023 Plan](https://docs.google.com/document/d/1xQIEf_oG_BhLIl6Y8qXs7JjfinSpUti2Rn-Ya9qUbX4/edit#heading=h.ekb6rlyii99k).
- Goals: to gain $20m AWS credits and 15% ($11m) in cost savings via migrating 50% of hadoop fleet to Graviton.  To reduce risk we will pursue 2 approaches in parallel: EMR(S) and hybrid (r6gd + EBS). Most extistential risk and ambiguity are to be identified by end of Q1.
- There is an additional $30m AWS Credit after 100% migration.
- What are all different approaches for the $30m total cost saving goal?
	- EMR-S, EMR, i4g, EBS(r6gd.16xlarge + 6TiB EBS), Hybrid (r6gd.16xlarge + 11TiB EBS), EBS (r6g + 16TiB EBS)
- What are the risks of each of these options?
	- EMS-S just started support for Graviton 6 months ago, may be immature.
	- We have never used it, don't know what issues to expect. (I should learn that this is an acceptable risk to document)
	- We didn't use EBS in hadoop at scale, so we don't know what to expect.
	- For EBS we pay for IOPs, which is a cost risk.
- Since the biggest risk is that we don't have experience, how to mitigate that risk?
	- Dmitry: we diversify by validating both EMR(s) and r6gd + EBS options in Jan/Feb
- What are other risks not captured by the approaches?
	- AWS fails to deliver the Graviton instances on time.
	- We are 2 HC short for the engineering effort.
	- Graviton cost savings can't offset cost of pure EBS
- In Dmitry's risk and beneift metrics, how did he calculate the costs?
	- He has two columns, one for amortized cost for 1 year, and another for amortized cost for 5 years. Also he plan to add IC cost (engineering time).
- What is [Granulate](https://granulate.io/)?
	- improve application performance and cut cost.
	- Real-time, continuous optimization at the operating system level. Zero-code change, no R&D effort, just install an agent, 20-days results delivered.

2022-12-16
- How to detect GC/OOM risk? 
	- With [this query](https://hubble.corp.stripe.com/queries/yichen/3daf6f78), I look for applications with significant GC pause on the driver.
	- I found this example: https://hubble.corp.stripe.com/viz/dashboards/28636--spark-jvm-profiler?appid=application_1670349731188_161192&subTab=Executors&tab=App+Profiler

### 2022-12-13
- EBS Elastic Volume: increase the volume size or change type and IOPs while the volume is still in use. Request these changes via API or CLI, and the volume states will change to modifying -> optimizing -> complete states. Usually takes a few seconds to complete. See [using elastic volumes for Oracle](https://aws.amazon.com/blogs/database/using-amazon-ebs-elastic-volumes-with-oracle-databases-part-1-introduction/).
	- Usually choose io1 for high-perf database workload, and gp2 for less demanding workloads. 
- EBS auto-resize
	- infor [automatically increase volume size when the utilization reach a threshold](https://aws.amazon.com/blogs/storage/automating-amazon-ebs-volume-resizing-with-aws-step-functions-and-aws-systems-manager/). 80% threshold in this case.
	- Increase volume size is easy, the tricky part is [extending the file system](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/recognize-expanded-volume-linux.html) to take advantage of the additional storage. If AWS System Manager manages your instances, it's possible to use AWS Lambda to send System Manager commands to run OS-level script.
- How EMR dynamically resizing EBS volume? See [blog](https://aws.amazon.com/blogs/big-data/dynamically-scale-up-storage-on-amazon-emr-clusters/).
	- Use [bootstrap action script](https://aws-blogs-artifacts-public.s3.amazonaws.com/artifacts/REVBDBBLOG-46/resize_storage_NVMe.sh). Looks like this is EMR specific, not sure if it works with generic EC2 nodes.
	- Internally, it is using the EBS elastic volume.
- https://github.com/mpostument/ebs-autoresize
- Helen on disk space issue.
	- i3 clusters. R5D
	- We are aware of the disk space issue.
	- Disk quota never worked, users just keep increase the quota, for 2+ years.
	- Only in the last year UAR demands more reliability.
	- i4 becomes a solution, 0% or 30% cost increase. Rolled out to cost, recon. 
	- Convince users to do the migration, user billing and recon, we will foot the migration bill. Recon ended up 1% or 3% cost increase. 
	- Cost increase maxed out at 7% instead of 30%.
	- Long-Term solution: disagg (2-year), EMR (2-year)
	- Med-Term: moving queues over, but its a lot of work for Helen. Dmitry math: expect 1% total hadoop cost for moving all. 
		- Can be done within 1 quarter. 
	- Migration: we migrate queue with 30% buffer, let it run for a week, and then resize back.
	- Can migration be automated and let the user drive it?
		- It's a lot of work.
	- What's causing the disk space usage?
		- Mostly cache
	- Helen: the shortest work, change the process, skip the i4 process. 
	- Have we thought about EBS?
		- data ingestion have more experience with EBS, and they use EBS for their dedicated cluster (snapshot).  JimmyXie worked on this.
		- Helen doesn't know if it has been discussed.
	- https://livegrep.corp.stripe.com/view/stripe-internal/zoolander/data_common/src/scala/com/stripe/spark/launcher/spark_submit/classified_errors.yaml
	- https://docs.google.com/document/d/1F5LokwvtMZCo7SGqIL5J8lJW4kEqwegm3JyYsoakuPw/edit#
	- https://groups.google.com/a/stripe.com/g/foundation-shipped/c/HUm1T8zhN60/m/UVH-jsZ5AwAJ
	- https://groups.google.com/a/stripe.com/g/foundation-shipped/c/7oJC0YJiXQE/m/JWlOzEx0CAAJ

### 2022-12-12

How Spark uses local disk?
- it still uses local disks to store data that doesn’t fit in RAM, as well as to preserve intermediate output between stages.
What are potential solutions for local disk issues?
- Use EBS for local disk? I need to know how to configure Spark's local disk path before thinking about if I can point the EBS volume. [EBS Elastic Volumes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-modify-volume.html).
- How about just use one giant [EBS MultiAttach](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volumes-multi.html) volume per cluster?

Meeting with Paul (@pb)
- Working on user facing reporting data.
- Would like to see we run on EMR in 2025.
- Think its a good idea to start on EMR with a small use case.


2023-Q1: 
	- Roadmap for preventing disk space resource exhaustion?
		- [2022-11-28](https://docs.google.com/document/d/1LCKbbd51jvUkC3KnXkJYEmlDIv7xtzoLtUIJPZfHh_w/edit#heading=h.x9nkgvdk0lay): teams seem more willing to migrate to i4s with estimated 7% increase in spend. 
		- 2022-11-14: migrate to Concord.
		- 2022-10-31: [Dmitry's doc](https://docs.google.com/document/d/1EABENXQoXBxQwW8JJzCUPv4JVvu8pl9Ias7hyKpU5LE/edit#heading=h.jn1zr2y2c0ov), [Helen's doc](https://docs.google.com/document/d/1Crmuyx8ORHp76qopGxGBFccpjDqGMr2Uecg_4eg_ZFY/edit#heading=h.jn1zr2y2c0ov).
		- Incident: **ir-potassium-evolve** : 40% of local disk space was taken by Scalding job. Notes were getting decommissioned because of disk filling, losing capacity for the cluster. 
		- Why strawberry/qos not reliable for disk space issue? It's less of an issue with concord/indigo because i4s has 4 times more local disk space of r5ds.
		- The scheduler are not smart enough to take local disk demand into account when making sceduling decision. As a result, jobs may fail when one or two tenents on the cluster spike their local disk space. Users ask for strong isolation, but our infrastructure cannot provide that.
		- What's the long-term plan? **disaggregated storage and compute**. Migration was targetted for 2024.
		- Helen's [dashboard](https://hubble.corp.stripe.com/viz/dashboards/28713--disk-space-usage?tab=Usage) for disk space.
		- Vein thinks it may be related to logging.
	- Spark-as-a-service: p90 Spark History logs delay is reduced from O(days) to O(1 hour) to aid self service debuggability of Spark Applications
		- 

2022-12-08

Where to find the trino dashboard for Hubble queries? 
- See https://dsrv-presto-nw2presto3.corp.stripe.com/ui/, and search by my user name yichen. When I visit a hubble dashboard, the 

How the title and BLUF of ship mail should look like? Give some examples
- Retention Change on sima.oplog, mercury, and change events topics
	- BLUF:  We’ve adjusted the sima.oplog, mercury*, and online_db.cdc* Kafka topics retention from infinite to 4-months. This is estimated to save ~$150K/month (or $1.8M annualized; an 86% cost reduction).
- Mongo backup optimizations save Stripe $9.3M/year
- Search support for Stripe Next/Caribou
	- Search is ready to accept Stripe Next datasets. Simply specify your search schema with proto, and write your data to Elasticsearch by publishing to Kafka. Detailed instructions [here](https://trailhead.corp.stripe.com/docs/search/stripe-next-datasets).

2022-12-07

Helen's comment on ship mail
-   missing impact summary, simple one liner for impact
-   missing why is important section: a detailed version of BLUF.
-   Story we are telling. Eg. we used to operate on a black box. List the incidents, UAR impacts.
-   Reduce diagnose time. 
-   Case Studies, with numbers.
-   You are not trying to prove something, but making it easier to understand. regarding observability tool.
-   Even if there are no numbers, we have NO observability before (black box). Zero-to-One impact.
-   Impact: we can unblock some future work (can we link to those future work already planned): efficiency and reliability (GC warnings). Nobody have asked, and didn’t know the opportunity for right-sizing.
-   Why is hard: two audiences: (1) execs: why it takes so long to do this, (2) engineers ….
-   You must be exact and precise for BLUF.

### 2022-11-29
#dmitry [Dmitry's feedback on the jvm-profiler dashboard](https://stripe.slack.com/archives/G2H1MLGUT/p1669752999127179):

thanks a lot for the great presentation, my notes:  
1.  Can we add more hints how to interpret GC metrics (marksweep, etc)?
2.  Can we add good/bad thresholds?
3.  It would be good to leverage the dashboard from [https://confluence.corp.stripe.com/display/DATALIB/OutOfMemoryError+%28OOM%29+and+GC+issues+in+Spark+jobs](https://confluence.corp.stripe.com/display/DATALIB/OutOfMemoryError+%28OOM%29+and+GC+issues+in+Spark+jobs) to quantify particular issues.
4.  Can we aromatically detect issues from [https://confluence.corp.stripe.com/display/DATALIB/OutOfMemoryError+%28OOM%29+and+GC+issues+in+Spark+jobs](https://confluence.corp.stripe.com/display/DATALIB/OutOfMemoryError+%28OOM%29+and+GC+issues+in+Spark+jobs) on the dashboard?
5.  Can we merge spark-profiler and jvm dahboards?
6.  Simpler navigation: click on app id to navigate to app specific page
7.  Quantify GC issues based unused API (DF vs RDD)
8.  Adding recent failures to the dashboard, especially once that are potentially OOMs

2022-11-28
Practices:
- Fear of Failure (be fearless)
- Do high-level thinking (look down on my machine)


2022-11-28
- JVM Profiler Case Study with data ingestion:
		https://stripe.slack.com/archives/C01F9BDN3RT/p1669680491407359




Come up with a plan to work with Vivek about JVM Profiler
- task `cost_platform.ReconcileCostsWithReportingData`
- `https://hubble.corp.stripe.com/viz/dashboards/28636--spark-jvm-profiler?appid=application_1668642001079_37375&tab=App+Profiler&taskid=cost_platform.ReconcileCostsWithReportingData`

jvm-profiler dashboard rebuild

```
-- Driver GC Metrics
select appid, collectiontime, collector, collectioncount, airflowtaskid, epochmillis
from iceberg.events.spark_jvm_profiler_report_raw
cross join unnest(gc) as g(collectiontime, collector, collectioncount)
where locality_zone = 'DEFAULT' and day >= date_format(current_date - interval '7' day, '%Y%m%d%H')
and role = 'driver'


-- Driver Memory Metrics
select
appid,
epochmillis,
heapmemorytotalused,
heapmemorymax,
nonheapmemorytotalused,
nonheapmemorymax,
vmHWM,vmPeak, vmRSS,
airflowdagid,
airflowtaskid
from
iceberg.events.spark_jvm_profiler_report_raw
where
locality_zone = 'DEFAULT'
and day >= date_format(current_date - interval '7' day, '%Y%m%d%H')
and role = 'driver'

-- driver buffer pools

select appid, host, processuuid, bufferPoolTotalCapacity / 1000000 as bufferPoolTotalCapacity_mb, bufferPoolName, bufferPoolCount, bufferPoolMemoryUsed / 1000000 as bufferPoolMemoryUsed_mb, epochmillis 
from iceberg.events.spark_jvm_profiler_report_raw 
cross join unnest(bufferpools) as bp(bufferPoolTotalCapacity, bufferPoolName, bufferPoolCount, bufferPoolMemoryUsed)
where locality_zone = 'DEFAULT' and day > '2022101800'
and role = 'driver'

-- driver memory pools
select appid, host, 1.0 * peakUsageMax / 1000000000 as peakUsageMax_gb, 1.0 * usageMax/ 1000000000 as usageMax_gb, 1.0 * peakUsageUsed/ 1000000000 as peakUsageUsed_gb, memoryPoolName, 1.0 * peakUsageCommitted/ 1000000000 as peakUsageCommitted_gb, 1.0 * usageUsed/ 1000000000 as usageUsed_gb, type, 1.0 * usageCommitted/ 1000000000 as usageCommitted_gb, epochmillis
from iceberg.events.spark_jvm_profiler_report_raw
cross join unnest(memorypools) as mp(peakUsageMax, usageMax, peakUsageUsed, memoryPoolName, peakUsageCommitted, usageUsed, type, usageCommitted)
where locality_zone = 'DEFAULT' and day > '2022101800'
and usageMax > -1
and peakUsageMax > -1
and role = 'driver'

-- driver non-heap usage
select appid, epochmillis, nonheapmemorytotalused from iceberg.events.spark_jvm_profiler_report_raw
where locality_zone = 'DEFAULT' and day > '2022101800'
and role = 'driver'

-- driver memory usage
select appid, epochmillis, heapmemorytotalused,
heapmemorymax,
nonheapmemorytotalused,
nonheapmemorymax,
vmHWM,vmPeak, vmRSS,
airflowdagid,
airflowtaskid
from
iceberg.events.spark_jvm_profiler_report_raw
where
locality_zone = 'DEFAULT'
and day > '2022101800'
and role = 'driver'

-- driver CPU
select epochmillis, appid, airflowtaskid, processCpuLoad, systemCpuLoad, processCpuTime
from iceberg.events.spark_jvm_profiler_report_raw
where locality_zone = 'DEFAULT' and day > '2022102000'
and role = 'driver'

-- day hour all apps
select  distinct day,  appid  from  events.spark_jvm_profiler_report  where  day > '20221018'

--- driver heap memory usage ratio
select
  appid, epochmillis, heapmemorytotalused_mb * 1.0 / heapmemorymax_mb as driver_heap_usage_ratio
from
  driver_heap_memory_metrics
where
  appid = '{{ appid }}'
order by
  epochmillis
```



[Enabling PySpark by Josh Marcus](https://docs.google.com/document/d/1XXw_b-t0m2hhhSwnHb08_VQeWOLF84eciRl7ygD-sxQ/edit?usp=sharing) 
- 22 Q3 QBR, it is our strategic direction to support Python as a first class language for data exploratrion.
- What's already there and what's missing? PySpark already comes packaged. We don't have tooling to support building and testing PySpark jobs., packaging Python libraries dependencies. Our infrastructure also depends on features (type arguments) that are inaccessible from Python. 
- PySpark focus: SparkSQL and DataFrame API, will not support Streaming API, MLlib, and RDD (SparkCore). We will be very cautious for non-vectorized Python UDFs.
- How to make Python libraries dependencies of a Python file available to all Spark executors? 

Incident ir-naming-feasible,  BlockMissingException
- Dmitry's splunk query, find all such failures from airflow logs count by task and date: `"Could not obtain block:" sourcetype="airflow" | stats count by airflow_task, execution_date`
- What is the reason behind BlockMissingException?
	- In DFSInputStream.refetchLocations in DFSClient, there is a random wait time for back-off retries (about 3 seconds).
	- Looks like a lot of similar errors comes from SHS because it also uses DFSClient.
	- for Concord, "Could not obtain block" seems to start appear around the time the incident happens and are continuing.
- Follow the steps based on [article](https://www.linkedin.com/pulse/solved-mystery-blockmissingexception-hadoop-file-system-rajat-kumar/).
	- make sure each data node is reachable from NameNode (how?)
	- Check Namenode and editlog/fsimage file status.
	- try switch namenode (with standby)
	- restart Hadoop
- During the time when the job failed, see many such errors: 
	- `java.io.IOException: Got error, status=ERROR, status message opReplaceBlock BP-1260119583-10.68.166.248-1618344631917:blk_6765789845_5692289329 received exception java.io.IOException: Got error, status=ERROR, status message Not able to copy block 6765789845 to /10.68.174.30:56872 because threads quota is exceeded., copy block BP-1260119583-10.68.166.248-1618344631917:blk_6765789845_5692289329 from /10.68.8.244:9866, reportedBlock move is failed`
		- This error comes from DataXceiverServer, used for receiving/sending a block of data. It listens for requests from clients or other DataNodes. It has a throttler based on bandwith and max threads. In this case, the maxThreads quota is triggered.
		- "replaceBlock"
	- `java.io.IOException: Got error, status=ERROR, status message opReplaceBlock BP-1260119583-10.68.166.248-1618344631917:blk_6945100759_5871602291 received exception java.io.EOFException: Unexpected EOF while trying to read response from server, reportedBlock move is failed`
	- `ERROR hdfs.DFSClient: Failed to close file: /system/balancer.id`
- What happens to the failed block `BP-1260119583-10.68.166.248-1618344631917:blk_6944836667_5871383772`?
	- found `WARN blockmanagement.BlockManager: PendingReconstructionMonitor timed out blk_6944836667_5871383772`. What does this mean?
		- Looks like it may be the block replication process. Maybe the replication failed so the block was never replicated.
	- Confirmed that during all the time when an app fail, the missing block has a corresponding error. Use this to search splunk: `host=hadoopnamenode* host_set=concord WARN blockmanagement.BlockManager: PendingReconstructionMonitor timed out`
	- During the same 7-day period, there is only one hour for strawberry.
- [HDFS-14560](https://issues.apache.org/jira/browse/HDFS-14560): looks like datanode decomissioning can trigger the reconstruction of blocks to reach the desired replication factor. Maybe we are scaling down the cluster, which triggered large block replication, which triggers the block replication timeout error?
- There is a [HDFS quota manager service](https://confluence.corp.stripe.com/pages/viewpage.action?pageId=400444277), showing max value at 2am every day for concord. See [dashboard](https://stripe.signalfx.com/#/chart/v2/D8asAfuAgAA?groupId=DdXBD73AcAA&configId=DoN5nzYAYAA&startTime=-1w&endTime=Now&sources%5B%5D=host_set:concord). Is this related? Is it possible that we have a quota set for /tmp/hadoop_* such that it is triggering this issue? Yes the default quota is 1000000 for name, and 30TB for space (and there is no override for concord)
- `org.apache.hadoop.hdfs.BlockMissingException: Could not obtain block: BP-1260119583-10.68.166.248-1618344631917:blk_7108260845_6034792795 file=/tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet`


First record of the block `blk_7108260845_6034768873`
```
[2022-11-08 13:19:53.967004] 22/11/08 13:19:53 INFO hdfs.HdfsQuotas: [DRYRUN] Assigning quota size: 30000000000000, files: 1000000 to created path: /tmp/hadoop_unknown_aXj1YIpn
	source = /pay/log/hdfs-quota-srv.log

[2022-11-08 13:30:12.799898] 22/11/08 13:30:12 INFO hdfs.HdfsQuotas: Name usage of application_1667625547913_49639 in hdfs:/tmp/hadoop_unknown_aXj1YIpn: 20004

2022-11-08 13:30:12,799 INFO org.apache.hadoop.hdfs.server.namenode.FSNamesystem.audit: allowed=true ugi=root (auth:SIMPLE) ip=/10.68.97.205 cmd=contentSummary src=/tmp/hadoop_unknown_aXj1YIpn dst=null perm=null proto=rpc

[2022-11-08 13:30:02.557682] 22/11/08 13:30:02 INFO hdfs.HdfsQuotas: Space usage of application_1667625547913_49639 in hdfs:/tmp/hadoop_unknown_aXj1YIpn: 23617100268


[2022-11-08 13:24:05.341504] 22/11/08 13:24:05 INFO hdfs.StateChange: BLOCK* allocate blk_7108260845_6034768873, replicas=10.68.175.245:9866, 10.68.48.191:9866 for /tm
p/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_017137_70896/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.p
arquet
```

The original temp files finished writting successfully at timestamp
```
[2022-11-08 13:24:05.707484] 22/11/08 13:24:05 INFO hdfs.StateChange: DIR* completeFile: /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_018342_72101/part-18342-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet is closed by DFSClient_attempt_20221108132013_0003_m_001623_55382_-1513622036_81
```

Check NameNode:
[https://amp.corp.stripe.com/host-types/hadoopnamenodepri](https://amp.corp.stripe.com/host-types/hadoopnamenodepri)

Search splunk by the file path `/tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet`
```
2022-11-08 13:30:01,219 INFO org.apache.hadoop.hdfs.server.namenode.FSNamesystem.audit: allowed=true ugi=root (auth:SIMPLE) ip=/10.68.53.246 cmd=open src=/tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet dst=null perm=null proto=rpc

2022-11-08 13:25:16,927 INFO org.apache.hadoop.hdfs.server.namenode.FSNamesystem.audit: allowed=true ugi=root (auth:SIMPLE) ip=/10.68.175.245 cmd=rename src=/tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_017137_70896/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet dst=/tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet perm=root:hadoop:rw-r--r-- proto=rpc

2022-11-08 13:25:16,926 INFO org.apache.hadoop.hdfs.server.namenode.FSNamesystem.audit: allowed=true ugi=root (auth:SIMPLE) ip=/10.68.175.245 cmd=getfileinfo src=/tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/part-17137-815a50a4-7a4f-426a-98cd-415ced59852e-c000.zstd.parquet dst=null perm=null proto=rpc
```

looks like the Hadoop rename operation is translated to the lower-level updatePipeline()

There is an ERROR log 12 seconds after the rename operation. Looks like 
```
[2022-11-08 18:25:28.259316] 22/11/08 18:25:28 ERROR namenode.RedundantEditLogInputStream: Got error reading edit log input stream /pay/hadoop/name/current/edits_inprogress_0000000038527917241; failing over to edit log http://hadoop-concord-namenodeprimary.service.northwest.consul:8480/getJournal?jid=hadoop-concord&segmentTxId=38527917241&storageInfo=-65%3A1569623881%3A1618344631917%3ACID-37ab7120-5a96-4779-b3b3-5599807e7bf8&inProgressOk=true, http://hadoop-concord-namenodesecondary.service.northwest.consul:8480/getJournal?jid=hadoop-concord&segmentTxId=38527917241&storageInfo=-65%3A1569623881%3A1618344631917%3ACID-37ab7120-5a96-4779-b3b3-5599807e7bf8&inProgressOk=true

[2022-11-08 18:25:28.259382] java.io.EOFException: Premature EOF from inputStream after skipping 380668 byte(s).
[2022-11-08 18:25:28.259464]    at org.apache.hadoop.io.IOUtils.skipFully(IOUtils.java:235)
.108.178:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_001994_55753/part-01994-815a50a4-7a4f-426a-98cd-415
ced59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.508125] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239713_6034747741, replicas=10.68.166.237:9866, 10.68
.96.72:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_000139_53898/part-00139-815a50a4-7a4f-426a-98cd-415ce
d59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.508279] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239714_6034747742, replicas=10.68.166.237:9866, 10.68
.169.107:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_002736_56495/part-02736-815a50a4-7a4f-426a-98cd-415
ced59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.508453] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239715_6034747743, replicas=10.68.166.237:9866, 10.68
.53.207:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_000510_54269/part-00510-815a50a4-7a4f-426a-98cd-415c
ed59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.508668] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239716_6034747744, replicas=10.68.166.237:9866, 10.68
.107.53:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_002365_56124/part-02365-815a50a4-7a4f-426a-98cd-415c
ed59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.508974] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239718_6034747746, replicas=10.68.166.237:9866, 10.68
.62.16:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_003478_57237/part-03478-815a50a4-7a4f-426a-98cd-415ce
d59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.509561] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239719_6034747747, replicas=10.68.166.237:9866, 10.68
.111.211:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_001623_55382/part-01623-815a50a4-7a4f-426a-98cd-415
ced59852e-c000.zstd.parquet
hadoop-namenode.log:[2022-11-08 13:23:55.509876] 22/11/08 13:23:55 INFO hdfs.StateChange: BLOCK* allocate blk_7108239720_6034747748, replicas=10.68.166.237:9866, 10.68
.15.178:9866 for /tmp/hadoop_unknown_aXj1YIpn/tmp_data_12744/_temporary/0/_temporary/attempt_20221108132013_0003_m_003107_56866/part-03107-815a50a4-7a4f-426a-98cd-415c
ed59852e-c000.zstd.parquet
[2022-11-08 18:25:28.260181]    at org.apache.hadoop.ipc.RPC$Server.call(RPC.java:1070)
[2022-11-08 18:25:28.260192]    at org.apache.hadoop.ipc.Server$RpcCall.run(Server.java:999)
[2022-11-08 18:25:28.260203]    at org.apache.hadoop.ipc.Server$RpcCall.run(Server.java:927)
[2022-11-08 18:25:28.260214]    at java.security.AccessController.doPrivileged(Native Method)
[2022-11-08 18:25:28.260225]    at javax.security.auth.Subject.doAs(Subject.java:422)
[2022-11-08 18:25:28.260241]    at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1730)
[2022-11-08 18:25:28.260255]    at org.apache.hadoop.ipc.Server$Handler.run(Server.java:2915)
[2022-11-08 18:25:28.260278] 22/11/08 18:25:28 INFO namenode.FileJournalManager: Finalizing edits file /pay/hadoop/name/current/edits_inprogress_0000000038527917241 -> /pay/hadoop/name/current/edits_0000000038527917241-0000000038527926280
[2022-11-08 18:25:28.260309] 22/11/08 18:25:28 INFO namenode.RedundantEditLogInputStream: Fast-forwarding stream 'http://hadoop-concord-namenodeprimary.service.northwest.consul:8480/getJournal?jid=hadoop-concord&segmentTxId=38527917241&storageInfo=-65%3A1569623881%3A1618344631917%3ACID-37ab7120-5a96-4779-b3b3-5599807e7bf8&inProgressOk=true' to transaction ID 38527926275
[2022-11-08 18:25:28.260325] 22/11/08 18:25:28 INFO namenode.FSEditLog: Starting log segment at 38527926281

```


What is the meaning of this ERROR?
```
java.io.IOException: Got error, status=ERROR, status message opReplaceBlock BP-1260119583-10.68.166.248-1618344631917:blk_7119026689_6045535067 received exception java.io.IOException: Got error, status=ERROR, status message Not able to copy block 7119026689 to /10.68.55.199:43674 because threads quota is exceeded., copy block BP-1260119583-10.68.166.248-1618344631917:blk_7119026689_6045535067 from /10.68.56.89:9866, reportedBlock move is failed
```
- This error is thrown from `DataXceiver` class during `copyBlock()` call, which is a runnable for Thread for processing incoming/outgoing data stream. `DataXceiver` runs on the DataNode.
- What is `opReplaceBlock`? Why? Maybe `opReplaceBlock` include a copy block from one DataNode to another? What DFS operation will trigger replace block and copy block?
- What is PendingReconstructionMonitor?


[Remove usage of ephemeral ports in Hadoop configuration](https://jira.corp.stripe.com/browse/BATCOM-998)
- 50070 is a [linux ephemeral port](https://en.wikipedia.org/wiki/Ephemeral_port#:~:text=4%20Notes-,Range,the%20port%20range%2032768%E2%80%9360999 "Follow link"), which means that it should only be used for temporary connections.
- there was recently an issue during QoS namenodes replacements where both the Hadoop process and the Envoy process tried to connect to the same port (50070) since Envoy attaches itself to ephemeral ports. Another process that we run on our hosts could grab the hardcoded port number, and then the Hadoop service would fail to start. Although this time it happened with the Envoy process, but it could just as easily be some other process. This could potentially be more of an issue as we cycle more hosts automatically with host lifecycling.
- Roll-out risk
	- requires cluster downtime.


Dave Holcombe
#dave 

- Do you understand why this document (vision) is blocking?
		- Dmitry: jordan asks if we are moving fast enough, that we are saying no a lot to other capabilities. They want to know what steps can taken to get out of the toil state.
	- I don't find the doc convicing. What's missing: The details on how to fix the problems, which will convince me you have a plan. The current doc is mostly vision business impact, no list of projects, too hand-wavy. You need this doc to be convincing. It's not about people don't understand your business. [Dmitry] we got the opposite feedback from Charles [Dave] Ignore Charles. 
	- What I look for in a roadmap: [who] will do [what] by [when] by [how].
	- you just told me you don't have a good way to know what to work on.
	- How to make OOM/GC easier to debug?  There should be a way to add a few setences to explain who,what,when,how. There gotta to be some details of how here, otherwise you can just say "we will make everything better."
	- I like the business impact "reduce toil from 3 eng to 2 eng", but this is a goal, not a roadmap. We need more detail.
	- Add an apendix, give reader an abstract. Don't expect reader to read another document to understand what's going on. It's not effective to get executive read and examine and agree. They should get everything in this doc.
	- People will not finish reading your doc (I stopped reading at FAQ). Do you have root-causing quantified (e.g. risk probability). Have you quantified historically for OOM errors in terms of toil. 
		- Dmitry: every other issue is OOM, but we don't track the engineering hours.
		- Dave: you should track (in jira, or in spreadsheet). This allow you to defend your own toil.
	- Amazon has its own JIRA, everything is in it, including non-technical work. Everything is given a root cause before it is closed. Everything is tracked, and automatically summerized in a dashboard. That's one of the biggest tool we can use to get the management to alignment.
	- You go ahead and come up a list of categories to operational budget, provide that as a table, nice and tight, this is an estimate, promise to adopt new process to get more accurate. I believe 3 of you can get that in an hour, come up with 5 or 8 categories that consumes this percent of our time for toil.
	- With this level of detail, it answers the executive's question "how we know."
	- Nobody will worry if you spend 10% resource for a pile of paper cuts, but if you say 50%, people will want to know more about it.
	- This looks cluttered. Where is the unknown-unknown classifications come from? Did Charles ask for them?  I think this add more clutter. Focusing on unknown-unknowns strike me as very less likely to success than focusing on known-knowns.
	- PySpark, which is very dear to some part of the company. Assuming you are not getting more headcount, how many people you need? What's your wild guess? Dmitry: we haven't done structured thinking, I would say 1-person-year. Dave: I would surface that in your doc exact.
	- I think you don't do efficiency, but work on PySpark, and then squeeze down the KTLO and other known-kowns.
	- FAQ section: nobody read it. Core message should be near the top.

2-people for pyspark.

scale up, scale down

```
sc-asg sync hadoopdatanodeicp.northwest.prod.stripe.io/strawberry --scaling-reason CAPACITY-2758
sc-puppet --host-set strawberry -Spt "hadoopresourcepri hadoopresourcesec" 

```
### 2022-10-31 Monday - Yi start RUN
My first RUN
- [PagerDuty Schedule](https://not-a-startup.pagerduty.com/teams/PB8HE5E#schedules)
- I am responsible for incidents (on-call is only responsible for off-hours, watching alert channels). 
- I can ask user to page on-call for off-hour requests.


### 2022-10-30 Sunday
How to create a strategy for visibility to be relevant with each audience? For Charles/Jordan/Natasha/Dmitry, what's their goals and desired outcome?
- Natasha's shipped mails
	- Timelier critical dataset in Q2


### 2022-10-27
Incidents related to jvm-profiler: ir-flash-potential
- First error for `org.apache.hadoop.security.AccessControlException: Permission denied: user=nobody, access=WRITE` happens on Oct 25 with a small amount. Large amount for the next day. No such error containing "nobody" before Oct 25, although a lot of other `AccessControlException` before that. So "nobody" is an issue.
- [Example log file full](https://hadoop-indigo-jobhistory.corp.stripe.com/jobhistory/logs/hadoopdatanodei--0f00976b4b232d178.northwest.stripe.io:8039/container_e71_1666641730668_9692_01_000001/container_e71_1666641730668_9692_01_000001/root/stdout/?start=0&start.time=0&end.time=9223372036854775807) for `application_1666641730668_9692` on `indigo`.
- The error is thrown from ApplicationMaster.



### 2022-10-26

How to find JIRA issues from data warehouse?

```
select description
from jiradb.denormalized_jiraissue
where strpos(description, 'OOM') > 0 or strpos(description, 'OutOfMemoryError') > 0
and project = 'RUN_BATCOME'
limit 10
```
### 2022-10-25 Tuesday
- Move CleanUpExcludedHostsAction from jobz/scanner as both get depricated
	- Understand the [source code](https://livegrep.corp.stripe.com/view/stripe-internal/zoolander/uppsala/src/main/java/com/stripe/hadoop/hadoopdecom/server/scanner/actions/scan/CleanupExcludedHostsAction.java)
		- This is a `CollectionAction`, iterates over subset or an entire Mongo collection. `doPerformAction` is the map function, and `performEndAction` is the reduce function. `getQueryPb` is the custom query to find the items from the collection?
		- Strangly, the action in question does not hae any of these map and reduce functions. Why? It does have performStartAction, performObjAction, and performEndAction. 
		- Looks like there is a mongodb called `hadoop_decom_db`, which has a collection called `ExcludedHost`. The scanner action works on each item in this collection: `CollectionAction<ExcludedHost>`
		- The current action is scheduled to run houry.
		- [Scanner is replaced by worflow-engine](https://confluence.corp.stripe.com/display/CDS/How+to+migrate+Scanner+to+Workflow).
	- [Useful slack discussion here.](https://stripe.slack.com/archives/C03RASSMC2E/p1666199745179609)
	- What is Decom Srv? [doc](https://confluence.corp.stripe.com/display/BATCOM/Decom+Srv%3A+Overview).
		- Responsible for decommissioning and recommissioning nodes with the ResourceManager and Namenode.
		- Runs on `hznhadoopdecombox`. and runs on MSP. 
		- Used by Hadoop node terminator script and temp decom nodes with full disk.
		- Can be restarted through the Amp UI.
		- Decom Srv has a scanner component (like a cron) which removes any hosts that no longer exist in ASG.
	- Let's understand workflow engine in a deeper level by taking ownership of the idea by [going through the guide](https://confluence.corp.stripe.com/display/PRODINFRA/Java+Integrator%27s+Guide).
		- you can see your workflow in amp by clickong on the `inspect_url` in the worfklow output.
	- The new service is now visible in qa: https://amp.qa.corp.stripe.com/workflow-engine/namespaces/product/northwest/clean-up-excluded-hosts
	- It turns out the MSP codegen automatically generated the sample source code under `uppsala/src/main/java/com/stripe/data/`, but I don't think it was merged.

		- Now I can start the job with `pay start clean-up-excluded-hosts`

- toil: https://confluence.corp.stripe.com/display/CDS/Scanner
	- Scanner are being replaced with Workflow Engine.
	- Usage: iterate over a databae collection and run soem action.
	- ExecutorAction: work with a single object or some global state. 


Debug Spark History Server
- Given an app `application_1666678018762_0187` that is finished, why Spark UI does not exist?

### 2022-10-24 Monday

Josh Marcus
- some difficult things can be done than easier things.
- building relationships, what direction we are going (think Jordan)
- Different things become more important at different time.
	- E.g. no-code pipeline.
- Use SQL to consolidate streaming and batch.
	- I've been talking about this idea for 3 years.
- Do you have a different audience for peaching your idea?
	- As staff engineer, the expectation is bigger than just your team.
- Big time lag between you peaching an idea to become funded.
- You (Yi) or I should tell Jordan what you think about SQL.
	- It won't hurt to write it down and share with people. If it doesn't work, it may come back later.
- I (Josh) started to post every other week. It doesn't have to be finished.
- Yi: this is the most producdtive first meeting
	- Josh: feel free to reach out. The feedback is not always positive.
	- External teams asking for things. 

What do I learn from the [Data Platform Q4 2022 Offsite](https://docs.google.com/document/d/1R1Szz5w17cIMunnRJn0j_7fQiMoeXLDPBEEtvdOEqgM/edit?pli=1#)?
- 

Given an application ID, how to find which cluster it is running in? For example, I see this application `application_1665916119741_6438` has very long total GC time on the driver.
- How to find application configs by an application_id?
	- Use this query: ```
```
select * from iceberg.yarn_iceberg.app_history
where app_id = 'application_1665916119741_5578'
and day > '2022102000'
```

Write a case study for investigating the root cause for `application_1665916119741_5578`

Understand the difference between these values in jvm-profiler, and why there is a huge difference between them and the heap and nonheap memory total when there is a timeout.
- vmHWM: Peak resident set size ("High Water Mark") in bytes for the JVM. An indication of actual physical memory (RAM) usesage in Linux by the JVM
- vmRSS: JVM physical memory usage (resident set size) in bytes. Looks like this is what's available in Spark 3 metrics.

### 2022-10-21 Friday

This is how to extract the airflow task ID from the profiler dataset:
```
select appid, split(split(tag, ';')[2], ':')[2] as taskId from iceberg.events.spark_jvm_profiler_report_raw
where locality_zone = 'DEFAULT'
and day >= date_format(date_add('day', -2, current_timestamp), '%Y%m%d%H')
and role = 'driver'
and tag is not null
limit 100
```

### 2022-10-20 Thursday

- [x] jvm-profiler last mile (see Natasha's feedback in 1:1 notes)

Message Natasha about spliting the team.

```
Hey Natasha, here are my potentially-controversial thoughts regarding splitting BATCOM teams:
- I think the security portion should be its own team, or merged into data government team. The reason is that the domain is more horizontal across data platform than the rest of the service areas in our domain. The knowledge is not easily transferable to the rest of the team members for long-term support.
- I think we could split the batcom team vertically, by a Spark engine team, and a Spark tooling team. The engine team would own making Spark engine works. This include Spark itself, EMR-S related work, PySpark, SparkSQL, Spark Streaming/SS, Notebooking, different Spark runtimes, connectors with other storages like S3, Trino, disaggregated shuffle etc. The tooling team is more user facing, anything above the Spark engine, including Spark profiling, observability, user experience, developer support, tuning, efficiency, CI/CD for Spark jobs, building automated infra for sister teams (e.g. auto config, auto tuning, pre-joining of dataset for cost reduction), error propogation, extraction and classification etc. This team can own capacity management tooling as well if we can't hand it to efficienty team.
- If we could split out capacity management and security scope without losing headcount, I think the remaining team could stay as one team. 
```

### 2022-10-19 Wednesday

- [x] Figure out how to chart memory and cpu profile data.

Take-aways from Gaurav's [Security Prelude](https://docs.google.com/document/d/1cjTZEABTRXFi7NKBQsZ4bF9H8srnB86Q0DxbGEF9VLo/edit#)
- What did we do in 2022 so far?
	- Q1: remove host based access to customer data in S3 from mydata and ad hoc hadoop.
	- Q2: reduced entitlement by 56%
	- Q3: Data Access Management initiative.
	- Q4 goal: reduce entitlement for Hadoop/S3 datasets from 127m to 20m
		- sophiscated users can no longer impersonate or intercept Trino requests without ssh/admin access.
		- data deletion and retnetion.
- 2023 Plan
	- Reduce Hubble usage for non data-exploration use cases.
	- Strenthen Trino: trino users can't bypass access controls by creating a copy of the table.
	- Strenthen Hadoop: auth is secure between S3, Hive Metastore, Hadoo and mydata. Adhoc hadoop in isolation.
	- EOL Hubble Notebooks (they are not secure enough)

### 2022-10-18 Tuesday

SparkHistoryServer's host set:
https://amp.corp.stripe.com/host-types/sparkhistory


How Dmitry categorize the business impact in 2024 vision doc? I should learn the vocabulary, just like Brene Brown's idea about emotions. If I know the vocabulary, I can  be better at identify incoming information.
- Dmitry uses Google sheet to describe the roadmap. The way to read the spreadsheet is from left to right. The left most column is the targetted business impact, basically goals in a way that can impact business. The next column is break-down of the goal to the drivers. That is, what we will do. The 3rd column is a category column, to measure which bucket (ROI, KTLO) this task fits in. The 4th column is a link column for documents. Then the head-count columns by quarters. Each column per quarter. This allows us to visualize when we will do a task and how much effort it takes. Question: what's the relationship between business impact column and category column?
- Dmitry charts out the head-counts based on the roadmap. This means that he is doing the manager's job.
- The business impact column has the following:
	- security
	- sufficient building blocks
	- exploration/experimentation
	- dev productivity
	- portability
	- capacity management
	- BATCOM team velocity
	- Data Quality
	- Correctness
- What's the plan for the items that I recommended, in terms of resources and scheduling?
	- Spark History Server should be fast and reliable, 1 eng quarter, Q1'23
	- Implement heuristics for OOMs, 1 eng quarter, in Q2'23
	- Integrate heuristics with reliability posture, 0.5 eng quarter, Q2'23
	- Continuous profiling (full fleet), 1 eng quarter, in Q4'23
	- Near real-time metrics (honeycomb), 1 eng quarter, in Q3'23
	- Evolve spark profiling dashboard to near real-time dashboard, 1 eng quarter, in Q4'23

### 2022-10-17 Monday
- understand how our current SparkHistoryServer is configured. 
	- RUNBOOK for SHS https://confluence.corp.stripe.com/display/BATCOM/Spark+History+Server+Troubleshooting
	- Config: https://livegrep.corp.stripe.com/view/stripe-internal/zoolander/data_common/src/data/spark_home/conf/spark-defaults.conf#L32

- [x] Share meeting notes with Engue. Wrote thank you note
- [x] Set up meetings as a staff eng (set up with Jordan, Yashiyah)
	- [x] Joaquin Luna
	- [x] Jordan
	- [x] Josh Marcus
	- [x] Sesh
	- [x] Joaquin
	- [x] Mike
	- [x] Avinash
	- [x] Shravan (medical leave)
	- [x] Archina
	
- [x] Reach out to Zoe learn about how LinkedIn does real-time ingestion for SHS
- [x] Meet Jon and share meeting notes.
- [x] Ask Joy Gao about what teams are asking for memory profile data
	- Joy: Yeah sure. so last week during office hour, Event Enrichment (i think formerly RDP?) was curious about how to check their new jobs memory usage, and they (specifically [@yunan](https://stripe.slack.com/team/U03F1SF4JTV) [@zhaobo](https://stripe.slack.com/team/U01FWRATS4X) who attended the OH) mentioned they know we are working on the JVM profiler. Context: they split up one of their job into 2 parts. The old one had OOMs before and they want to double check that the new jobs don't have the same risk by looking at their recent runs performance

### 2022-10-14 Friday
How to create a Hubble dashboard using existing data?
- This query returns 100% for the test app, how to make this useful?
	- ```select max(heapmemorytotalused *1.0 /heapmemorymax) as maxheapusedratio from iceberg.events.spark_jvm_profiler_report_qa_raw
		group by appid
	
	- ```select appid, host, processuuid, max(heapmemorytotalused *1.0 /heapmemorymax) * 100 as maxheapusedratio from iceberg.events.spark_jvm_profiler_report_qa_raw
		group by 1, 2, 3


### 2022-10-13 Thursday


1-on-1 with Engue from Efficieny:
- DP: Smruti manager
- Ask to prepare a 30/60/90 document. https://docs.google.com/document/d/1YqOd6zu8JqjuWCG7I1Si4F5Ow1Zo3JdyFPU6XYT3eYc/edit
	- understand where the team is, 
	- had a lot of 1 on 1s, build relationships across teams. with team members, member of other teams, cloud team, compute team, they are all my customers.
	- You should use it as your advantage. Talked to all staff engineers in DP, what challegnes they have in efficiency, and I can help.
	- Prepared tech talks. Collaborate with other teams, bring people alone, get there opinion, write doc together. 
	- Greatly Exceeded for all staff engineers, one of few in the whole company. It is not enough to do incremental engineering work. They expect bigger impact. You inflence others. Get involved in projects with bigger impact. 
- How to show impact for UX improvement? How about estimate by number of Spark jobs, developer commits, etc, use user study to get estimate per user, then estimate. 
	- Our PM did 30 interviews, about their pain point, wrote a doc, about Solis. Part of justification: what the user actually need from us. 
	- One of our company principle is user focused. 
	- Build relationship with users.
- Real-time cost estimate of Spark jobs
	- Engen: now you have a cross-team collab project
	- Cost saving opporutnityies can be surfaced here: https://viz.corp.stripe.com/efficiency/solis?pageType=consumer&team=%5B%22stripe%22%5D&tab=savings
	- 

### 2022-10-12 Wednesday

Pensive chat
- When a job failed, Netflix's internal scheduler will call Pensive API. Pensive then use RM API to download driver logs, use SHS API to find URLs for the failed executors, and geneate URLs to find RM API endpoints to download the executor logs
- There are about 250 rules. Each rule contains the following fields: a regex to match the error stack trace, and classifiation (user or infra), and permanent/transient error. If multiple jobs over a threshold report the same error (stack trace match), report it as infra issue. 
- Download logs from ResourceManager API. Remove HTML tags.
- 2 engineers, 12 months for batch, 12 months for streaming. 250 rules. Started with a library, over 6 years.
- Current manager of Pensive: Pawan Dixit
- MVP can use MySQL, a simple web service to collect the most painful problem.

### 2022-10-07 Friday
separated jars into two deploy tracks, one through maven artifactory for zoolander dependency, one using jenkins build for javaagent access

### 2022-10-06 Thursday
Lessons learned from Uber's [Bo Yang's tech talk about jvm-profiler](https://www.youtube.com/watch?v=fCTdbX-mG2I).
- [System Integration](https://youtu.be/fCTdbX-mG2I?t=498): Uber send metrics to Kafka, then analyze it in Flink to calculate the metrics on the application level, then land the result in MySQL. The Observability UI is powered by the MySQL backend. The data from Kafka is also sent to HDFS, which allows traditional data warehouse based analytics (Hive/Presto/Spark).
- Advanced use cases: 
	- trace arbitrary java method argument
	- access auditing: read/write HDFS files from individual Spark app.
	- Trace arbitrary java method during runtime.
	- Framegraph to trace CPU hotspot
- It appears that the JVM profiler is not always on, as he talks about future work about turn on the profiler after an application is stuck doing nothing. May need to ask him about that.

### 2022-10-05 Wednesday

Helping out with a RUN issue where the SAL (Storage Abstraction Layer) resulted in two partitions. What is SAL?
- [Storage Abostraction Layer doc](https://confluence.corp.stripe.com/pages/viewpage.action?pageId=248223395)
- [Foundation Deep Dive: Storage Abstraction Layer](https://paper.dropbox.com/doc/Foundation-Deep-Dive-Storage-Abstraction-Layer--Bqf5qGEBA~8idRr6~rTdO6_8Ag-1F8212hmppQFNoljk72FA)
- Using SAL API encourages you to standardize on naming an S3 prefix. Such prefix makes it easier for S3 retention configs and deletion pipeline, which is configured by YAML.
- The SAL is used in both Airflow task definitions and a user's Spark job. 
- Looks like it was designed to make the migration easier to Iceberg.

Understand all jvm-profiler's different profilers and see what we can use:CpuAndMemoryProfiler, ThreadInfoProfiler, ProcessInfoProfiler, durationProfiling, argumentProfiling, sampleInternal, ioProfiling, MethodDurationProfiler,MethodArgumentProfiler,StacktraceReporterProfiler, MethodArgumentProfiler.
- ThreadInfoProfiler is used to collect the thread related metrics, including totalStartedThreadCount, newThreadCount, liveThreadCount, peakThreadCount
- ProcessInfoProfiler contains: processUuid, jvmInputArguments, jvmClassPath, cmdLine.
- durationProfiling is an argument for the javaagent, to configure specific class and method. It support wildcard for method name.
- argumentProfiling: configure to profile specific method argument.
- StacktraceReporterProfiler: reads the stacktraces from the given buffer.
- MethodDurationProfiler: number of times a specified method was called, time taken for the method execution, max and average time taken by a method execution.
- [[2020 talk](https://www.databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)] At a high level, what Hadoop profiler is, It’s basically a Java agent. So when you are defining a Spark launch in the extra arguments, you will provide some configurations which is listed on their website. And once you submit a Spark job, whenever executer comes up, it comes up with this Java agent attached. This Java agent lets you do some profiling, first is a CPU memory. So when we say memory, it also tells you the speed of the memory. So let’s say you are consuming some x GB of memory for your heap, some remaining x GB of memory for your office. Also, it will give you further more information like let’s say if you’re using direct byte buffers or if you are using memory mapped buffers, then it gives you pretty detailed information about the memory. This is the specific piece which we used when we were figuring out memory usage for Marmaray jobs. Which I’ll be talking about later in this presentation. The second thing is the method duration profiling. So let’s say you have some API calls which you are making to NameNode or DataNode, and you want to profile them, Hadoop profiler is the way to do it. And the third thing is method arguments profiling. So let’s say if you are making some remote API calls, and you are passing some arguments, Hadoop profiler lets you profile them as well. Once the information is collected in the Java agent, it needs a way to report them. So the default reporters are Kafka and InfluxDB. At Uber, we use Kafka. But if you want to add your own reporter, it’s open source so feel free to go and add your own.
- [Interesting use case of jusing jvm-profiler to debug](https://issues.apache.org/jira/browse/SPARK-32277).

How other people use jvm-profiler?
- http://bigdatainourpalm.blogspot.com/2019/05/profiling-spark-application-p.html?m=0
	- Able to determine that CPU is under used, around 20 for process CPU and 27 for system CPU. This helped in reducing the number of cores given to each executor without impacting the performance
	- Able to see that none of the executors were going into aggressive full GC frequently. Able to see the scenario when vmHWM keeps increasing but java heap staying constant, implying memory leak somewhere.
	- Flame graph showed epollWait consuming unusually high CPU time, which lead to stack analysis of the process, which in turn showed there were more than 20k threads running for the process with 99% being epollWait. Found thread poll memory was ever increasing, which again point out of memory leak issue.
- https://medium.com/@Iqbalkhattra85/profiling-spark-jobs-in-production-b569ab45d84e
	- 

Understand how to add additional tags for other metadata (taskId, dagId, user, )


## 2022-10-04 Tuesday

Understand how to use [Checker](https://confluence.corp.stripe.com/display/OBS/Checker+Usage+Guide).
- Checker provides a success/fail boolean alert on UI.
- Checker runs about 1 hour frequency.
- Adding a new CheckSuite, and a new Check, in git, create PR, code review, and merge. Deploy checker and admin with the commands you get via slackbot.
- A check contains configration and check itself, which is a block of code that makes some assertions.
- The Check code can query against Hubble, and assert on the results.
- This is the Checker admin [dashboard](https://admin.corp.stripe.com/checker/batch-compute) for Batch Compute.

Planning with Yashiyah for the rest of Q4
- How to dashboard? In most cases, we need to use a database like influxDB to store jvm-profiler data to use in Grafana. Can we use other data store within Stripe? 
- What's stopping Yashiyah and I to come up with a week-by-week plan for Q4?
	- We don't know if we can onboard grafana/prometheus now. Grafana supports datasources like ES, InfluxDB, MySQL, PostgreSQL, Prometheus, but we don't know if MySQL can handle the load, and if we can publish data to Prometheus.
	- Looks like Splunk may speak the Graphite protocol, which jvm-profiler supports. Does that mean we can use Splunk for dashboarding?
	- Can we publish profiler data to prometheus? 
	- What's the relationships between Prometeus and SignalFX? Looks like some docs reference them together, talking about getting data from prometheus to SignalFX via veneur.
- How does [Veneur](https://github.com/stripe/veneur) work?
	- Veneur is a StatsD or DogStatsD protocol transport, forwarding locally collected metrics.
	- Instead of paying to store tons of data points and then aggregating them later at read-time, Veneur can calculate global aggregates, like percentiles and forward those along to your time series database.
		- reducing cost by pre-aggregating metrics such as timers into percentiles.
		- creating a vendor-agnoistic metric collection pipeline.
	- [Commandline tool ](https://github.com/stripe/veneur/tree/master/cmd/veneur-emit/#readme)to emit veneur metrics.
	- [Sinks](https://github.com/stripe/veneur/tree/master/sinks#readme) supported by Veneur, including Kafka, New Relic, SignalFX.

- Can we use [Veneur](https://github.com/stripe/veneur) to send metrics to SignalFX?
	- Will data volume a concern? Check with zp's work.
- What's the meaning of peak in JVM profiler? Is it the peak in the duration? What about the GC duration? Does it mean the duration within the trigger period?
	
	

## 2022-10-03 Monday

[2020 Gaurav's investigation on running Spark on Kubernetes](**https://paper.dropbox.com/doc/Current-State-of-Spark-on-MSP--BqVrTGLTAwdl9nMdyjMboXJhAg-37I1e5QXssf4WOCVqaEii**)
- Yi: I think Spark on k8s has improved in the past 2 years on the main issues addressed in this investigation. Namely, 
	- Spark on k8s is now GA
	- there are new open source gang schedulers for running spark
	- Dynamic allocation and external shuffle service is still listed as future work on Spark's v3.3.0 doc.

Understanding [why and what of sunset HDFS](https://paper.dropbox.com/doc/Sunset-HDFS-1-Pager--BqWAYTMgIZgKWV5if4T_AhujAg-f02JUBDc6Xw8OybvclsDX)
- How do we use HDFS today?
	- cacheAsParquet, to write intermediate data as parquet files to HDFS.
	- Stage output for Spark/Scalding apps for historical reasons for parquet.
	- Event logs from Spark write directly to a folder on HDFS. Then aggregated and imported into Presto for analyzing Spark jobs.
	- Scalding apps use HDFS for caching and shared dependencies across app. (shared cache manager)
- Challenges
	- HDFS is an open risk for security.
	- HDFS is not reliable for us and a source of toil. 
	- HDFS makes it difficult for us to run on other stacks such as Databricks, EMR etc.
	- HDFS storage colocated with compute leads to waste of resources and prevents us from using cheaper instance types (as much as 20% of our cost). Stateful hosts increases the decommission time for our hosts.
- Path forward
	- replace HDFS with S3 for cacheAsParquet
	- Stage job output for Spark on S3.
	- Spark event logs writen to S3.
	- Retire scaling jobs.


## 2022-10-02
For building jvm-profiler, I should follow this example: https://git.corp.stripe.com/stripe-private-oss-forks/hadoop/commit/7f585ec339971f5857c7182fb3c57e71db845380
Based on this instruction:
https://confluence.corp.stripe.com/display/DND/Jenkins+Configuration+User+Guide

**This worked!** 

Sending a scheduled message to @sylvestery:

Hey Yashiyah, I just hooked up the jvm-profiler repo with CIBot and jenkins. Looks like jenkins will upload the build artifact to s3 after each successful build. The physical s3 location can be found by looking for the following line in the build log:

```
Uploading file to S3 after miss: local_path="/pay/jenkins/jobs/workspace/stripe-private-oss-forks-jvm-profiler/artifacts/build.tar.gz" remote_s3_path="s3://stripe-builds-us-west-2/by-sha256/a82f750f0031db1b8c7f0daff5d98e220fb59093bfa2a60bec9ace2e030fd799.tar.gz" region="us-west-2"
```
You can manually validate the file by download the tarball to laptop and then unpack it. For example, for the above path, you can download the tarball like this:
```
sc aws s3 cp s3://stripe-builds-us-west-2/by-sha256/a82f750f0031db1b8c7f0daff5d98e220fb59093bfa2a60bec9ace2e030fd799.tar.gz .
```
Looks like there are a few ways to consume the build artifact that contains the jar. According to [this instruction](https://confluence.corp.stripe.com/display/PRODINFRA/Build+artifacts), we can use `stripe-fetch-artifact` to download to any machine. There are also puppet resources `jenkinss3artifact` and `stripe_s3_artifact` which also use this binary under the hood. There is an example [here](https://confluence.corp.stripe.com/display/TRAFFIC/Deploying+a+Binary+via+Puppet). I hope this is useful.

## 2022-10-01

There is a faster way to analyze JIRA issues, e.g. how to check who is filling batch run tickets? Here is a [hubble dashboard](https://hubble.corp.stripe.com/queries/mollyo/ad38efb1) that query the jira tickets. Essentially all JIRA tickets are stored in `jiradb.denormalized_jiraissue` and employee records with team information are stored in `mongo.stripeemployees`.

## 2022-09-30
Scheduled zoom meeting with Vikram to learn about Pensive

## 2022-09-28 Wednesday

Asked @zp about how to send Spark container logs to Splunk. This is his response:

```

so basically yeah we used splunk agent
[https://git.corp.stripe.com/pulls?q=is%3Apr+author%3Azp+archived%3Afalse+spark+log](https://git.corp.stripe.com/pulls?q=is%3Apr+author%3Azp+archived%3Afalse+spark+log)
there was a handful of PRs i submitted to add that config and setup the proper ACLs etc to make it work and configure an add'l error log output file to for spark jobs
```

How many applications / how long each SparkHistoryServer retains now?
- apricot: 14 days
- indigo: 14 days, 50k apps
- sapphire: 7 days, 4k apps
- blueberry: not functional, waited more than 30 minutes
- strawberry: not functional, waited more than 30 minutes


## 2022-08-26

It's 3 weeks on the job now, and first week on the team. Last week I was a bit more stressed out and started to lose sleep. This week I started to feel more confident. This week I was able to participate the team meeting about an incident, and make a useful suggestion (to create an end-to-end canary job to hadoop) which I think earned some trust from Guarav. I met with Dmitry and talked about Spark observability, and he liked my idea, so I think I also earned some trust from him. I start to meet more people in the team. I met Natasha. She is very focused on the fact that I am a staff engineer, which makes me a bit conscious if I am making big enough impact. She thinks the Spark Observability is related to user experience which is vague.