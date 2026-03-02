https://jira.corp.stripe.com/browse/RUN_BATCOM-5482

This is an hourly cron job: nn_clean_corrupt_blocks

I don't understand why the error, the output looks correct to me:
```
[2022-08-28 23:00:02.414432] Starting run of hdfs fsck / -delete [2022-08-29 00:00:02.157373] Starting run of hdfs fsck / -delete [2022-08-29 01:00:01.489131] Starting run of hdfs fsck / -delete [2022-08-29 02:00:02.068125] Starting run of hdfs fsck / -delete [2022-08-29 03:00:01.755720] Starting run of hdfs fsck / -delete [2022-08-29 04:00:01.715638] Starting run of hdfs fsck / -delete [2022-08-29 05:00:02.226881] Starting run of hdfs fsck / -delete
```

- So why the monitor/sentry will fail? What are the conditions and what are the assumptions?
	- This is from a detector `important_cron_job_failing.tf`
	- This detector will fire when `cron_status > 0`
	- According to runbook, I should consult the log file `/pay/log/nn_clean_corrupt_blocks.log`
	- Looks like to search splunk, I can specify `source=/pay/log/nn_clean_corrupt_blocks.log`, or `sourcetype=nn_clean_corrupt_blocks`
