---
name: Documentation Writer
description: A guide for drafting and reviewing technical documentation with a focus on narrative impact, quantitative evidence, and clear structure.
---

# Documentation Writer Skill

This skill defines the preferred style for technical analysis and proposal documents. Use this when drafting new documents or reviewing existing ones.

## 1. The "Narrative" Executive Summary (TL;DR)

Do not just list bullet points. Tell a cohesive data-driven story.

*   **The Hook (The "What"):** Start with the single most shocking or impactful metric.
    *   *Bad:* "We analyzed the market."
    *   *Good:* "We identified that **58% of developers** still use manual workflows for a task that takes 3 hours per week."
*   **The Validation (The "How Bad"):** Immediately back the hook with specific data.
    *   *Example:* "Across 500 survey responses, the average time spent is **3.2 hours/week**, with power users reporting **6+ hours**."
*   **The Mechanism (The "Why"):** Briefly explain the cause in simple terms.
    *   *Example:* "Current tools require 4 separate steps across 3 platforms, with no automation between them."
*   **The Solution & Impact (The "So What"):** State the fix and the result.
    *   *Example:* "A unified tool reduces this to 1 step, saving **2.5 hours/week** per developer."

## 2. Structural Elements

*   **Descriptive Headers:** Use headers that convey the *insight*, not just the topic.
    *   *Bad:* "Market Size"
    *   *Good:* "A $4.2B Market Growing 23% YoY with No Clear Leader"
*   **The "Thought Experiment":** When explaining complex dynamics, use a simplified "Mental Model" or "Thought Experiment" section to make the logic intuitive.

## 3. Evidence Presentation

*   **The "Denominator":** Always contextualize costs. Don't just say "$100". Say "$100 (3% of total bill)".
*   **Differentiation:** Clearly distinguish between verified data and estimates.
*   **Handling Debunked/Inapplicable Claims:** During iteration, preserve context; for final version, clean up.

    | Document State | How to Handle Inapplicable Claims |
    |----------------|-----------------------------------|
    | **Work-in-progress** | Move to Appendix `[N] Considered But Inapplicable` |
    | **Final/Presentation** | Remove unless it's a common misconception worth addressing |

## 4. Proposal Format

*   **Conceptual Design:** Provide high-level logic for the proposed solution.
*   **Risk/Trade-offs:** Be honest about risks.
*   **Implementation Steps:** Clear, actionable next steps.

## 5. Appendix Standards (Mandatory)

*   **Always Included:** Every significant analysis or proposal document MUST include an Appendix section at the end.
*   **Numerical Ordering:** Items must be strictly ordered numerically (e.g., `[1]`, `[2]`, `[3]`).
*   **Full Citation:** **Every** item in the Appendix MUST be referenced in the main body of the document at the relevant location. Use the `[N]` format for links.
*   **Content:** The main body should tell the story; the Appendix should hold the "Receipts" (raw data, detailed source lists, methodology notes).

### Special Appendix: "Considered But Inapplicable" (Work-in-Progress Only)

During iterative analysis, use a special Appendix section to preserve context about claims that were considered but found inapplicable:

```markdown
### [N] Considered But Inapplicable

The following claims were evaluated during analysis but found to be inapplicable. They are preserved here to prevent re-investigation.

| Claim | Why Inapplicable | Date |
|-------|------------------|------|
| "Market is $10B" | Includes unrelated segments | 2026-03-15 |

**Note:** Remove this section before final presentation.
```

**Rules for this section:**
- Does NOT require citation in main body (exception to the normal rule)
- Should be the LAST numbered Appendix item
- Must be removed before document is finalized for stakeholder presentation

## 6. Review Checklist

When reviewing a document, ask:
1.  Does the first sentence grab attention with a number?
2.  Is the "Why" explained simply enough for a non-expert to grasp?
3.  Is the heavy data moved to the Appendix?
4.  Is every Appendix item referenced in the text?
5.  Does the Summary tell a complete story (Problem -> Cause -> Solution -> Impact)?
