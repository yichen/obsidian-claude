JIRA: https://jira.corp.stripe.com/browse/RUN_BATCOM-5477?filter=-1

Following the runbook, found this message in sentry:
```
Failure of minreplication_monitor for batch-compute
Run of '/usr/stripe/bin/minreplication_monitor --datanode-type hadoop-blueberry'

Output:
Starting run of /usr/stripe/bin/minreplication_monitor --datanode-type hadoop-blueberry
Traceback (most recent call last):
File "/usr/stripe/bin/minreplication_monitor", line 67, in <module>
check_minreplication_errors(tags)
File "/usr/stripe/bin/minreplication_monitor", line 56, in check_minreplication_errors
f = seek(path, datetime.now() - timedelta(minutes=5))
File "/usr/stripe/bin/minreplication_monitor", line 45, in seek
if t < target:
UnboundLocalError: local variable 't' referenced before assignment
```

Note that to search splunk for a cron job logs, specify sourcetype=minreplication_monitor.

Q: Looks like there is a code error? where to look for this file `minreplication_monitor`?
A: I did `find . -name` search on `~/stripe` folder, and found this: `./puppet-config/modules/hadoop/files/minreplication_monitor`

This is a regression from commit 7769a70a51f4a22de609ea77f412082394365d0b

Source code for the cron job:
https://git.corp.stripe.com/stripe-internal/puppet-config/blob/0db4fa6b/modules/hadoop/files/minreplication_monitor#L59






