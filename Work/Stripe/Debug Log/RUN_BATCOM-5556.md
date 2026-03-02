https://jira.corp.stripe.com/browse/RUN_BATCOM-5556


Found runbook [here](https://confluence.corp.stripe.com/display/BATCOM/Decommissioning+or+Replacing+Hadoop+Datanodes)

```
030465607062 us-west-2 hadoopdatanodeicp--0c49d97bc857a5b73.northwest.stripe.io (instance_id=i-0c49d97bc857a5b73 host_set=concord contact=batch-compute) instance-stop The instance is running on degraded hardware 2022-09-12T16:00:00Z. If this host has automatic lifespan management enabled, then it will be automatically replaced if AWS takes it out of service and you can opt-out of these events by adding `ignore_ec2_maintenance_events: true` to puppet-config/config/<domain>/hosts/hadoopdatanodeicp.yaml.
```


pt
`sc-asg replace hadoopdatanodeicp--0c49d97bc857a5b73.northwest.stripe.io`

Output:
```
sc-asg replace hadoopdatanodeicp--0c49d97bc857a5b73.northwest.stripe.io
I, [2022-08-29T16:02:25.123499Z #98831]  INFO -- SpaceCommander: Going to run this command on Space Station 🚀
I, [2022-08-29T16:02:25.123641Z #98831]  INFO -- SpaceCommander: Please reach out in #space-station if the ride gets bumpy
I, [2022-08-29T16:02:26.377139Z #98831]  INFO -- SpaceCommander: Using puppet-config branch master-passing-tests@942245b by folbricht 14 minutes ago (Use 6th gen AMD instances for DI service hosts (#85596)) from GitHub
I, [2022-08-29T16:02:26.377423Z #98831]  INFO -- SpaceCommander: If you'd like to use your local HEAD (yichen/clean-up-cron-jobs@7c1b49c) instead, use the --branch flag.
I, [2022-08-29T16:02:26.867725Z #98831]  INFO -- SpaceCommander: This request's output is available at http://go/space-station-output/51526afe-2c32-49ad-a448-2e815403761e
I, [2022-08-29T16:02:26.868033Z #98831]  INFO -- SpaceCommander: You can view the logs for this request at http://go/space-station-logs/51526afe-2c32-49ad-a448-2e815403761e
Preparing execution environment; this could take a few seconds, thank you for your patience 🙏
Building Docker image...
Finished preparing execution environment, will run your command now
Replacements made in 0 asg(s)
```

Looks like I just wait?