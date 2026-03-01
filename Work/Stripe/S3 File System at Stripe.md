
What are the different build targets involves S3 and Hadoop in zoolander?
- //uppsala/src/main/java/com/stripe/hadoop/fs/s3:s3
- //uppsala/src/main/java/com/stripe/hadoop/fs/s3:file_system
- //src/scala/com/stripe/data_common/hadoop/fs/s3:s3
- //src/scala/com/stripe/data_common/hadoop/fs/s3:file_system
There is also a legacy S3 library:
- //src/scala/com/stripe/data_common/s3
- //src/scala/com/stripe/data_common/redirecting_output_committer



Under uppsla path, we have two bazel java_library build targets: (1) s3, and (2) file_system. In Bazel, they will be referenced as `zoolander/uppsala/src/main/java/com/stripe/hadoop/fs/s3:s3` and `zoolander/uppsala/src/main/java/com/stripe/hadoop/fs/s3:file_system` respectively.

The "s3" build target (a java_library) contains some classes for S3 metadata and a DirectSequenceOutputCommitter.java. This build target will export public access point `@com_stripe_zoolander//src/scala/com/stripe/data_common/hadoop/fs/s3`, and this target is accessible to public. That is, any other build target can see and depend on this target. This build target was used by both Spark and Scaling jobs. In Spark, we specify the commiter in the configs.

The `file_system` java_library taret is only visible for zoolander data_common targets, including the "s3" build target above. That means the file_system is a lower-level target to s3 target.

The `file_system` library contains the Stripe's S3CFileSystem and its consistency validator.  The `s3` library contains the `DirectSequenceOutputCommitter` which directly copy data to S3 and avoid the HDFS's OutputCommiter's write-and-rename behavior. How do we achieve that? When each task is committed, the filename for this task was added to the job metadata in HDFS (the location is `/tmp/hadoop-metadata/{jobId}`. When the whole job is to be committed, the job metadata file (`_SUCCESS`) will be uploaded to S3.


---

Scala library `aws` depends on `//src/scala/com/stripe/data_common/hadoop/fs/s3:file_system`. It contains sub libraries `aws/spark:spark` and `aws/spark:spark3`.

What's inside this `//src/scala/com/stripe/data_common/hadoop/fs/s3:file_system`? 
- It extends and wrapps around the `ExposingS3AFileSystem` and name it `S3FileSystem`
- It depends on the `file_system` package defined in the uppsala path. This means it is at a higher-level than the uppsala package. 

---

What's up with `data_common/s3:DirectFileOutputCommitter`? The file looks similar to the DirectSequenceOutputCommitter, even more similar to the parquet/scalding's DirectSequenceOutputCommitter (of the same file name).  Sequins extends this committer. What is sequins? It is Stripe's in-house key-value database serving read-only batch-loaded data.




