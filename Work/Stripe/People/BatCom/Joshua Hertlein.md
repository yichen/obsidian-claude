[2022-08: BDI User Support Funnel Design](https://docs.google.com/document/d/18r6AGIs6KbKmcmQaIKHGfiIj3tczLkT1fWoEs1p5srk/edit)
	- The pain
		- there is no intentional path, direction or curation for the experience, users require context to even begin to navigate available support options.
		- we rely heavily on runners to map user queries to relevant documentation, which is both a slow RTT for the asker, and takes up runner/infra time and doesnt scale. 
	- Solution
		- build a "user support funnel", essentially creaet a process on how to support customers, not haphazardly.


[2022-07 Spark 3 Initial Support](https://groups.google.com/a/stripe.com/g/foundation-shipped/c/MhVQa285UkY/m/jNIGWCTFAQAJ)
- Jonathan Bender driving this effort, Joshua is one of the contributor.
- Challenges
	- Stripe's customization of Spark requires a significant amount of time to port to Spark 3. In particular, Stripe's schema/encoder extensions and custom integration with Iceberg.


[Spark fast fail connection patch for unresponsive hosts](https://groups.google.com/a/stripe.com/g/foundation-shipped/c/ksD418Kl51s/m/EFiWhESGBQAJ)
- pull a spark patch.
- Tested in SparkCanary, now it takes 6 minutes to fail instead of 20 minutes.

[Stripe Next Backtesting with Spark](https://groups.google.com/a/stripe.com/g/foundation-shipped/c/pl0CWifkcDo/m/eYsGAF9aBAAJ)
- Problem: Sonic needed Spark on Java 11 for backtesting. Stripe runs Spark 2.4.4 on Java 8.
- Solution: get Spark 2.x running on Java 11


[Patch Linux Container Executor to reduce GC bottleneck](https://groups.google.com/a/stripe.com/g/foundation-shipped/c/Bqu9kYOklcI/m/nA63aszlAwAJ)

Databricks Notebooks Alpha



