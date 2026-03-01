# ServiceTitan Interview Notes

**Created:** 2025-09-02
**Status:** In progress - Multiple interview rounds completed

---

## Company Overview

### Business
- **Industry:** SaaS for home service industry (B2B)
- **Company Size:** 3,000 employees
- **Work Arrangement:** Permanently remote
- **Stage:** Growing, preparing for IPO
- **Market:** Primarily USA, starting to expand to Australia

### Leadership
- **CEO/President:** Available on YouTube, highly regarded
- **CTO:** From LinkedIn background
- **Culture:** High energy founder, aggressive delivery expectations

---

## Role Overview

### Position
- **Level:** Senior Staff Data Platform Engineer
- **Reports To:** Senior Director (Sumanth Jain, joined 3 months ago)
- **Total Compensation:** Mid $400k

---

## Initial Recruiter Call - Robbie Abraham (2025-09-02)

**Focus:** Growing data organization

---

## Interview with Sumanth Jain (Senior Director)

**Joined 3 months ago**

### Team Priorities - 3 Key Metrics
1. **Data Freshness:** Goal of <5 minutes (currently using Gold/Silver/Bronze layers which hurt freshness)
2. **Data Quality**
3. **Query Performance**
4. **Governance** (fourth priority)

### Team Structure & Growth
- **Current:** 15 members
- **Acquisition:** 5 people from acquired company (will merge)
- **Leadership:** 3-4 staff engineers, 1 principal
- **Future:** Adding 2 managers

### Team Organization (Future State)
1. **Data Infrastructure Team** - Storage, compute
2. **Data Product Team** - Query layer, data quality
3. **Data Governance Team** (future)

### Current Tech Stack
- **Database:** Multi-tenant database on Microsoft Azure
- **Ingestion:** Custom data pipeline, data replication
- **Warehouse:** Snowflake
- **Transformation:** dbt
- **Layers:** Gold, Silver, Bronze (hurting data freshness)
- **Transition:** Moving from batch to real-time

### Success Criteria
- Very hands-on
- Deliver impact in first 2 quarters
- Move fast: Get results in 1 quarter
- Velocity of delivery
- Enable impact for the team

### Hiring
- Hiring for: Senior Staff, Staff, and Principal levels
- Goal: Best-in-class data freshness and quality

---

## Interview with Swami Veeramani (Principal)

**Background:** Previously at LinkedIn

### Company Stage
- More in growing stage compared to LinkedIn
- "Not built for growth" - need to scale infrastructure

### Technical Strategy
- **Goal:** Move from Snowflake to open source solution

### Day-to-Day Responsibilities
**Short-term:**
- Enable business-driven quarterly KPIs
- Lots of meetings in first month of each quarter

**Long-term:**
- Architectural work

---

## Interview with Daniel Weiss (Group Product Manager) - 2025-10-03

**Role:** PM for Data Platform Team

### Team Details
- **Team Size:** 12 engineers
- **Focus Areas:**
  - Data ingestion (streaming and batch)
  - Data freshness improvement
  - New semantic layer for data (net new product investment)
  - External customers expect fresh data

**Separate Infrastructure Team:** Different team spins up infrastructure (like Kafka clusters)

### Work Environment
**Meetings & Processes:**
- Daily standups most days
- Each member has a focus area
- Working to establish on-call process
- Engineers break into work groups
- Weekly backlog grooming
- Weekly demos
- Team becoming a "more well-oiled machine"

**Work Intensity:**
- **Intense workplace**
- Founder has a lot of energy → aggressive delivery expectations
- A few times a year can be intensive
- People rarely work weekends/evenings
- **Not a company for people to rest**

### Why This Role?
- Company growing rapidly
- Lots of data platform work
- Team needs more capacity
- Next year has activities requiring more capacity

---

## Interview with James Giles IV (Engineering Manager)

**Background:** EM for Data Platform, 4 years at ServiceTitan via Convex acquisition

### Team Composition & Growth
- **Convex team:** 6 engineers (all North America)
- **ServiceTitan team:** 13 engineers (North America + Armenia)
- **Hiring:** Another 7 engineers
- **Total Future:** ~26 engineers

### Organization Structure
- **Parent Org:** Titan Intelligence
- **Two Pillars:**
  1. AI/ML
  2. Data Platform

### Team Responsibilities
- Control all application data from microservices
- Manage underlying infrastructure (topic ingestion, data marts)
- Note: Different org owns business metrics data
- Most computation in Snowflake
- No dedicated people for data infrastructure yet

### Tech Stack
- **Not heavily using Spark yet**
- **Primary:** Snowflake and dbt
- **Streaming:** Kafka streams
- **Migration:** PostgreSQL (from Convex) → Snowflake
- **Optimization needed:** Many queries running more often than they should

### On-Call
- **Improved recently:** Only actionable alerts now
- Getting paged, but incidents are calm

### Work Hours
**Armenia Team:**
- Start work at noon their time
- Work into later evening (US time)

**Pacific Time Team:**
- Most meetings 10-11am
- Some 9am project-specific meetings
- Later meetings to collaborate with Armenia team

### Key Opportunities
- Transform from cost savings to latency optimization
- Bring new capabilities into the system
- Primary collaboration with Dan (PM)

---

## Interview with David Stein (Principal AI Engineer) - Behavioral & Technical Strategy

**Background:** 1.5 years at ServiceTitan, previously at LinkedIn (left 2023 via layoff)

### Current Role
- Principal on AI Platform team
- Measuring AI agent performance
- Example: Agents answering phones for plumbers, scheduling appointments
- Previously worked on Data Platform

### Why He Chose ServiceTitan
**LinkedIn Context (2012-2023):**
- LinkedIn changed over the years
- Lots of people left
- Less interested in innovative work
- Got laid off in 2023

**Decision Factors (had 3 offers):**
1. **Really liked the leaders**
2. **CEO and President** - Watched them on YouTube, impressed
3. **CTO from LinkedIn** - Familiar background
4. **Hidden gem opportunity** - Friends hadn't heard of ServiceTitan
5. **Leaders understand the space**
6. **Large opportunity size**

**Retention Philosophy:**
- Will stay because of "how well I am treated"
- Not just waiting for IPO/stock gains (reference: Airbnb stock didn't grow much post-IPO)
- Reminds him of LinkedIn in 2012 (growth phase)

---

## Technical Architecture

### Current State
```
Microservices → Kafka → Custom Ingestion → Snowflake → dbt → Metrics
                                             ↓
                                    Gold/Silver/Bronze Layers
```

### Pain Points
1. **Freshness:** Gold/Silver/Bronze layers add latency (goal: <5 min)
2. **Cost:** Heavy Snowflake usage
3. **Query Performance:** Inefficient query patterns
4. **Scale:** Not built for current growth trajectory

### Strategic Direction
- Move from batch to streaming
- Potentially move from Snowflake to open source
- Build new semantic layer
- Improve data ingestion (streaming and batch)

---

## Red Flags / Concerns

⚠️ **Work Intensity:** "Not a company for people to rest" - aggressive delivery expectations
⚠️ **New Leadership:** Senior Director joined only 3 months ago
⚠️ **Multiple Migrations:** PostgreSQL → Snowflake, considering Snowflake → Open Source
⚠️ **Organizational Merge:** 5 people from acquisition still merging
⚠️ **Meeting Heavy:** First month of every quarter is meeting-intensive
⚠️ **Time Zones:** Armenia team creates later evening meetings
⚠️ **Fast-Paced:** High expectations for quick delivery (1-2 quarters)
⚠️ **Technical Debt:** "Not built for growth" suggests infrastructure challenges
⚠️ **Pre-IPO Pressure:** Preparing for IPO can create additional stress

---

## Positive Signals

✅ **Strong Compensation:** Mid $400k total comp
✅ **Permanently Remote:** Full flexibility
✅ **Large Scale:** 3,000 employees, growing
✅ **Real Problems:** Clear technical challenges to solve
✅ **Growing Team:** 15 → 20+ engineers (significant expansion)
✅ **Strong Leadership:** CEO/CTO well-regarded, CTO from LinkedIn
✅ **Clear Metrics:** Focus on freshness, quality, performance
✅ **Impact Opportunity:** 2-quarter timeframe for visible impact
✅ **Multiple Senior Engineers:** Not alone at senior level (3-4 staff, 1 principal)
✅ **Improved On-Call:** Only actionable alerts, calmer incidents
✅ **LinkedIn Comparison:** Reminds ex-LinkedIn engineers of 2012 growth phase
✅ **Treatment:** Engineers report being treated well
✅ **Market Opportunity:** Large addressable market (home services)
✅ **Product Investment:** Building new capabilities (semantic layer)

---

## Key Insights

**Cultural Fit Considerations:**
- High-energy, move-fast culture
- Aggressive delivery expectations from founder
- Not a place to "coast" or "rest"
- Similar to high-growth LinkedIn (2012 era)
- People stay because they're treated well, not just for stock

**Technical Challenge:**
- Interesting problems: freshness, scale, cost optimization
- Freedom to make architectural decisions (e.g., Snowflake → open source)
- Hands-on expectations even at senior staff level
- Need to deliver visible impact in 1-2 quarters

**Team Dynamics:**
- Distributed team (North America + Armenia)
- Some evening meetings required for Armenia collaboration
- Growing rapidly (15 → 26 engineers)
- Working to become "well-oiled machine"

**Career Trajectory:**
- Pre-IPO company with growth potential
- Strong technical leadership to learn from
- High-impact role with visibility
- Opportunity to shape architecture

---

## 2025-10-21 Mehmet Murat Ezbiderli (principle engineer)
- Joined 3 years ago.
- Multi-tenant data platform, similar to Salesforce
- Why do you hire senior staff? What will be the first
	- We are a heavy snowflake customer. We are trying to use them less.
	- Ingestion delay is 4 minutes P90. 2 minutes at P50. This is not enough for some users.
	- For new projects, Move Spark, Flink out of Snowflink is on the roadmap. This will improve the delay.
	- It is hands-on for Senior Staff.
## 2025-11-04 Robbie Recruiter Call

-  What are you timeline? When you will be starting. 
- **Good News: I am getting an offer**, initially reporting to Sumanth
- 2807 257th Pl SE, Sammamish 98075.