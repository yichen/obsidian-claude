#questions #stripe 



## @pb
### [Project Polaris](https://docs.google.com/document/d/10kvyLgivOdI69dd1UVhi8aqHgJiphmstUDYHDfr59xM/edit#)
- Regarding "Polaris is a strategic investment to significantly reduce the development effort": Has a lack of a more ergonomic ledger interface caused correctness/completeness problems? In other words, are users grumbling/wasting time but ultimately getting it right, or are they failing to do the right thing entirely due to the current design? [link](https://docs.google.com/document/d/10kvyLgivOdI69dd1UVhi8aqHgJiphmstUDYHDfr59xM/edit?disco=AAAApUnpL48)
- Regarding "improve ledger's data quality": This should be the top point - the business needs correct and timely accounting data more than it needs reduced development costs. [link](https://docs.google.com/document/d/10kvyLgivOdI69dd1UVhi8aqHgJiphmstUDYHDfr59xM/edit?disco=AAAApUnpL5M).
[PySpark](https://docs.google.com/document/d/12i0ewYk6x1G_Kftq6m9-5MQDL_Sq0v-gC_acWP0t4e0/edit#heading=h.f28ez4fes4g3)
- Regarding PySpark Motivation: "How does PySpark fit in with the other processing abstractions we offer? Once this GAs, how can we make it clear to users when they should use SimpleSparkSQL vs. PySpark vs. Scala Spark vs. other future Pipelines-as-a-Service abstractions?" [comment](https://docs.google.com/document/d/12i0ewYk6x1G_Kftq6m9-5MQDL_Sq0v-gC_acWP0t4e0/edit?disco=AAAAmmIZRvo)
- Regarding PySpark roll-out plan: who will want alpha? 

## @jganoff
### [Project Polaris](https://docs.google.com/document/d/10kvyLgivOdI69dd1UVhi8aqHgJiphmstUDYHDfr59xM/edit#)
- Regarding the goals of the Polaris project: I'd like to understand how you'd compare the priority of your stated goals with some of the following: (1) dollar cost to maintain ledger, (2) enable additional upstream or downstream integrations, (3) reduce the time to deliver day downstreams. [comment](https://docs.google.com/document/d/10kvyLgivOdI69dd1UVhi8aqHgJiphmstUDYHDfr59xM/edit?disco=AAAAoOhb99o).
- Regarding the goal of "reduce 50% development cost": it's not intuitive to me that we need to reduce development cost at this time. Being toilsome is one thing, but how significant is it, and is the current level of effort preventing us from reaching our adoption/migration goals? [comment](https://docs.google.com/document/d/10kvyLgivOdI69dd1UVhi8aqHgJiphmstUDYHDfr59xM/edit?disco=AAAAoOhb990)


## @rahulpatil
- I am struggle to see why it is yellow instead of green: regarding critical project tracking meeting. We don't want to see yellow and dissentitized. 



Dmitry
- To follow up a call, "do we have some live doc to capture meetings agenda upfront?"
- Regarding EMR-S's benchmark: " it seems like cost analysis is based on sequential execution of the benchmark in a statically sized cluster. Is my read correct? if so, It’s not really representative for multi-tenant EC2 clusters nor for EMR-S. It would be great if team shares actual vcore consumption by applications and sum of runtimes of all spark tasks. In this case, we can see how it applies for our use case."
- Do you have a sense what is the desired state from user point of view?
- Do we have some specific user feedback about "error reporting"?



Avinash
- Regarding [Data Processing QBR Q2](https://docs.google.com/document/d/1V5snSR5R0Di_UwH7pSdn766KHriTmXRWlgPwIt5Ygjs/edit#)
	- Impact of this to users? Do we know if our users hae missed on their target because of this?
	- How are we doing on other operational indicators? Page volume? How is the run ticket load? Time to resolve?
	- Let's share this status with the EMs on the compute group and make sure they don't get surprised when we surface this in the DP QBR discussions.
	- Do we know of a resourcing gap?
	- Regarding "we have a stretch goal of 100% graviton migration this year": I would refraim from making this statement. Even if we can, we should evaluate this against some of the operational improvements we want to make.
	- Who has the ball on this? Is this something that RahulM can help with?
	- Is this our ideal adoption plan? I read that we are not having enough alpha users. Is that still a problem?
	- Keen to get an update on this next week?
	- I know what it means for as-a-service, but we should write it down, what it means by managed service at Stripe. What's the minimum viable managed service? What does Spark-as-a-Service mean?
	- Which of the services above requires 5 9s (99.999%)?



