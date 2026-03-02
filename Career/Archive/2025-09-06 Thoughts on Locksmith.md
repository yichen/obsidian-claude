# **Thoughts on Locksmith**

Status: *In progress*  Author: [Yi Chen](mailto:yichen@stripe.com)    Created: Sep 6, 2025  Last Updated: Sep 6, 2025

# Context

I reviewed the [Data Warehouse Catalog Assessment](https://docs.google.com/document/u/0/d/1PXP1S5lsLgufMgtj7Kj89jeKyIXII2uXWm01dyDiwZg/edit) and [Project Locksmith](https://docs.google.com/document/u/0/d/1XNXz0hTVoH31FqY1p_3WpyLWULlkCyyNx0ro9HSJW2E/edit). While I left a few inline comments, I found many of the issues too broad and interconnected to be addressed effectively in that format. My concern is that a large number of inline comments risks fragmenting the discussion (drive-by-shooting feedback) and obscuring the central themes.

The purpose of this document is to provide a consolidated view of my observations and feedback. My main concern centers on the alignment between the proposed design and the current realities of the Data Infrastructure team. Specifically, we are structured today with a stronger focus on DevOps operations than on distributed systems development. This gap creates risk when building a key infrastructure component that sits on the critical path for all Spark jobs.

By organizing my thoughts here, I hope to make the risks and trade-offs clearer and help the team converge on a design that is both technically sound and realistically executable.

# Main Concerns

The scope of Project Locksmith is very big. It tries to solve many problems in one large project, with one unified solution. There are no clear trade-offs and priorities among these requirements. As a result, we rejected all 3rd party solutions and opt to roll our own. I feel rolling-our-own is the only way when we won’t take trade-offs. 

There are significant discrepancies between the motivation of this project, with the proposed solution. The proposal doesn’t seem to address these contexts, even though some 3rd party solutions were rejected with the same context. See Appendix [\[1\]](#bookmark=id.rpmduavqmby1).

It appears that some of the assumptions require deep dive. The lack of Hive support is a reason to reject a few 3rd party solutions. Vendor lock-in is also a concern that leads to rejection of 3rd party solutions. The final proposal requires us to implement Iceberg REST API, develop our own authentication layer below it, and implement Hive wrappers for back compatibility. I feel this is not the appropriate direction. Iceberg was invented to solve a few critical issues with Hive, and it is a replacement for Hive in general. In my view, the lack of Hive support for many 3rd party solutions is a feature, not a bug. We propose to develop our own solution to work with Hive, is a throw-away work that may mean wasted engineering effort. Slack also have an ongoing Hive to Iceberg migration, with a mandate to finish this in about a year. We should factor in this in the assumption of this large-scope project. The key question is: do we really need to care about Hive tables at all. See Appendix [\[3\]](#bookmark=id.llpgk992n94k) for more context.

One of the main innovations in Project Locksmith, is the federated permission. This may be one of the main reasons why we are not using existing 3rd party OSS tools, as none of them have such ability. I think we need to deep dive this from the following three perspectives:

* Even though there are no OSS solutions for federated permission, Databricks-Managed Unity Catalog actually have this ability, allowing external organizations to have “read” access to the catalog, and the catalog can be a federated HMS. I am curious if there is a solution to use Databricks-Managed Unity Catalog just for this feature, without migrating our HMS over.  
* Can this be solved by building on top of S3 Access Grants?  
* Is this problem worth solving given the complexity and high risk nature of the proposed solution? 

Vendor lock-in is a real risk. However, the Project Locksmiths proposal requires us to implement Iceberg REST API, and the authentication/authorization layer along with it. 

# Thought Experiment

Instead of attempting to solve a large scope of problems with a unified approach, I’d like to present a thought experiment, to build the solution bottom-up instead of top-down. Instead of implementing the Iceberg REST API that is on the critical path, I propose a potential solution that augments existing infrastructure.

The core idea of this thought experiment is that we will only focus on the core problem. Data retention, zero-copy data sharing, etc, are all problems that can be solved outside of the core infrastructure, so as part of this thought experiment, they are all out of scope. I will remove the Hive support since there is already a mandate to migrate our Hive tables to Iceberg, which is the industry standard practice, and any work for Hive tables is wasteful work. Without all of the scope that are not vital, the core problem is very simple and solvable with low risk.

The core problem, is solve the S3 permission management pain. We will start the thought process from solving this problem first, and then to see if we can augment the solution to solver more related problems. On the high level, it seems this is possible. The core solution is S3 Access Grants.

* With S3 Access Grants, we can manage our S3 datasets, without having to manage the IAM role for each datasets.   
* S3 Access Grants has robust Okta integration. We may need to augment with TSAuth. We 

# Appendix

## \[1\] Discrepancies between the motivation and the solution

In the [Context](https://docs.google.com/document/d/1PXP1S5lsLgufMgtj7Kj89jeKyIXII2uXWm01dyDiwZg/edit?tab=t.0#bookmark=id.qw8a8t4z1fe6) section of [Data Warehouse Catalog Assessment](https://docs.google.com/document/u/0/d/1PXP1S5lsLgufMgtj7Kj89jeKyIXII2uXWm01dyDiwZg/edit), it listed 4 additional goals that we want to tackle besides our core concern of S3 permission management for our data warehouse. It is not clear how the Locksmith proposal is addressing these goals. For example:

* Regarding “**AI capabilities**”, I don’t see relevant proposals related to AI in Locksmith. Other alternatives like Unity Catalog, which was rejected in our design, appears to have this feature. The open-source version supports AI Assets (e.g. models), which the Locksmith lacks. It also supports AI powered documentation, which is only available in Databricks-managed versions. If our goal includes AI capabilities, we should come up with the trade-off between implementing and maintaining our own code-base, with adopting managed Unity Catalog.  
* Regarding “**Simplify architecture**”, we want to simplify the current “HMS+Ranger+S3 IAM” with a single catalog, but I feel we are adding many more moving parts and new surface areas, including wrappers, plugins, new RBAC system, credential vending, federated permissions. We need more clarity on how Locksmiths achieves the goal of simplifying architecture, and how we justify the trade-offs.  
* Regarding “**Interoperability and data sharing**”: The “federated permissions” is a key differentiator for Locksmith. . it seems Unity Catalog can provide credential vending for external system access (see [doc](https://learn.microsoft.com/en-us/azure/databricks/external-access/credential-vending)). The [open-source Unity Catalog](https://www.databricks.com/blog/open-sourcing-unity-catalog?utm_source=chatgpt.com) announcement appears to declare that databricks-managed unity catalog allows “enabling external clients to read from all tables (including managed and external tables), volumes, and functions in hosted Unity Catalog from Day 1, with your existing access controls in place. This change simply means a larger ecosystem of clients will work with your existing catalog”[\[2\]](#bookmark=id.p1qnz2rvet7o). Do we have a trade-off analysis to use Unity Catalog or implement our own federated permission?

## 

## \[1\] Unity Catalog’s AI Capabilities

**AI Asset Management**: the OSS Unity Catalog supports managing AI assets, including AI models (besides Iceberg tables). See [https://github.com/unitycatalog/unitycatalog](https://github.com/unitycatalog/unitycatalog)

**AI-Powered Documentation**: The Databrick’s Unity Catalog leverages generative AI to simplify the documentation, curation, and discovery of the organization’s data and AI assets by automating the addition of description and comments for tables and columns. See [Public Preview of AI Generated Documentation In Databricks Unity Catalog announcement](https://www.databricks.com/blog/announcing-public-preview-ai-generated-documentation-databricks-unity-catalog).This feature is only available in the Databricks-managed Unity Catalog and its not available in the open source version. We need a trade-off analysis between the vendor lock-in of using managed Unity Catalog, with implementing and maintaining this ourselves. 

## \[2\] Unity Catalog’s support for external access

The [open-source Unity Catalog](https://www.databricks.com/blog/open-sourcing-unity-catalog?utm_source=chatgpt.com) appears to imply that the open-source version provides [credential vending for external system access](https://learn.microsoft.com/en-us/azure/databricks/external-access/credential-vending), while the databricks-managed version provides this from day 1\.

## \[3\] Trade-off for Hive table support

Unity Catalog was rejected because of its lack of Hive table format support. However, the Locksmith proposal calls for implementing our own Hive table format support, besides implementing the Iceberg REST API.

It is not clear if this is the right trade-off. Another option is to adopt open-source Unity Catalog but implement the Hive table format support on top of it, instead of implementing both Hive table support with Iceberg REST API.

Another consideration is that we rejected the Databricks managed Unity Catalog because it is only available for Databricks customers, which is non-negotiable. Databricks-managed Unity Catalog not only provides support for [external access](https://www.databricks.com/blog/secure-external-access-unity-catalog-assets-open-apis), which solves our needs for sharing data with Salesforce, it also supports Hive table format.

We should be wary of implementing our own Hive table support with Locksmith, especially since Slack's current Hive support strategy and roadmap are unknown. This approach carries a higher risk than migrating to Iceberg, which aligns with industry standards. Rejecting third-party open-source solutions and developing our own Hive support—a path many open-source tools have abandoned—is a significant concern.

## \[4\] Zero-Copy Data Sharing & Federated Permission

It appears that Databricks Managed Unity Catalog does support [HMS Federation](https://docs.azure.cn/en-us/databricks/data-governance/unity-catalog/hms-federation/). That is, it creates “foreign catalogs that mirror our Hive metastore” and “run in Hive metastore compatibility mode.”

This seems to mean that we can keep our existing Hive tables unchanged, the Unity Catalog provides governance lawyer on top of our existing HMS. Our EMR jobs can be accessed via the federated catalog. “[Foreign catalogs for external metastores do not support writes](https://docs.azure.cn/en-us/databricks/data-governance/unity-catalog/hms-federation/)”, but most of our Salesforce are mostly reading and not writing. 

## \[5\] Vendor Lock-in vs. First-Party Implementation

The proposal replaces vendor lock-in with a first-party implementation of the Iceberg REST API. This introduces a large surface area, and there are only a very small number of OSS implementations in the market today. We rejected OSS Unity Catalog in our proposal because it is still in an early stage with little traction. I am concerned that building our own implementation would carry even greater risk. Beyond the technical capabilities of our team compared to Databricks engineers, we may end up “vendor-locked” to our own engineer who originally built the system.

For example, if Iceberg REST API v2 were released, would we be unable to adopt newer versions of Spark and Trino that depend on it until we reimplemented the newer version ourselves? We already face similar struggles: emrAdm is tied to EMR Go API v1, and upgrading to v2 has proven a significant engineering effort that is now effectively impossible. I worry we may recreate this situation with the Iceberg REST API—locking ourselves into a high-touch, hard-to-upgrade implementation that prevents us from moving forward with newer Spark and Trino versions.

In my opinion, Vendor Lock-in is a much easier problem to workaround than the entire codebase becoming a technical debt. 