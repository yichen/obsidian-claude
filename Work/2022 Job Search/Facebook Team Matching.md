----


Cheng Hui
* When choose teams, look at how long the manager has been at FB. Longer the better.
* E6: the first couple of years may be very challenging because of the large scope. 
	* E6 in Data Infra: technical difference is not much different from E5. 
	* The main difference is in cross-team scope. You need to build relationship with E6s from collaboration teams, understand their challenges and roadmaps, build win-win situation. You need to be able to find scope for the team.
	* Internal E5->E6 is easier because they already have the relationships.
	* Example: E6 in my team, he eats lunch every day with another person.
* Facebook managers are more hands-off. They are not willing to fight for his own engineer's promotion. Instead, it is better to accept the no-promotion in exchange for better rating for himself (too aggressive to fight for his own team).


Lenni Kuff
* Monitor and observability Team
	* Challenge: AI/ML focus, we anticipate 10x increase in scale in the next few years. We need to figure out how to ingest and scale our systems. We are trying to build an internal infra-cloud data center, and give AWS like experience.
	* Capex
	* There is ton of scope and opportunity. We are growing the team.
	* One of our senior tech lead is the founder of Opentelemtry. The data model is different, so we do our own.
* E6 Failure Point
	* The biggest challenge is how to successfully ramp up, because you need to know more context compared to lower level 
w	* Advice: meet other teams, build a lot of context, don't come in and give directions.
	* Mini bootcamp for data infrastructure team, to explain the team in DI, and the current challenges. Why networking? If you are blocked, you know who to reach out to.
	* We are a social network company. If you have a big network, it will help you. I encourage you to build your network.
* WLB for parents
	* I have 3 kids. I always put family first whenever possible. For example, I set boundary that I need to have dinner with family.
	* If you don't make it explicit, it may not work well. For example, people may wonder why you are not responding when you are pick up kids.
	* For E6 that do very well. They have different profiles, two general buckets of profiles:
		* tech leads: they are good at leadership path, talking to partners, coaching junior members, creating more scope of the team, more aligned with EM roles. Good E6 are not expected to do it all by himself, but more federated with others (create more projects for the team)
		* strong subject matter expert, who code a lot, not interested in leadership aspects, and can get a lot done.  Fixers.
	
* I don't expect E6 to give me surprises. No last minute scrambles. More communication, clarity of communication is good skill especially for E6 and above. Good design doc (clarity of communication) is very important.
* Scope wise: E6 can think what it will look like a year out from now, able to talk abotu that distance in the future. E7 should be able to talk about how things looks like in 2 year.
* Infra team, there are more senior heavy (more senior level engineers)

Munir
* 2 years
* scube - realtime monitoring and analytics
* MPK
* WLB
	* You do control some of WLB, based on the rating system. The bar is higher at FB, so if you are accustomed to exceeded from other companies, the expectation is 
	* Work with your manager to set the goal for the perf rating.
	* E6: you need to figure out how to generate more revenue, or great product idea in 6-month to 1 year (3% of company get exceeded ). 
		* Greatly exceeded:
		* Exceeded: 30% of the company get exceeded. You have some goals, and you beat your goals.
		* Meet All: we expect you to meet 50% of your goals. It's not a negative rating.
		* Meet Most: about 5% of the company
		* Meet Some: its negative. bottom 5%
	* On-call: how often is the on-call, how often is the on-call.
* Ramp Up
	* Expect Meet Most.
	* The first 3 month, expect below the line performance
	* Expect 6 month to reach meet all.
* Failure mode
	* There are top-down priority push. The manager is more like an influencer, they won't dedictate what and how. The E6 needs to take the initiatives. So, during ramp up time, build your network, get exposed to user painpoints, and drive that with your manager.



Adwait Tumbde (big data observability)
* Looks like Molly mentioned that he might have offered to have me chat with a team memer.
* Good friend of Yi Pan.
* compared to LinkedIn, it is so much bigger. At LinkedIn, you have to do everything, at Facebook, the org is much larger, there will be a lot more cross function support
* LinkedIn focus more on let's do it right. At Facebook, the time to market is more important. E6 is to balance the long-term and short-term goals. People are friendly, more friendly. A lot more formal structures.
* WLB: from team to team, depending on candidate aspirations. LinkedIn is more promotion oriented culture. Meta is more perf review rating focused. 
* Software maturity: a few steps ahead of LinkedIn.
* Meta has more people with more technical depth.
* DI team
	* Priority: focus on AI, and privacy.
	* Observability (new team)
		* scalable processing of the data
		* lineage across the infra. for last mile problem, etc.
		* we started with many data engineers.
		* the team started last year.
* Biggest challenges
* Failure mode for external E6 hires
	* There will be ramp up time.
	* The support for learning tooling is much better than LinkedIn. You won't fight with the tools. The bootcamp helps.
* Operation vs. Dev load
	* more dev vs. ops, 50% time on operation during on-call duty. Expect 5-10 questions.
* WLB
	* When i joined, i have 9month old.
	* you will have to be more disciplined on managing the time. Who are good at guarding their time, they usually do well. 


Charlie - 
- 6.5 years, most recently become a manager.
- Data Intellgience 
- Data Infrastructure, building many data tooling (privacy, etc), observability, anomaly detection, forecasting, dashboarding etc.
- All my team in Seattle/Bellevue. Most in MPK (60%) and Seattle (30%). 
	- Half in remote, half hybrid
- E6 ramp up
	- Meta try to improve.
	- build on guard rail over a year.
		- start with small projects
		- eventually roadmaping
	- E6 is the only path to M1.
		- ability to partner with another manager, and can set directions for other managers (4-5 engineers), lead them, scope for them. 
		- E6 personas
			- TL
			- Fixer
			- Coding Machine
			- Documentation, scope, 
- Team Composition
	- Mentor.
- Work-life-balance
	- We expect them to 9-5, many are parents, we set clear boundaries and goals.
	- Use your manager as a resource, explain my personal boundary (time to pick up kids), set expectations. Work with the manager constantly, the manager.



Bandish - Spark Team

bandish@fb.com

* Spark team in Data Infra org
* Largest engine in Meta.
* 1.5 extrobytes per day.
* half billion a year in hardware cost
* Spark Team and new initiatives
	* forked open source, optimized query optimizer, shuffle service, rewrite c++ core engine, resourcemanager.
	* looking ahead, invest in ML. We are pivoting to team to be ML first. 
	* handreds of thousands of machine, how to do cluster management? 
		* The team is junior right now. We haven't started the project yet.
		* efficiency work, auto tuning spark jobs.
	* Shuffle service is one of the most expensive 
		* we created a solution that is 3x cheaper.
	* 4-6 month of wramp up time, expect:
		* understand the landscape.
		* work well with the team.
		* onboard buddy, E6 or 
	* Spark team: 2 E7 engineer. Later on a metor from E7. Most E7 from Google.
	* Larger org, 2 E8 for Spark and Presto.
* Hybrid/Remote
	* Most of team in Bay Area. Bandish is in Bay Area
	* 3 completely remote.
	* More and more will become in remote.
* Oncall
	* 3-day/4-day oncall for engine
	* 1-week oncall for rest.
* I can come join the Spark team, and then ramp up, and decide which team to join.
	* ramp up, 5-week bootcamp for company-wide tooling introduction.
	* then join a team, i get a few months for team's codebase, take a task, build credability.