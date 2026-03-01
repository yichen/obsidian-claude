[CacheLib](https://engineering.fb.com/2021/09/02/open-source/cachelib/)

* What's new?
	* Use a hybrid model (both DRAM and NVM drives) for caching instead of just DRAM, which is too expensive.
* What's the challenge?
	* With hybrid model, need innovative caching designs, by identifying the relevant content to cache for the right duration.
* What's the result?
	* A Pluggable, in-process caching engine.
	* A benchmarking tool to evaluate caching performance on production workloads
* Impact
	* Used as an in-process cache in more than 70 large-scale systems at Facebook.
	* Twitter, Pinterest, CMU, Princeton, Yale
* Overview
	* cache for small/large items in flash is called BigHash/BlockCache. The combination of BigHash and BlockCache is called Navy (non-volatile memory cache)
	* The coordination layer between DRAM cache and Navy is NvmCache.
	* DRAM cache, using slab memory. Each class has the same size.


[ZippyDB](https://engineering.fb.com/2021/08/06/core-data/zippydb/)

* What's new?
	* largest strongly consistent, geographically distributed key-value store at Facebook.
* What's the challenge?
	* Duplicated effort across teams to use RocksDB directly to manage their data, especially similar challenges in consistency, fault tolerence, failure recovery, replication and capacity management.
* Design Decisions
	* Reuse as much of the existing infrastructure as possible. This focuses the effort on data replication (Data Shuttle), laying it with RocksDB with a preexisting shard management (Shard Manager) and distributed configuration service (built on Zookeeper), together solves load balancing, shard placement, failure detection, and service discovery.
* What skills I should learn from this
	* 
* Use Cases
	* metadata for a distributed filesystem
	* counting events for both internal and external purposes
	* data features for product data.
* Overview
	* ZippyDB uses RocksDB as the underlying storage engine.