See [BATCOM-1703](https://jira.corp.stripe.com/browse/BATCOM-1703)


- How should the data look like after ingesting into Hubble? Schema? Can hubble data contain array data type? That's because the GC columns should be an array. It should be a flat table with the following columns
	- nonHeapMemoryTotalUsed
	- heapMemoryTotalUsed
	- epochMillis
	- nonHeapMemoryCommitted
	- heapMemoryCommitted
	- processCpuLoad
	- systemCpuLoad
	- processCpuTime
	- appId
	- name
	- host
	- processUuid
	- tag
	- gc 
- How to use JVM Profiler?
	- Maybe I can experiment with a ConsoleOutputReporter first with USM?
- How to use USM? Do I have to write a new Spark job first, or can I use a production job and run it myself?
	- `bin/airflow-local run --date 2020-02-02 --usm --plugin pay/to/my/plugin.py`
	- `airflow-local` will not run on your laptop, you need to use pay ssh into your mydata box.
	- To run a single airflow task under USM: `bin/airflow-local run mytaskid --usm` The --date is default to yesterday.
	- This ["Developing in Zoolander" guide](https://confluence.corp.stripe.com/display/PRODINFRA/Developing+in+Zoolander) has a list of useful guides including how to use kafka.
	-  `bin/airflow-local run ddl.DenormQualityReview --usm`
- How to actually modify Spark command line?
	- [PR 156523](https://git.corp.stripe.com/stripe-internal/zoolander/pull/156523/files): 
	- 
	- 