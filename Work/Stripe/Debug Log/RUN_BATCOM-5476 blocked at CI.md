RUN_BATCOM-5476: Reassign cron job ownership due to oncall split

PR: https://git.corp.stripe.com/stripe-internal/puppet-config/pull/85700

Looks like I need some ldap permission to be able to run puppet tests against flink machines:
https://amp.qa.corp.stripe.com/command/papertrail_plL77MQlhs12Hwglc9fKYwm7POmx8sl0laMQEFCC6vA

```
sc-puppet --domain stripe.io --env qa --type airflow,airflowbackfill,airflowds,airflowicp,airflowretention,airflowweb,dsrvprestocoord,flinktaskmanager,hadoopzk,kafkaoplogsplitter,mydata,myflytebox,zoolandercanary
```