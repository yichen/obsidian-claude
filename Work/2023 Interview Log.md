#interview/2023/log


Lessons Learned
- The way I practice with technical interview questions are very deliberate. For every algorithms, if I find a blind spot, a way that I haven't thought before, I would practice and make sure that I learn how to use that technique in the future. I should practice with every non-technical issues I experienced at work. For example, if I see Dmitry explain something I don't know (e.g. the reason we need to add more context and clarity with go/compass update is to make it easier for Habib to answer questions), I should practice and make sure I have the same prototype or checklist so I can actually take the ownership of the new learning. That is, get very excited about things I don't know.
- I found that after a month of covering the basics by data structure, I started covering the problems by solution type and it has been helpful to develop a better intuition.
- I found that I started to develop a better intuition about how to be a tech lead after frequent repeating (every 30 minutes) using anki for tech lead questions. Looks like my previous way of practice is just not frequent enough.
- For leetcoding, go to library. Otherwise, I would feel lonely and depressed at home. Although I need to bring my headphone, because the library can be very noisy in the afternoon when the schools are out, especially from 3:30pm to 4pm. Use https://kcls.org/rooms to book rooms if I have meetings.
- Understanding how to team and data platform organization works. What are the teams, org chart, and each team's main responsibilities. I never did that because it was not interesting, but during interview time I need to study so I can answer interview questions around "tell me how you influence your organization horizontally". What made this process easier to do is to write it down on my own doc (Google doc). In the past I didn't thought it was important, because I am a bottom-up thinker. Instead, as a leader I need to be a top-down thinker. That is, I need to know the high-level view of the organization and its challenges first. 
- Felix was right: I am too relaxed. Now that I am anxious about finding a new job, I am learning faster. Subjects that I was not interested in learning (for example, Adam's thoughts about validation for preventing data corruption) before becomes interesting and I was able to follow. It was not interesting before because I don't have intrinsic motivation and curiosity to learn those specific issues discovered through on-the-job training. I seem to be more interested in more structured learning like a tech talk or blog posts.
- Similarly regarding the lack of curiosity. I had no interest in Flink. Now that I am in interview process, I started writing a doc to understand the scope, projects, and challenges of Stripe's Streaming Compute Infrastructure. I start with an engineer's profile, and scan through their ship mail, and write down the summary.  It doesn't take long to start building an intuition of the problem space without having to spend too much time deep-dive. I should have done that a long time ago, and I should have done that for each teams within the Data Platform. As a staff engineer, I should have such a high level view of the larger org. I especially should do this level of investigation with deeper dive for my own team (BATCOM), which will help me understand intimately what each member of the team is working on.
- I never studied all alerts systematically. Now that I am leaving, I tried to study all the alerts in place, and it was a good learning opportunity. This is probably because during ramping up, the surface area is too large to do a structured learning. Also, it is a skill that can be improved. The expectation is that I can speak intelligently about how to monitor Hadoop/Spark infrastructure.
- Looks like leaving/interviewing is when I learn. I spent sometime cataloging my manager Habib Nahas' activity on Slack (only two week's history), and it provides concrete example of how to be a manager. It is very "abstract" to explain the importance of setting clear expectations, but it is important to see how somebody actually do it. In this example, Habib creates clarity of expectations through expected outcome of the StripeSat review meeting
- In terms of engineering leadership, from studying Dmitry and Habib's observable behaviors, I noticed that they usually work on things that I intuitively don't want to work on, the issues that I try to avoid. Those are actually the same issues that everybody try to avoid, and that's where we need leaders to step up, because everybody is looking up for the leader to take on those issues. For example, Dmitry came up with a doc about silent data corruption issue that nobody is interested in, or capable of investigation, and ask for further comments and ideas. Nobody asked him to come up with that doc, but it is a good example of engineering leadership for raising the bar, closing the loop.
- Databricks is concerned why I didn't get a promotion when I was at Airbnb for so long. Last year they were concerned with my time at Hulu.
- After a week of onsites, by 11/02 after I finished all scheduled onsites, I all of sudden lost all motivation to continue learning and leetcoding. I still have a possible opportunity with Apple that I will chat tomorrow (11/3), but I felt I have lost motivation to continue preparing for it. Not sure why. It is possible that this happens for every job searching period. It also be possible that I have a month of fever now and I am physically weak. 
- During onsite interviews, looks like I always make the mistakes of thinking in "big data" when a "small data" solution may work. I should always start with a "small data" solution in system architecture questions first.
- I probably should study the LinkedIn Jobs search for "staff engineer" regularly so I get a sense of the job market.
- **I should practice regularly (weekly?) for staff or manager interview questions, maybe 2 hours on every Friday, in the form of retrospective.** 
	- What do I do in this weekly 2 hours? There are so many things I want to learn, from studying documentations and other leader's communications, to learning from shipmails and hope I have time to chat with the team who did the work to get more context and learn from them. 



## 2023-11-20
Slack Recruiter Call
- Putting together an offer.
- Not confident with the numbers. 
- Current state: verbally, not want to make it official 
	- L9 staff at the company. Base: $280k, 20%. 
	- Sign-on bonus: $56k.
	- Equity: $500k RSU. Annual refresher.
	- Unlimited PTO. Very good WLB. 

## 2023-11-21
Summer.io
- CEO: Mike Godsey. Founded last year. Small team of 7. Seed funding $7million
- Runway? Sept 2025, to scale the team to 13 people by June.
- We are still building the first version. Plan to introduce private testing.
- Business model: usage based model for now.
- How to compare to DOMO. 
	- We plan to hand-held.
	- You need to be data savvy.

AMC Theater
4500 9th Ave NE
Seattle, 
Call me at 1pm.

## 2023-11-20
Slack Recruiter Call
- Putting together an offer.
- Not confident with the numbers. 
- Current state: verbally, not want to make it official 
	- L9 staff at the company. Base: $280k, 20%. 
	- Sign-on bonus: $56k.
	- Equity: $500k RSU. Annual refresher.
	- Unlimited PTO. Very good WLB. 

## 2023-11-17

Tiktok Interview: one of the techlead on the team, supporting any features on TikTok, analytics tools, data science team, and algorithm team. data product manager, data architecture, data governance, multi-IDC data architecture (collab with Signapore). 
- How big of the team? data engineering / data infra layer. 14 - 16 engineers (building on top of data infra). Big Data Tooling
- TikTok is building an IDE for big data tooling!! 
- Data Solutions: 80% of the team are migrating to USA, so there will be less evening/morning meetings. Every week, one or two meetings after 7pm. For Data Architecture team (which I may be a better fit).
- Business travel is very common. Max stay in China is about 2 months (mainly Beijing or Shanghai office). The business needs is to meet stake holder in Beijing/Shanghai. You could work remotely in Shenzhen for 2 weeks and then take PTOs.
- Tech Lead Manager need to lead a team of more than 5 engineers. The expectations is to be able to build something from scratch. Have clear roadmap, play TPM role.
- Teach Lead is 3-1
- WeChat: shensun001, LinkedIn:Aaron Shen
- WLB: depends on teams. During some time with lot of reorgs, many people choose to work very late. Business owners are aggressive. I suffered a year. Now we changed hiring strategy.
	- Team lead, more people to support, high priority: expect 40 hours a week. If you are short of hands in your team, 50-15 extra. 
	- Our team now mostly self-pace.
	- 45-person team, still have 7 HC.
	- Used to work 1 day every weekend. Now I can take 2-day weekends.
	- data mesh.


Maven Clinic Interview
- Chong Qiu
	- work in platform, build company-wide infrastructure service. Eg. database, common library. Cron job system.
	- 3 team for platform: devops, core service team, and data team.
	- Data Team: ELT (instead of ETL). Use dbt. 
	- 220+ total employees. 
	- WLB is OK.
		- On-call can be busy and wake up at night. 
- Rong Chen
	- been here for 10 months, doubled engineering count in this 10 months.
	- Amazon, MS, Google, BoA.
	- WLB: pretty good, 8h, oncall low load.
	- Data Team: new team created this year, less than 10 engineers. GCP, dbt (because they like SQL)

## 2023-11-16
Tecton.ai Recruiter Call
- Questions: 
	- total employee/engineer HC? growth?
	- raised $100m in 2022 with 80 employees. Now a little over 100 employees, taking measured growth. 
		- A: 409a stayed the same. next raise will be in 2025.
		- We have a good forecast.
	- 130 customers for next round. We have 40 customers now.
	- Tecton offers options, not RSU.
- L5/L6 Staff role
	- Base: $216,000/yr - $258,000/yr. Hire at 75%.
	- Equity: options, not RSU. 
	- Two perf review per year. 
	- Compute Team: is the core product.
	- Talk to Rohit.


## 2023-11-15

BlueSky Data
- Yi's research:
	- $8.8m in September 2022 funding.
	- First product: Snowflake workload usage and cost as well as actionable insights and recommendations.
	- Zheng Shao was CTO for 10 months: I met him at Airbnb when he was hired as a consultant.
	- Wants to go beyond mere cost visibility to provide deep insights into how data is being used.
	- Core tech: query patterns, suggest high-impact tuning options. Tuning data layouts and warehouse settings. The last step is to have an optimization engine that automatically does this for you.
	- The product is built around optimizing SQL queries, plans to apply same approach to other data products like Databricks.
	- The idea is to delete workloads that are costing cash but don't add a lot of value.
	- Buy one of the best health insurance plans for all employees and their families, luxury plan.
- Yi's question:
	- How do you do with delete workload that don't add a lot of value?
	- How do you sell "cost saving" products to enterprise users?
	- How much runway? What's the next milestone for next funding round?
	- How is it different from Pepperdata?
- Mingsheng Hong
	- We don't look at user's data.
	- Best fit team members need to be passionate about the mission.
	- Motivation: passionate.
		- That's a sign you are not a good fit with early stage company.
		- We are looking for people who are willing to sacrifice. 
	- 

## 2023-11-13


Tiktok Recruiter (Kevin)
- Interview Process: you can only interview one role at a time. You can still be considered for another role if you get rejected by a role (but feedback from that role still considered)
- The role I have now are mostly IC role. 
- I have a TL role from a different role, for experimentation team. More focused on providing data, A/B testing.
- There is a large focus on e-commerce. Tiktok shop. 
- https://careers.tiktok.com/position/7273229223958759738/detail
	- This team is in US. Evening/morning meetings are less frequent. Higher manager is still in China.
	- Support 80% of data needs for TikTok (20% from embedded data teams)
	- mostly a Java shop
- Fully return to office. We are based in Bellevue.

Maven Clinic Recruiter Call (Michelle Ullman)
	- 3-4 years from IPO
	- interview process takes 2 weeks.
	- Staff, up to $255k/year. Senior Staff: close to $290k/year
	- Director of Data is based in California
	- Layoffs: zero layoffs in the past 2 years. Last round last November Series E, $90 million. 450 clients, signed up Amazon recently, we provide support over 100 countries. 70% margin. 2x growth year over year. Hiring is conservative.  Last quarter hired 20 engineers, this quarter hiring 6. Director of Data is Steven Zhen (was at Hippo, Lyft for long time).
	- Total 580 employees, about 165 engineers.
	- Product: follow women and their life.
	- Data Team: streaming, data platform, hope to double up data size by the end of next year (by doubling client base)
		- Need data warehouse.
		- Data insights.
		- 6 engineers in the data team, hope to hire 2 this quarter.
		- We are a Python shop
	- WLB
		- People have children would block calendar say kids picking up and drop-off.
	- Yi's questions:
		- Looks like glassdoor review says there is a lack of diversity: mostly white engineers.
		- What about return-to-office policy regarding my role?
		- Unlimited PTO is REAL, and employees are strongly encouraged to take at least a week per quarter minimum

## 2023-11-09
Firebolt Recruiter Call
- The current role is in the compute engine, focusing on infrastructure, working with kubernetes, building production cloud.

Bluesky Data Recruiter Call (Sandra Petit)
- Sandra is new at the company, for 7 weeks.
- Seed stage, raised $8.8 million. Do not quote on me, still have a year and half runway. Looking to raise another round early next year. In Q3 we tripled our recurring avenue. ARR.
- Currently 20 full time employees, with 10 of them being engineers. It's flat structure, everybody reports to CEO. Data warehousing and query optimization.
- Currently 2 tech leads. Baiji Hei
- Recently brought on two engineers. 
- Hiring opportunistically.
- Cofounder and COO both have children, both have kids pick up drop off block in calendar.
- We are a remote first company. We have an office in Santa Clara
- Base Salary and Options
	- $160k to $210k base salary
	- 0.5 - 0.8% share of the company in equity.
- TODO:
	- Sandra to schedule an informational with either CEO or Baiji (techlead)

## 2023-11-07
- HighTouch recruiter call with Sara
	- Only recruiter at HighTouch, been here for 2 years.
	- Managing 8-9 engineers. You will stay close to tech, doing design reviews, product roadmapping.
	- The team grow to this size over the Summer.

## 2023-11-06
Apple: Stan Ignatev. Design
- Intro: analytics, we focus on tooling, we don't create models, we focus on performance, partition data, scala libraries, flink libraries. Spark problem.
- Report to Bernad. He manages too many people. He somerimes have to work on weekends.
- DRI


## 2023-11-02


Slack Onsite Day 2
- Sarah Henkens (Software Engineering Architect)
	- ML Infra team. 4 years. Cali
	- Debugging, Incident Management.
	- How to ramp up fast?
		- We have so many articles written. 
	- Remote: team onsite twice a year.
	- Salesforce/Slack: there is a culture shock. We need to fit in to the larger culture.
- Mahendran Vasagam, Jigar Bhalodia (1+ year)
	- Hive and Spark, managed service for internal teams. Trino. S3
	- Why you like Slack?
		- data lake model and moving to data lake model
		- Offsite 2-3 times a year.
- Nav Shergill
	- Staff Engineer: expectation is the same: influence roadmap, vision, 
	- You are driving without authority. It is up to you . I am looking for a person to help the team to be a bit more organized. (team lead architect). That will be very helpful for me. I know what need to be done, but I am spread too thin, helping me scale myself.
	- I am not the expert, but I found myself having to drive the projects.

## 2023-11-01

Databricks Onsite: Li Xiong (Sr. Engineering, Manager)
- From Microsoft Azure
- Most likely I will report to him.
- Challenge in recruiting
	- No promotion over 4 years.
	- May talk to previous manager (Guang)
- Is this role for your org?
	- Team Money: compute the revenue.
	- We are software engineers, process the data, use databricks, ETL and 
	- Customers to pay two bills, AWS, and Databricks.
	- 17 engineers total, the org was started last April, with 2 engineers. 30% engineers are staff engineers.

Figma Onsite: Zubair Saiyed
- bootstrap data infra team, developed the original deliberate ask from the leadership. Now we are looking to figure out what to do next.
- boundary of staff engineer and the EM
	- We have a huge green field. I want the staff engineer to surface these areas and 
Figma: Darren Tsung
- protobuf
- 

## 2023-10-31
William Li
- been at Figma 2 years.


## 2023-10-30

Slack Onsite Interview
- Deepak Agarwal - Data Ingestion, one of 5 teams (orchestration, data ingestion, data tools.
	- 50+ EMR clusters, in all regions
	- Interactive workloads: trino/presto on k8s
	- routing layer for EMR.
	- Recently upgraded EMR, to Spark 3.x.
	- Currently moving from EMR to EKS (for more cost savings)
	- Developed a routing layer for all compute engine.
	- Developed a service to manage AWS roles, etc. A golang service to spin up new clusters.
	- Responsible for all data warehouse for Slack.
	- Customers are other internal teams.
	- Ranger, also own logic.
	- Real-time
	- CDC continuous ingestion. Hoodi. 
	-  5+ years.
- Stan Babourine (principle engineer)
	- Ramping Up: onboarding training. Slack channel has all the information.
	- What failure modes?
		- not in this team, in general, senior engineers do a lot of great work. Staff engineers, they fall into senior engineer role, solving specific problems, rather than seeing big pictures. 
		- How to demonstrate impact for staff/senior staff? 
			- I would rather you (EM) see the impact of my work 12 to 18 months from now.
			- Staff:  6 month.

Figma with Jenna
- 4 more interview sessions split in the next two days. Tomorrow will be technical heavy ones, including an architecture and system design type question, similar to my interview with Adam (positive feedback: great at requirement collection, and communication). 
	- Architeture
		- Will look at my technical communication, do not solving problems right away, make sure you understand the problem.
		- Problem solving
		- Product intuition: reason with customer needs. 
	- Coding Question with Stephen
		- Format will be the same with the last one with Erica: a real technical question, not from leetcode.
		- Advice: think about the time and pacing. With Erica, I ran out of time. Ask if there are multiple parts of this problem. 
	- Non-tech session with HM: behavior. Look at the two links in my email, related to Figma core values blogs: craftmanship, collaboration, conflict resolution, give or receive feedback. How you grow the people around you, in both technical and relationship, examples of mentorship. Example of how I grow myself, out-level myself. Growth mindset is important. What do you do outside of your day-to-day responsibilities (like enrichment actdivities). I think I helped engage Airbnb to work with Stripe for two projects (ML Infra, and Minerva)
	- Last interview: technical deep-dive. Drive a deep discussion on a project I've worked on in an organized manner. Looking for strong signal for technical communication, challenge I saw. Look for large scope and deep challenges. Choose a large project within the last 5 years.
		- Think about what I did at Airbnb (either DIO, or cost attribution)
		- It's OK to bring a slide deck (I have that from Stripe's interview)
		- Frameowork:
			- start with business problem
			- Get into the solution itself, why it is hard, different methods we have tried. talk about trade-offs, considerations before th
			- Talk about the result. What's the impact to the company, and to the team. What would I do differently if I do it again.
		- Darren interviewer:
			- He will look for how the project is designed. Shapes of the design.
			- If I have a wholistic design, and low level details.
			- Impact and Scope.

## 2023-10-27
- Haogang Chen: working on unity catalog, data governance team, been at Databricks for 7 years
	- How to ramp up? onboarding buddy. onboarding docs
		- L6: ramp up within a quarter
	- failure mode for staff engineers.
		- easiest to fail is just keep talking and don't fix things. We are action bias. It is not enough to just talk about we should fixing things. You need to demonstrate that you will make forward progress.
	- Parent:
		- I will have my second kids.
		- I don't think it is an issue in the team.
		- Most L6+ folks have kids. Block the calendar if you need to pick up kids.
- [Priyam Dutta](https://www.linkedin.com/in/priyamdutta) System Architecture
	- Advice for ramping up:
		  - ask questions, stupid questions.
		  - 

## 2023-10-26
Salesforce Recruiter Lisa
- Looking for somebody join ASAP.
- Closer to Bellevue.
- I should continue with Slack interview first, and then follow up.
- RTO: 10 days per quarterly, by team may ask for more.
- TODO: reconnect after Slack interview.

HighTouch Recruiter: Ryan Anderson
- 100 total employees.
- Doubled customer number in past 18 months.
- Core team: manage 5 people. The other team has 3. They run team very lean.
- Looking for people who can handle the chaos. 
- Help non-technical users to sync data from data warehouse to SaaS tools.
- Base: $240k. 
- Fully Remote, some people in SF. They don't care about employees location.
- Interview process:
	- Intro to their in-house recruiter.
	- HM screen.
	- Leadership & tech interviews.
	- Meet and Greet with the team you manage.
	- 2-3 weeks of whole interview process.
- This Role:
	- Strong backend experience.
	- Not necessarily hands on, but must have deep engineering knowledge.
- 

- Looks like leaving/interviewing is when I learn. I spent sometime cataloging my manager Habib Nahas' activity on Slack (only two week's history), and it provides concrete example of how to be a manager. It is very "abstract" to explain the importance of setting clear expectations, but it is important to see how somebody actually do it. In this example, Habib creates clarity of expectations through expected outcome of the StripeSat review meeting
- In terms of engineering leadership, from studying Dmitry and Habib's observable behaviors, I noticed that they usually work on things that I intuitively don't want to work on, the issues that I try to avoid. Those are actually the same issues that everybody try to avoid, and that's where we need leaders to step up, because everybody is looking up for the leader to take on those issues. For example, Dmitry came up with a doc about silent data corruption issue that nobody is interested in, or capable of investigation, and ask for further comments and ideas. Nobody asked him to come up with that doc, but it is a good example of engineering leadership for raising the bar, closing the loop.
- Databricks is concerned why I didn't get a promotion when I was at Airbnb for so long. Last year they were concerned with my time at Hulu.
- After a week of onsites, by 11/02 after I finished all scheduled onsites, I all of sudden lost all motivation to continue learning and leetcoding. I still have a possible opportunity with Apple that I will chat tomorrow (11/3), but I felt I have lost motivation to continue preparing for it. Not sure why. It is possible that this happens for every job searching period. It also be possible that I have a month of fever now and I am physically weak. 



## 2023-11-03
Apple EM Bernard / HM
- EM at Apple for the last 4 years. Lead a team that is growing significantly last 12 months.
- This new role responsibility:
	- Responsibility: data ingestion from devices, providing the data to data stores.
	- GDPR integration with a larger system at Apple.
	- New program from last year, to start address the question of how we can provide a better platform to engineers. Established very complex and large number of pipelines. It is difficult to scale: how to continue to provide data sets and data processing while still maintaining data pipelines. 
	- understand the implication of a job issue and how it impacts the downstream datasets.
	- Someone who can take a strong leadership role in this space, and really execute the promise. 
	- A lot of involvement with customers. I don't have the bandwidth.
- 

## 2023-11-02


Slack Onsite Day 2
- Sarah Henkens (Software Engineering Architect)
	- ML Infra team. 4 years. Cali
	- Debugging, Incident Management.
	- How to ramp up fast?
		- We have so many articles written. 
	- Remote: team onsite twice a year.
	- Salesforce/Slack: there is a culture shock. We need to fit in to the larger culture.
- Mahendran Vasagam, Jigar Bhalodia (1+ year)
	- Hive and Spark, managed service for internal teams. Trino. S3
	- Why you like Slack?
		- data lake model and moving to data lake model
		- Offsite 2-3 times a year.
- Nav Shergill
	- Staff Engineer: expectation is the same: influence roadmap, vision, 
	- You are driving without authority. It is up to you . I am looking for a person to help the team to be a bit more organized. (team lead architect). That will be very helpful for me. I know what need to be done, but I am spread too thin, helping me scale myself.
	- I am not the expert, but I found myself having to drive the projects.

## 2023-11-01

Databricks Onsite: Li Xiong (Sr. Engineering, Manager)
- From Microsoft Azure
- Most likely I will report to him.
- Challenge in recruiting
	- No promotion over 4 years.
	- May talk to previous manager (Guang)
- Is this role for your org?
	- Team Money: compute the revenue.
	- We are software engineers, process the data, use databricks, ETL and 
	- Customers to pay two bills, AWS, and Databricks.
	- 17 engineers total, the org was started last April, with 2 engineers. 30% engineers are staff engineers.

Figma Onsite: Zubair Saiyed
- bootstrap data infra team, developed the original deliberate ask from the leadership. Now we are looking to figure out what to do next.
- boundary of staff engineer and the EM
	- We have a huge green field. I want the staff engineer to surface these areas and 
Figma: Darren Tsung
- protobuf
- 

## 2023-10-31
William Li
- been at Figma 2 years.


## 2023-10-30

Slack Onsite Interview
- Deepak Agarwal - Data Ingestion, one of 5 teams (orchestration, data ingestion, data tools.
	- 50+ EMR clusters, in all regions
	- Interactive workloads: trino/presto on k8s
	- routing layer for EMR.
	- Recently upgraded EMR, to Spark 3.x.
	- Currently moving from EMR to EKS (for more cost savings)
	- Developed a routing layer for all compute engine.
	- Developed a service to manage AWS roles, etc. A golang service to spin up new clusters.
	- Responsible for all data warehouse for Slack.
	- Customers are other internal teams.
	- Ranger, also own logic.
	- Real-time
	- CDC continuous ingestion. Hoodi. 
	-  5+ years.
- Stan Babourine (principle engineer)
	- Ramping Up: onboarding training. Slack channel has all the information.
	- What failure modes?
		- not in this team, in general, senior engineers do a lot of great work. Staff engineers, they fall into senior engineer role, solving specific problems, rather than seeing big pictures. 
		- How to demonstrate impact for staff/senior staff? 
			- I would rather you (EM) see the impact of my work 12 to 18 months from now.
			- Staff:  6 month.

Figma with Jenna
- 4 more interview sessions split in the next two days. Tomorrow will be technical heavy ones, including an architecture and system design type question, similar to my interview with Adam (positive feedback: great at requirement collection, and communication). 
	- Architeture
		- Will look at my technical communication, do not solving problems right away, make sure you understand the problem.
		- Problem solving
		- Product intuition: reason with customer needs. 
	- Coding Question with Stephen
		- Format will be the same with the last one with Erica: a real technical question, not from leetcode.
		- Advice: think about the time and pacing. With Erica, I ran out of time. Ask if there are multiple parts of this problem. 
	- Non-tech session with HM: behavior. Look at the two links in my email, related to Figma core values blogs: craftmanship, collaboration, conflict resolution, give or receive feedback. How you grow the people around you, in both technical and relationship, examples of mentorship. Example of how I grow myself, out-level myself. Growth mindset is important. What do you do outside of your day-to-day responsibilities (like enrichment actdivities). I think I helped engage Airbnb to work with Stripe for two projects (ML Infra, and Minerva)
	- Last interview: technical deep-dive. Drive a deep discussion on a project I've worked on in an organized manner. Looking for strong signal for technical communication, challenge I saw. Look for large scope and deep challenges. Choose a large project within the last 5 years.
		- Think about what I did at Airbnb (either DIO, or cost attribution)
		- It's OK to bring a slide deck (I have that from Stripe's interview)
		- Frameowork:
			- start with business problem
			- Get into the solution itself, why it is hard, different methods we have tried. talk about trade-offs, considerations before th
			- Talk about the result. What's the impact to the company, and to the team. What would I do differently if I do it again.
		- Darren interviewer:
			- He will look for how the project is designed. Shapes of the design.
			- If I have a wholistic design, and low level details.
			- Impact and Scope.

## 2023-10-27
- Haogang Chen: working on unity catalog, data governance team, been at Databricks for 7 years
	- How to ramp up? onboarding buddy. onboarding docs
		- L6: ramp up within a quarter
	- failure mode for staff engineers.
		- easiest to fail is just keep talking and don't fix things. We are action bias. It is not enough to just talk about we should fixing things. You need to demonstrate that you will make forward progress.
	- Parent:
		- I will have my second kids.
		- I don't think it is an issue in the team.
		- Most L6+ folks have kids. Block the calendar if you need to pick up kids.
- [Priyam Dutta](https://www.linkedin.com/in/priyamdutta) System Architecture
	- Advice for ramping up:
		  - ask questions, stupid questions.
		  - 

## 2023-10-26
Salesforce Recruiter Lisa
- Looking for somebody join ASAP.
- Closer to Bellevue.
- I should continue with Slack interview first, and then follow up.
- RTO: 10 days per quarterly, by team may ask for more.
- TODO: reconnect after Slack interview.

HighTouch Recruiter: Ryan Anderson
- 100 total employees.
- Doubled customer number in past 18 months.
- Core team: manage 5 people. The other team has 3. They run team very lean.
- Looking for people who can handle the chaos. 
- Help non-technical users to sync data from data warehouse to SaaS tools.
- Base: $240k. 
- Fully Remote, some people in SF. They don't care about employees location.
- Interview process:
	- Intro to their in-house recruiter.
	- HM screen.
	- Leadership & tech interviews.
	- Meet and Greet with the team you manage.
	- 2-3 weeks of whole interview process.
- This Role:
	- Strong backend experience.
	- Not necessarily hands on, but must have deep engineering knowledge.
- 


## 2023-10-25
- Apple Interview.
	- My Role: Streaming, Flink system and user experience., Stream processing.

## 2023-10-23
Code interview with ServiceNow
- What's the failure mode for staff and senior staff engineers?
	- Answer: there has been no failures. Good hiring. Looks like they are all successful.

## 2023-10-21
Actually writing code
- Implement https://leetcode.com/problems/132-pattern/editorial/
- Implement https://leetcode.com/problems/shortest-path-visiting-all-nodes/


## 2023-10-20
- Amazon recruiter: supporting last mile delivery technology team (big org), fulfillment, robotics, mapping system for driver. Had lay-offs and now we started hiring now, focus on high-level roles at the moment. For location, we have opening in Seattle/Bellevue area (including NY, Boston etc)
- Start with a senior engineer interview, and if we thinking you are better fit for manager or principle, we will add a couple of rounds of interviews.
- Managers: spend 50% of time writing docs for promotion, responsible hiring and developing the team. Usually a team of size 8 to 15.
- TODO: Yi to decide which role to interview (EM or Sr. Engineer)

## 2023-10-19
- Figma Interviewer: Figma Interview Adam Collins
	- App Platform, 15 months. Monolithic, at Reddit for 4 years, startups. 

## 2023-10-18
- AWS Recruiter Sree
	- Senior SDE, IAM team, highly available scalability distributed system.
	- Senior SDE, security, ML, Ai models to identify anomaly
	- Senior engineer, EC2 team, hardware, virtualization.
- Hightouch
- Tiktok (Shine)
	- Seattle Tech lead role, https://careers.tiktok.com/position/7278824732421900600/detail
	- Seattle office is hybrid role
	- We have a lot of teams based in China.
	- 45 minutes long interviews, including 2 coding round, 1 system design, and the 4th round could either be system design or behavior. We can move with your pace, like one round at a time, or we can do back to back interview.
	- Some interviewer are from China, using Chinese.
	- Meetings with China team?
		- Work out with the team. Possible to have meetings between 4pm-8pm. 

## 2023-10-17
- Medallion
	- This is the only open software engineering position, to backfill a person who wants to found a new company.
	- VP Engineering, 2 Directors of Engineering, 4 EMs, and about 35 software engineers.
	- Most engineers work about 50 hours a week.
	- $220k is the highest salary we can go. No bonus. Equity. 
	- Python is their main language, this is for a product development role
	- Decision: this is a mismatch (salary and role), let's keep in touch.
- Figma Interview on Thursday
	- It will be a system design interview.
	- Use an online whiteboard tool. 
		- Figjam
		- LucidDraw.
		- CoderPad.
	- Interviewer is looking for:
		- Technical communication
			- Mistakes: dive into design without asking questions. Use the first 5 minutes to ask exactly what the problem we are trying to solve before design.
		- Problem solving
			- bounce ideas with the interviewer, 2-way conversation.
			- Being able to talk about trade-offs.
		- Product intuition.
			- Reason about technical decisions. Explain technical decisions and how that affect users.
- Feedback from phone screen: Erica
	- Minor bug errors that needed hints.
	- Very thorough and think about different implementation.
	- Talk too much time on my part, ran out of time in the end.

## 2023-10-13
- Found a list of interesting System Design interview questions and answers: https://www.designgurus.io/course-play/grokking-the-advanced-system-design-interview

- ServiceNow interview with Director: Luiz Bucci
	- Overseeing the data streaming company, include different products and projects. Help customers replicate data externally, also development own time series database, we are very successful.
	- This position is for the core streaming team. Enabling Kafka as a service at ServiceNow. The new effort for the next version of ServiceNow, to provide kafka (and flink, etc) as Service, Make kafka service self service.
	- Core team of 5 engineers. 
- Role: Senior Staff Engineer, Data Stream team (responsible for Kafka)
- Founded at San Diago, 3000 engineers here.


## 2023-10-05
- Slack interview for Senior Staff engineer, Senior Manager: Nav Shergill
	- Question: what are you most passionate about?
	- team of 9, scope: EMR, flink, spark, including 3 staff engineer, 3 senior engineers, etc


## 2023-09-28
- 

## 2023-09-25
Interview with Zubair Saiyed, Data Infra EM
- Self Intro
	- Started in web dev, moved to backend (full stack developer), monitoring systems (data pipeline), big data. Went through insight data engineering training crash course. Spark/Kenesis/Kafka. Teach data engineering.  Early stage ad, real time bidding.
	- Adobe acquisition announced, not completed.
- The Team and the role
	- DI team: the motivation: (1) data science team ended up doing a lot of infra level work, data leadership (2) try to keep operational overhead down, today use a lot of vendors. The bill from third party vendors become unsustainable.
	- 1 year later, I took over the operational overhead (snowflake and data integration services). we are managing data governance, reduce cost, a service (Golang, Kenisis)that ingest data into data warehouse, parquet, landed in S3.. The cost dropped 80%.
	- For the team, 5 ICs. This May is an inflection point for the team. We need to figure out our future identity. We need to figure out the highest leverage and impact. We also need to make foundational investment. Ensure infra can continue to scale. Improve data governance, access control, data discoverability. DS/ML team (through acquisition) will become a larger consumer of the data platform. Reverse ETL (from data warehouse to online database). 
	- What I am looking for:
		- We are in need of an experience engineer in the space of Data, for strategy and vision. We need to figure out the right sequencing.
- 


## 2023-09-23
- It's been 40 days since I started this round of preparation. I started looking at questions by types (all questions using backtracing etc), and I found it helpful to develop an intuition. 

## 2023-09-21
Found a long list of Leetcode DP problems: https://leetcode.com/discuss/study-guide/1000929/Solved-all-dynamic-programming-(dp)-problems-in-7-months./900006


### 2023-09-22
Talk with Sabitha, AWS Recruiter
- Data role was filed internally recently, due to back to office and people change teams.
- Open roles: 
	- Distributed system, networking focus in EC2 team.
	- Block storage. EBS team, L5. The product PHYSALIA. 
	- Data Plane and Control Plane.
	- Rust, Networking, Distributed System.
	- Embedded Systems.
	- Security.

### 2023-09-20
Slack recruiter Xavier
- Slack Review 4.2 overall on Glassdoor, 4.1 on Blind
	- Blind Review 4.5 for WLB!!, 4.1 Company Culture.
- Data Infra Team: 
	- Team of 7. 4 staff engineer, 3 seniors.
	- own 13 services, migrating from EMR 5 to EMR 6.
	- Delta Lake Iceberg, Trino. Driving roadmap. 25% coding for Senior Staff. 50% coding for Staff.
	- AWS stack. Airflow, Hadoop, Hive, Kafka, Flink.
- TODO: apply this position.
- Interview Process
	- 3 Technical rounds
	- 2 behavior rounds

### 2023-09-19
Interview with Human Interest: Shabu
- Had a large team at Workday, moved to Human Interest a bit more than a year ago.
- This Opportunity
	- Business opportunity is quite large. Only half of US employees can participate in 401k plan.
	- Usually SMB, 1 - 50 employees. 
	- Double participant count every year. Partner with payroll providers. We have over 50 integrations.
	- The company is about 5 years old. They farmed out the backend to other companies (e.g. LT Trust for record keeping). 3 years ago, the company build record keeping system in house to improve margin.
	- Interesting Open Roles:
		- 1. Tech opportunity: Domain specific services. Horizontal scalability, SoA.
		- 2. Automation, lean to machine learning. Automatically detect issues, and self correct.
	- I have 4 teams.
		- Portfolio team
			- AEM Billing
		- Money Out Team
			- 401k loan, 401k roll over to new employer.
		- Transactional, Order Management
	- The Staff level engineer
		- Cross-team ownership. In some company its principle.
		- We have principle engineer now.
		- Eng 5(staff), Eng 4 (Senior II),  Eng 3(senior) can lead 102
		- 80 engineers total in company, 20 in my 4 teams. I have 2 staff engineers, hiring the 3rd. Total 8 across the company.
		- The Staff engineers are embedded into teams, but reported to me directly.
			- Large initiative, helping the whole team to improve processes.
		- 
	- Interview Process (4 steps)
		- This role is still hands-on. About programming language, we use Typescript/Node. We don't have expectations on language when you come in. Just have your own IDE to write the code.
		- System Design. Do think about the operational aspect of it.
		- Behavioral. 
			- Accountability, getting things done, giving and receiving feedback. 
			- Look for an example from your past.
		- Staff level interview: cross-functional collaboration, with director of product. Technical roadmap and product vision. Production support. Balancing tech debt and features. 
	- We are planning to IPO in a couple of years. We are already profitable, we are only hiring for growth. We haven't had any lay-offs 30-40% growth this year. 
- You may be leveled as staff, or senior 2.


### 2023-09-19

Interview with Sr Manager Data Platform, Gaurav Gupta
- ServiceNow has an office in Kirkland
Questions to Ask:
- Gaurav
	- IT Service Management (started as a ticket system). Started out as an ORM model. HR, Workday, Customer Service Management. End customers like Netflix.
	- The power of the business comes from the data platform, with very flexible data model.
	- More than 10k customers. 
	- A basic data platform is: MariaDB with Tomcat Java service on top of it.
	- Every customer get their own technical stack, so it is not multi-tenant. 10k customers, 250k installations.
	- Isolation: small blast radius for incidents. 
	- The downside: maintaining all these 250k installations.
	- I represent the Data Platform Persistence tier: abstraction over different database engine (MySQL, MariaDB, PostgreSQL)
	- The group I belong to: we have 4 teams, 40 members, 10 each team, by next year each team will grow 50%.
		- Data Access team: owns the SQL query layer.
		- Scaling databases: to avoid Run out of disk space of one host. Shard the databases. The code runs in hibernate layer.
		- Data Management Team (led by me). Data lifecycle management of an instance. Archiving, Rollback, adding index for large table. This is the type of problems we deal with.
			- Offload work from the instance to S3 storage. When tables are too big, deleted data will not free up the space. Data becomes fragmented. 
			- 10 HC
		- MariaDB database team. We release our own patches for MariaDB. 
			- Data Scale: we bought a company 2 years back, based on enoDB, does not scale for our requirements. We bought Swamp64 from Germany. They work on postgresql. We certified postgresql is our choice of database going forward.  They can do both analytical and transactional workload on postgresql. on 2GB of Java heap space (for cost efficiency purpose). Driver code, changes to JVM.
- Gaurav
	- 
- How big is the team? 
- What's the expectations of the role?
	- This is Senior Staff level. I have Senior Staff now, 4 Staff, 3 Senior, and 3 IC. 
	- Senior Staff, Principle: technical skill is the same. The difference is in structured thinking. That "Principle" engineer can make the call that what to invest, what not to invest. 
	- A Principle engineer in my team will look at all the problems. How do you know when to use what technology. I want my principle engineer to have strategy on what projects we can do in the next couple of years. A Senior Staff engineer can take one set of the problem. Have a strategy for a customer. 
	- Senior Staff and Principle is close partner with the manager, talking once every other day.
- What's the current challenge?
	- 
- What's the operational workload?
	- 
- How do you run operations?
	- 

### 2023-09-18

Meeting with Roblox HM: Lu Chen
- Returned China 2 years ago. Google, Facebook. Now work on ML. 
- Role Introduction:
	- I am open because I have teammates from infra. 
	- Joint venture, long term to move roblox platform to China.
	- We are certified to go online in China.
	- We are not online yet. We are doing both USA and China features.
	- Trust & Safety: ensure content is positive. We don't make games ourselves, we let the players to make games. Our role is to audit the user generated games. 50% of games are audited by AI, the rest are manual. We hired 2-3000 auditors. They login backend, and each audit task shows up as a ticket. Outsourced auditors, dashboard to show each outsourcer. We want to build optimize (assign tickets to people who are good at something). 
- The Role is a team lead for the tooling team.
- Meeting every day with US team. Responsible to communicate with US team (Data scientist and PM are US based), alignment, dependency. 10 team members. Most experienced with 7 years experience (MS and Google in Seattle), half are fresh grads with 2-3 years.
- WLB: our culture is following silicon valley, 7-9am meetings with USA team, meeting from home. Then come to office. I don't expect people sitting on the desk. We don't work on weekends. I feel many people feel WLB is good. Every 6 months there is an opportunity to visit USA. The US office culture is closer to Google (instead of Facebook). I think WLB, we are top 3 in WLB. Otherwise, Microsoft, Google.
- Why hiring from USA?
	- Because I want somebody who can be responsbile for communication with USA team. Not only English, but also thinking process. 
- What's the scope of Team Lead?
	- Need to be able to get projects from USA.
	- Expectations:
		- Expected to deliver features with coding (at least 50%), and should be more difficult features.
		- coach other engineers.
		- Drive new initiative, get new scope 
- Tech stack
	- Golang, Python (deprecating C#)
- What's Technical challenges?
	- Offline to Online. We need to talk to operations a lot. Make their process easy. 
	- 自动派单系统. When you have a ticket, which one you assign it to, it's an interesting optimization problem.
	- Auditing 3D content with script.
- Coding Interview loop
	- Coding interview 
	- System Design and later will be interviewed by USA team
- Address: 南山区， 腾讯滨海大厦对面.
- Hiring from US based. Why?
	- MS and Google. They are coming back to China to get married.
	- A LinkedIn director, come back by himself, struggled a bit, and returned to US later.
	- I come back with wife, have green card. My family is in Beijing. I am the single child.


Meeting with Ditto Recruiter Rin Chon (Manager Role)
- Manage 8-10 people.
- It it not a tech lead role. We are not looking for hand-off people.
- Ditto: we are US based company, we have people all around the world, 24/7.
	- 90 - 100 people.
	- 3/4 are engineers, most are senior level engineers.
	- WLB: most engineering teams have family.
	- The EM may manage people in 5 different time-zone.
	- Two profiles for people you manage: RUST, and database engineers.
- Interview process: 
	- John, VP in Seattle, 30 minutes call
	- engineering interview
	- Finally, CEO (because its a management role)

Meeting with Habib
- He will start the official document for coaching plan. Looks like I have 4 weeks left at Stripe.
- He says forget about this R2 incidents. What I am missing is the operational leadership, consistently lead the team to improve operations.
- He says that I am good at engineering work, but in the foreseeable future, Stripe needs the staff engineers for organizational leadership skills, especially in the Spark team.

Meeting with Ebay recruiter Wes
- The linked job has expired: https://jobs.ebayinc.com/us/en/job/R0057567/Staff-Software-Engineer
- Ebay public info:
	- blind: 3.7 overall, 4.2 - work-life-balance, 3.6 > culture , compared to Stripe 3.5 overall, 3.0 > WLB, and 3.3 > culture
	- Levels.fyi for software engineer:
		- MTS 1: $261k
		- MTS 2: $293k
		- Senior MTS $404k
		- Principle MTS: $394k
- Meeting Notes
	- We have a tough time on compensation.
	- We have office in Bellevue, we are open for remote. This team is open for remote.
	- The highest is half of what you are making.
	- Interview process:
		- HM call
		- Technical screen
		- 3 rounds of virtual interviews.
	- Team
		- It's a small team. Two data platform roles open.
		- Team: 15 members. Senior, Staff, MTS 1, MTS 2.
- TODO:
	- Yi to send resume
	- Wes to send job description


### 2023-09-07
- Apple Interview questions: https://leetcode.com/company/apple/

### 2023-09-07
- Lakshmi
	- Querying data, bringing into data platform, devices, websites, store the data, real time, in batch fashion. Adhoc analysis. API. real-time and event driven architecture. 
	- Spark, Flink, Kafka, Trino.
	- Lots of committer for open source. 
	- This is a senior role, contribute to data strategy. roadmap. be a catalyst for the team.
- interview
	- 1 code challenge 60 minutes, java
	- virtual onsite, 4-hours, multiple people, coding, design, culture, how things work at apple. 

### 2023-09-06
Roblox
- Principle for safety
- EM from Instagram: Lu Chen.
- 20 engineers.
- Currently work global projects, work with San Mateo team
	- ML Engineer
	- Services.
	- Tools.
- Why we need a principle level?
	- There is a senior EM, grow to 20 engineers.
	- The EM does both people management and engineering
	- He is looking for somebody to help backend, as a team lead for 5 engineers.
	- It can go to EM1 in the future.
- May need to travel to US (a few months a year)

### 2023-09-05



Hubspot Recruiter Call
- Base salary: cap at 275k, RSU 300k. Total camp $400k/year
- Founded 17 years old,  CRM founded by MIT. Focus on SMB (vs. salesforce)
- Public company
- Over $1B in the bank.
- 6000+ employees, 1400 engineers. In Infra group, 180 engineers.
- Tech stack: HBase, SQL, elastic search, Java, Kafka,
- 60% employees are remote. Never be required to reallocate.
- We respect WLB
- Interview process
	- Code challenge with 3 hour limit
	- Shared screen with your own IDE
	- System interview, may need to make presentations
	- Hiring Manager interview, behavior interview. It's a she and she is Seattle based.

### 2023-08-30
Meeting with Andrew from Human Interest
- Leading 401k provider for SMB.
- Growing 2x year over year. 
- Last funding round 2021, raised $500m
- Looking to IPO in 2025. Expecting 10 to 20Billion
- Currently have unlimited runway.
- Building a word class engineering org. Eng leaders from Amazon. 
- We are looking for Staff Engineer, horizontal scaling, influence technical standard, SOA, performance, reliability, observability, coach and mentor senior engineers. 
- Andrew: I think WLB is good
- We are a remote first company.
- Base salary range: $240-$260 base. Equity annual vesting. Equity is options, not RSU.

### 2023-08-14
- signed up for leetcode again.
- [30-day plan 2022](https://leetcode.com/discuss/study-guide/2021884/30-days-interview-preparation-plan)
- [The Blind LeetCode 75 study plan for 4 weeks, updated for 2022](https://www.techinterviewhandbook.org/coding-interview-study-plan/)
- 