#grafana

- What's the relationship between Grafana and Prometheus?
	- Looks like Grafana is the dashboard, the UI, the front end, while Prometheus is the backend, the data store. Looks like Prometheus also provide its own dashboard and front-end. In Grafana's [tutorial](https://grafana.com/tutorials/grafana-fundamentals/), it uses prometheus as the data source for Grafana.
- How to integrate Grafana with Spark on a happy path?
	- According to [grafana.com](https://grafana.com/docs/grafana-cloud/data-configuration/integrations/integration-reference/integration-apache-spark/), looks like the recommended way is to integrate with Spark 3 because it comes with a built-in Prometheus plugin.
- How do we integrate with Spark 2? 
	- [Spark, grafana, influxdb](https://medium.com/@xaviergeerinck/building-a-real-time-streaming-dashboard-with-spark-grafana-chronograf-and-influxdb-e262b68087de).
- How does Grafana work in general?
	- Data Sources: storage backends that you can query in Grafana. You can query multiple data sources in one dashboard. AWS Hosted Grafana supportes the following built-in data sources that may be relavent: Graphite, InfluxDB, JSON, 
	- 
- How to send data to hosted grafana?
- How does it work with Stripe? Since grafana licence per user, do I need to get approval? What kind of approval I need?