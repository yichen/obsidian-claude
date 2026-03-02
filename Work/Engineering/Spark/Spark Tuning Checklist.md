#sparktuning

Optimize and improve Spark performance

* Use SparkListener to detect if a node is slow (disk or network issue) and do task analysis. For example, use history configs to save system resources, and only fall back to the user's hard-coded configuration for executor sizing.
* With SQL Tab, look for WholeStageCodeGen box, and start the one with the longest duration for optimization effort.
* Partial aggregation can be bad for performance when the column cardinality is too high.
* Effective data layout with parquet, by sorting the records based on colume cardinality to take advantage of columnar compression. See [reference](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
* Use Kryo serialization. It has a lesser memory footprint than Java serilizer and it's faster. See [reference](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
* Use custom accumulators. [reference](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
* Restructuring payload to reduce ser/de time. [reference](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
* Parallelizing spark’s iterator. [reference](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
* Improve utilization by sharing some spark resources. For example, ingesting multiple Kafka topics together. See [reference](https://databricks.com/session_na20/how-to-performance-tune-apache-spark-applications-in-large-clusters)
* Tune shuffle partitions to reduce shuffle spill to disk.
* break long-running tasks into simple/short ones because more chances to find available slots and faster for recovery from failures.
* Be careful when casting a column: filter push down won't work with casted column.
* For heap size less than 32G, tune JVM to use four byte references instead of eight. See [reference](https://www.databricks.com/session_na20/fine-tuning-and-enhancing-performance-of-apache-spark-jobs)
* Change the query to reuse *analyzed query plan* so cached data can be used. See [reference](https://towardsdatascience.com/best-practices-for-caching-in-spark-sql-b22fb0f02d34)