https://admin.corp.stripe.com/team-run/boards/RUN_BATCOM/preview/RUN_BATCOM-7391

- Job failed on Dec 30. Seems to be executor OOM during a shuffle.
- Cant tell which shuffle is causing it.
- Join 4 datasets together, and these joins are duplicated. 
- List of jobs: https://hubble.corp.stripe.com/queries/fgu/2c8bf5bf
- Judging from Dec 30 failed run: https://hubble.corp.stripe.com/viz/dashboards/28636--spark-jvm-profiler?appid=application_1672261870690_25494&tab=App+Profiler&subTab=Executors
	- nothing wrong with driver.
	- Noticing long executor GC period that triggered executor lost.
- Question: so what we are looking at, is that the job will pass by giving more heap memory, but will fail by keeping existing memory config?