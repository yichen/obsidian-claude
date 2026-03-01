[LinkedIn: Migration madness: How to navigate the chaos of large cross-team initiatives towards a common goal](https://engineering.linkedin.com/blog/2022/migration-madness--how-to-navigate-the-chaos-of-large-cross-team)

Problem Scope
- Deprecate legancy deployment backend, impacted every third-party integration, across dozens of engineering teams. Migrating 600+ use cases required 100+ individual engineers. 

Challenges
- Large, cross-team projects can seem daunting. They require hours of work from dozens of different individuals, and there may be dependencies between different individuals’ work. Driving these projects is a huge feat of coordination, even when everything runs smoothly! Plus, it’s not unusual for unexpected issues to pop up along the way, requiring additional work or adjusted timelines. All of these factors often make large projects hectic, but planning, documentation, and communication can bring order to the chaos.

Strategies
- **Get clients aligned with the benefits of the new system**. We framed these benefits in terms of reducing/eliminating pain points that clients had previously experienced with our system.
- **Write clear step-by-step instructions**. We used these instructions to migrate a pilot use case ourselves, following only the exact written instructions without considering any of our prior knowledge. We asked the first few clients for feedback on how we could improve the instructions, and ended up adding even more details. Eventually our instructions were clear enough so that many engineers were able to complete the migration without any help from us at all. Enabling self-service pays off in the long run.
- **Provide automated tooling wherever possible.** There are often similar tasks that need to be done by many different people and/or tasks that are trivial but time-consuming. Finding all possible opportunities to leverage automation can save a huge amount of cumulative time.
- **Make it easy for clients to find help**. One support method was a Slack channel specifically dedicated to questions and issues that came up during the migration process. We also set up workstation days for 1:1 support, which is helpful for live debugging sessions.
- **Utilize decision frameworks**. By modeling our projet within the organization's decision frameworks during our planning phase, we were able to obtain commitment and buy-in from partner teams that increased confidence in our project's successful completion.
- **Track project progress**. Regular status meetings, clear categorization of issues, and utlization of workflows and dashboards on JIRA helped us monitoring, visualize, and quantify progress across the 600+ use cases.

