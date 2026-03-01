# **RCA: Spark Jobs fails after migrating from EMR to EKS**

Status: *Under review*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Jul 25, 2025  Last Updated: Jul 30, 2025

# Problem

* A large portion of the Spark jobs running in the Percolator cluster on EMR are failing after migrating to EKS with the same memory configuration. Our default memory overhead is 10% of the heap memory.  
* For this large portion of the failing jobs with the same 10% memory overhead, individual tuning is required. We observed that some jobs require a significant increase, up to 100% or even 120% memory overhead compared to 10% on YARN. 

# Risks of OOM with the assumption that we can maintain the same memory configuration during migration

1. The container OS has memory overhead, small but not zero.  
2. Another container OS process (e.g. chef, rpm) can create large memory spikes, which is hidden from pod metrics. It's unpredictable and can be large. This would block the proposal of running a cron job inside the container to update os  
3. Ubuntu image has different configuration with optimized EMR AMI running Amazon Linux 2\. The default for max arena chunk is higher on Ubuntu, which creates significant memory fragmentation. Unused memory in the fragmentation will not show up in Spark UI but will be counted and enforced by cgroups. Looks like the memory fragmentation factor is based on the number of cores on the physical machine (instead of pods on k8s), so the number of fragmentations would be a magnitude higher on k8s. When the fragmentation is big, Spark UI can only see the actual consumed memory, but the unused memory in each arena chunk still consumes physical memory, which can cause OOM.   
4. We are using Parallel GC for the jobs on YARN. The default GC for Kubernetes is G1GC. G1GC is known to have a much higher GC overhead, and can increase overhead by 10%. This is significant considering our global default for Spark jobs is 10% overhead. This change alone could OOMKill a good number of jobs.   
5. Cgroup and YARN do memory accounting differently: cgroups account a lot more memory. For example, Iceberg is known to use memory-mapped files, which consumes OS page cache memory. This memory is not accounted for and not enforced by YARN (but still consumed on the host machine with less fragmentation). This memory will be accounted for by cgroups, and can result in OOMKill if it spikes. This applies to all virtual memory (including memory-mapped files) usage. On YARN, the current ratio is set to 100\. On Kubernetes, there is no such equivalent configuration.  
6. PySpark jobs (SqlPen, Merlin): PySpark memory is more complicated, it involves additional Python interpreter memory, Apache Arrow native memory, JNI integration, Vectorized UDFs. There is a significant risk when migrating to Kubernetes. For example, the Arrow C++ library/JNI consumes some memory that are not accounted for and enforced by YARN, but are accounted for and enforced by cgroups. IPC (data transfer from Python process to JVM process via Arrow) may require additional shared memory segments and socket buffers, which may depend on container OS??  
7. \[PENDING FURTHER INVESTIGATION\] Spark jobs on Kubernetes appear to behave differently: the same job has more skipped stages. It is possible that with the existence of HDFS (or other reasons like external shuffle service), Spark can detect states (e.g. cached dataframe) and can skip more stages more proactively than on k8s.  
8. \[PENDING FURTHER INVESTIGATION\] Tasks are all in the “Scheduler Delay” stage before OOMKilled. It can be as long as 3 minutes. This is consistent with every failed run on Kubernetes, but never happened on Kubernetes. There is no current explanation at the moment. It is possible that the “Scheduler Delay” happens when the executors are still finishing, shuffle data being fetched/cached, GC pressure, Iceberg metadata operations. 

