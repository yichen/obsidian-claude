# What I can I learn the EMR-S decision that Dmitry was driving?




## What Dmitry has to do to prepare for the initial decision

- He has to learn and understand a new offering from AWS. Looks like EMR-S is a new service, different from the EMR I know. It has no need for the team to manage servers and clusters. This is launched late in November 2021.
- He created a [document](https://docs.google.com/document/d/1daFg539PyC0NNqXCfUyHhHi_tZcUGf_i7ttjqeHJQU4/edit#heading=h.spp3815n94rz) to track the questions he need to investigate and negotiate with EMR team. This doc was created on July 7. This doc is shared with AWS under MNDA.
- He settled on the key question, that if EMR-S is comparable to EC2 costs for our existing Hadoop clusters.
	- Pro: a lot less operational needs, auto-scale, EMR runtime that is twice as fast. EMR team suggested a benchmark workload from Stripe.
	- Con: does not have short-term plans to offer Savings Plans.
- His second question is performance. What CPU/local drive performance to expect?
- Third question: does EMR support dynamic allocation? It will dramatically increase the "usage" component of the cost if not.
- Dmitry has good understanding of other potential Spark improvements, and asked AWS their future roadmap, that if AWS will adopt native vectorized accelerators like velox/databricks photon? The reason is that these are related to cost. We may lose up to 10-20% cost saving opportunity if so (I can learn from Dmitry how he can tie the technical knowledge to the core business question: cost saving, and quantify it. I also can learn from Dmitry from the breath of knowledge, to know about what's coming up in the industry)
- How fast can you do patches from OSS Spark if needed? We need to patch from OSS spark urgently a few times to address some reliability issues. Answer: EMR-S will have the latest OSS version within 60 days.
- What's SLA on how fast application resources demand is satisfied? Answer: 90 seconds, or pre-warmed.
- How does EMR-S isolate applications? Answer: strictly network isolated. You can use AS IAM to define and run jobs.
- Do we expect preemption? Answer: no. each app is isolated, with a soft limit of 2000 containers. 
- Can you prioritize help based on user's SLA? For example, we have important pipelines (UAR) that has very important and strict SLA. Answer: enhanced support model.


## What Dmitry did when recommend his recommendation?
- Looks like most of the technical questions Dmitry asked, are related to cost, as he is looking for reasons that EMR-S provide more cost savings beyond the on-paper service cost. That is, it may provide more advanced features that naturally cost less wholesale for data pipelines. 
- Dmitry concluded that we will reconsider if (1) if hadoop footprint shrinks (2) they bring some huge efficiency win features.



## How did Dmitry bring this for feedback and discussion, and defend his position?

- Dmitry wrote up a [different doc to formalize the NO-GO decision](https://docs.google.com/document/d/1UQzsS219eg3c3ukabv2st_JsCgvg05DvVFeEqsiZNL8/edit#heading=h.iydo5uzcmou5), which was started on July 6. Looks like he created a formal recommendation doc at the same time when he created the question doc with AWS. The lesson here is to have a high-level view of what needs to be done, and start them in parallel.
- Dmitry estimated that EMR-S is more expensive. He actually quantified it with [a spredsheet here](https://docs.google.com/spreadsheets/d/106mFRY9gt1GovEqWUqn98LZibzcdRG5hf8vy0qlJ0Ug/edit#gid=0). I like that he is prepared for any potential questions that can come up.
- This decisiondoc has a "gavel block" requesting each stake holder to sign their name. This is critical for high-touch decisions.


## How did Dmitry follow up and close the loop?



-----

## Practices

### Checklist
- first thing first, the cost priority, how does it compare?
	- Is the buy's cost saving claim verifiable? Can we verify from a third party experience?
- if we build, we have more option to adopt advanced, non-standard OSS. What are these out there, and will these be adopted by the buy option?
- 

### Inverse Inverse Inverse

- I assume the buy's claim in cost saving will work out.
- I assume that the effort to migrate is too optimistic.
- I forgot to follow up and drive a closure on the decision.
- There are obvious "gaps", "negative spaces" that I did not cover in the two options.



