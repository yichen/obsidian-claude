* Get advice early
    * Before writing any code.
    * Before writing any lengthy design documents
    * Instead
        * Jot down some rough ideas (a few paragraphs)
        * Go find some people and chat at a whiteboard.
        * Even better: discuss a few different potential designs and evaluate.
* Interfaces
    * Think carefully about interfaces
    * Imagine other hypothetical clients trying to use your interface
    * Document precisely, but avoid constraining implementation.
        * Very important to be able to reimplement
    * Get feedback on your interfaces before implementing!
    * Best way to learn is to look at well-designed interfaces
* Protocols
    * Good protocol description language is vital
    * Desired attributes
        * Self-describing, multiple language support
        * Efficient to encode/decode, compact serialized form
        * Google solution: Protocol Buffers
    * Automatically generated language wrappers
    * Graceful client and server upgrades
        * Systems ignore tags they don’t understand, but pass the information through (no need to upgrade intermediate servers)
    * Serialization/deserialization
        * Lots of performance work here, benefits all users of protocol buffers
        * Format used to store data persistently (not just for RPCs)
    * Also allow service specifications
* Designing Efficient Systems
    * Important skill: given a basic problem definition, how do you choose the “best” solution?
    * Best could be simplest, highest performance, easiest to extend, etc.
    * Important skill: ability to estimate performance of a system design, without actually having to build it!
    * Numbers every one should know (about latency)
* Write Microbenchmars!
    * Great to understand performance
        * Builds intuition for back-of-the-envelope calculations
    * Reduces cycle time to test performance improvements
* Know your basic building blocks
    * Core language libraries, basic data structures, SSTables, PB, GFS, BigTable, indexing, MySQL, MR
* Building infrastructure
    * Identify common problems, and build software systems to address them in a general way
    * Important not to try to be all things to all people
    * Don’t build infrastructure just for its own sake
        * Identify common needs and address them
        * Don’t imagine unlikely potential needs that aren’t really there
        * Best approach: use your own infrastructure (especially at first), much more repaid feedback about what works, what doesn’t
* Design for growth
    * Try to anticipate how requirements will evolve
    * Ensure your design works if scale changes by 10X or 20X, but the right solution for X often not optimal for 100X
* Design for low latency
    * Aim for low average times (happy users!)
    * Worry about variance! Redundancy or timeouts can help bring in valency tail
    * Judicious use of caching can help
    * Use higher priorities for interactive requests
    * Parallelism helps!
* Consistency
    * Multiple data centers implies dealing with consistency issues
        * Disconnected/partitioned operation relatively common
        * Insisting on strong consistency likely undesirable 
        * Most products with mutable state gravitating towards “eventual consistency” model.
* Threads
    * If you are not using threads, you’re wasting ever larger fractions of typical machines
    * Think about how to parallelize your application
    * Threading your application can help both throughput and latency
* Understand your data access
* Encoding your data
    * CPUs are fast, memory/bandwidth are precious, ergo.
        * Variable-length encodings
        * Compression
        * Compact in-memory representations
    * Compression very important aspect of many systems
        * Inverted index posting list formats
        * Storage systems for persistent data
* Making applications robust against failures
    * Canary requests
    * Failover to other replicas/datacenters
    * Bad backend detection: stop using for live requests until behavior gets better
    * More aggressive load balancing when imbalance is more severe
    * Make your apps do something reasonable even if not all is right, better to give users limited functionality than an error page.
* Add sufficient monitoring/status/debugging hooks
    * Export HTML-based status pages for easy diagnosis
    * Export a collection of key-value pairs via a standard interface. Monitoring systems periodically collect this from running servers.
    * RPC subsystem collects sample of all requests
    * Support low-overhead online profiling
        * CPU profiling
        * Memory profiling
        * Lock contention profiling
    * If your system is slow or misbehaving, can you figure out why?