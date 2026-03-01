[Towards data quality management at LinkedIn 2022](https://engineering.linkedin.com/blog/2022/towards-data-quality-management-at-linkedin)

- What are the main categories of data quality issues and how to collect data?
	- Metadata category of data quality issues.
		- concerns data availability, freshness, schema changes, and completeness
		- This can be collected from the metadata repository (e.g. Hive metastore and related event) or storage services (e.g. HDFS). 
	- Semantic category of data quality issues
		- Concerns the content of the datasets, column value nullability, duplication, distribution, exceptional values, tc.
		- Can be collected from the data profile (if it exists) or by scanning the dataset itself. 
- What are the main challenges?
	- A monitoring solution must address the scalability issue and offer low overhead, short latency, and monitoring-by-default (i.e. no manual onboarding process) capability.
	- If producers miss the SLA commitment, the misses may not impact all of the consumers and the real impact depends on the consumption usage. Avoid alert fatigue.
	- When a pipeline consues any of the data sets with different arrival frequences (monthly, weekly, daily, hourly etc), defining the freshness staleness of the dataset can be a challenge.
	- Engineers receiving too many alert emails, resulting in alert fatigue. Different expectations on dataset availability also magnifies the fatigue issue. This leads to the mishandling or overlooking of any real data quality issues.


[2022: LinkedIn's journey to Java 11](https://engineering.linkedin.com/blog/2022/linkedin-s-journey-to-java-11)

* Context
	* Running over 1000 Java applications on 320,000+ hosts. 
	* Based on the performance improvements of G1GC and other benefits, LinkedIn made the decision to migrate from Java 8 to Java 11. Java 8 was the last LTS version before Java 11 was released in 2018.
	* At LinkedIn, applications use one of four main types of frameworks: Jetty, Play, Samza, or Hadoop. Only Jetty was at a version (within LinkedIn) that was compactible with Java 11.
* Prepare
	* Build framework. The first step is to have our code built with Java 11. This means that over 2000 repos needed to have their builds changed to Java 11. We need to upgrade to Gradle 5 or above to be compacti le with the Java 11. Aftre that, our team quickly transitioned to early adopter testing.
	* We picked 20 applications as early adopters and tested them with Java 11. Our selection criteria prioritized the applications with larger heap sizes, higher host counts, and higher QPS. Overall, the results were positive with no applications seeing performance degradation after upgrading to Java 11. The best cases showed performance gains of up to 200%.
* Automation
	* After some minor changes to our infrastructure, it was possible to change repository build systems to use Java 11. We then were able to trigger mass Java 11 builds in a test environment to find out what issues needed to be addressed. This testing allowed us to identify a plethora of edge cases as well as several major challenges. Eg: code could be compiled on Java 8 but failed to run properly on Java 11. We decided to use the "--release 8" flag in order to make the Java 11 compiler compile down to Java 8 level bytecode. The upside is that we were able to maintain compactibility between Java 8 and 11 much easier, a tradeoff that the team unanimously agreed on.
* Migration
	* The actual migration was planned for an additional three quarters in which 500 libraries and about 1100 applications would be migrated, led by a team of two engineers and one TPM.




