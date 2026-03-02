# **Java & Python Upgrade Risk Assessment for EMR 7 Migration**

Status: *Under review*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Aug 21, 2025  Last Updated: Aug 21, 2025

| Aug 21, 2025 | Shared with the DI team and requested feedback. See [thread](https://slack-pde.slack.com/archives/CJFHE7AR3/p1755795754762829). |
| :---- | :---- |
|  |  |

# Goals

As part of the EMR 7 migration, we need to address a new risk: the JVM upgrade. Unlike EMR 6, which stayed on Java 8, EMR 7 upgrades the default runtime from Java 8 → Java 17 (a nine-version jump). This introduces potential compatibility and runtime issues that require a thorough impact assessment.

EMR 6 to 7 upgrade is also a bigger Python risk due to OS upgrade to Amazon Linux 2023, OpenSSL 3, and Spark 3.5. We also need to assess the risk in this scope due to overlapping engineering effort and  methodology.

# Potential Risks

## 1\. JAR Compatibility

* Can Java 8-compiled Spark jobs run on Java 17? Risk of UnsupportedClassVersionError.  
* All custom libraries and dependencies require Java 17 compatibility validation. Or, what do we need to do before migration?  
* Some modules were removed after Java 8 (e.g. javax.xml.bind removed in Java 11). Usage will trigger ClassNotFoundException unless explicitly added back. We seem to have that risk, see [here](https://hound.tinyspeck.com/?q=javax.xml.bind&i=nope&literal=nope&files=&excludeFiles=&repos=).  
* Jobs relying on JDK internals (reflective access, unsafe APIs, etc.) may break.Are those fixable by DI team, or do we need to document this in the runbook so the user can self-help.

## 2\. Build System Impact

* Build pipelines may need to update target versions from 8 → 17\.  
* JARs built with Java 17 cannot run on Java 8 runtimes. Do we need a parallel build strategy during migration?  
* Slack’s internal build system may need changes to support dual builds and align with EMR 7 migration timing. If so, how to change it?  
* Dependency ecosystem: third-party libraries and Scala version compatibility need verification.  
* What are all 3rd party jars (e.g. Iceberg) we are using? How are they built or linked? Will they all work on Java 17? If not, what needs to happen so we don't have to deal with each individual issue when migration happens?

## 3\. Runtime Environment

* Default GC changes: Java 8 (ParallelGC) → Java 17 (G1GC). G1GC typically has \~10% higher heap overhead, which may trigger OOMs for borderline jobs. Is this a concern? Do we have Spark jobs that customize its GC today? What's the risk of the jobs that are using the cluster default?  
* Some GC flags have been removed or changed from Java 8 to 17— any job or clusters are using depreciated flags?  
*   
* UDFs and shaded dependencies may have hidden incompatibilities.  
* Any impact on our own HDFS caching system that Gage developed? How to avoid the case we need to cache the same jar built for Java 8 and 17\.

4\. Python-specific risks

* Do our PySpark (e.g. Sqlpen) use UDF, third-party libraries/dependencies that need to be upgraded. What needs to be done for upgrading? For example, Pandas UDFs may require newer pands/pyarrow, schema/typoing and timezone handling can differ.   
* Research online, and assess known risks for Python and PySpark, that may related to OS upgrade (from Amazon Linux 2 to Amazon Linux 2023), with a new default Python version.  
* Can we run static checks for Python 3.9+ compactibility, to get a feel of the risk?  
* Amazon Linux 2023 base images and EMR 7 bootstrap can surface path and linker difference. Is this a risk for Slack?  
* Will the OpenSSL 3 upgrade cause issues? Search slack and google and see if service teams have seen common issues related to OpenSSL 3 upgrade.   
* Spark 3.5 updates Py4J/cloudpickle versions. Assess the risk and mitigation ideas.  
* EMR 7 ships newer Jupyter components. Kernes depend on system Python and OpenSSL. Is there a risk for us?

# Required Scoping Work

We should aim to answer:

* DI Internal:  
  * What build system changes are required?  
  * Do we adopt a parallel build (Java 8 \+ 17\) during transition?  
  * What changes are needed in the deployment pipeline to support this?  
  * What’s the estimated engineering effort for enabling the build system, CI/CD, and deployment system?  
  * Have we checked out Google, AWS/EMR forums and have a good understanding of common issues other EMR users have faced that may have an impact on our migration?  
* User-facing:   
  * What failures can users expect during mass migration?   
  * Is there a runbook document to help users to look up the errors and resolve them by themselves? Can the DI team automate some of these steps beforehand? 

# Exit Criteria

* By FY26Q3, our build and deployment pipelines support dual Java 8/17.  
* DI team scope preventive changes so migration does not require case-by-case debugging.  
* All assessment questions answered with documented evidence. For questions without answers, identify and list them as open questions.  
* Key risks documented with severity classification  
* Tasks related to Java upgrade scope (e.g. build system changes, timeline, effort) if the work is needed. Work that the DI team needs to do to prevent case-by-case hand-holding before migration is identified and scoped.  
* Discovered risks documented. Mitigation strategy defined.

