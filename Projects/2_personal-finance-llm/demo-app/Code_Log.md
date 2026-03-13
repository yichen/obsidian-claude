# Code Log: Finance Demo App — Verification & Test Infrastructure

Started: 2026-03-12
Last Updated: 2026-03-12
Status: READY_FOR_REVIEW
**Branch**: feature/finance-demo-app-tests

---

## Implementation Tracker

| ID | File/Component | Status | Entry | Notes |
|----|---------------|--------|-------|-------|
| 1 | electron/finance-core.ts | COMPLETED | #12 | generate_standard_chart execution fixed |
| 2 | electron/index.ts | COMPLETED | #2 | Thin Electron shell after extraction |
| 3 | vitest.config.ts | COMPLETED | #2 | NEW — test runner config |
| 4 | electron/__tests__/electron-mock.ts | COMPLETED | #3 | NEW — mock factories |
| 5 | electron/__tests__/finance-core.test.ts | COMPLETED | #5 | Updated for timing info |
| 6 | electron/__tests__/config.test.ts | COMPLETED | #5 | NEW — path validation tests |
| 7 | src/components/Sidebar.tsx | COMPLETED | #11 | NEW — Navigation sidebar |
| 8 | src/components/Dashboard.tsx | COMPLETED | #11 | NEW — Home dashboard |
| 9 | src/components/TransactionsView.tsx | COMPLETED | #11 | NEW — Searchable transactions |
| 10 | src/styles.css | COMPLETED | #12 | Responsive chart styles fixed |

## Design Decisions

| Decision | Rationale | Alternative Rejected | Entry |
|----------|-----------|---------------------|-------|
| Extract finance-core.ts | Electron env makes index.ts untestable directly | Mock electron module (fragile) | #1 |
| Dependency injection via FinanceDeps | Enables mocking execFile and openai in tests | Module-level monkey-patching | #1 |
| Fix runFinanceCommand to accept pre-split args | CRITICAL: whitespace split breaks SQL queries | Shell escaping (no shell used) | #1 |
| eventSender interface instead of IpcMainInvokeEvent | Allows plain-object mock in tests | Importing electron types in tests | #1 |
| Parallelize tool calls | Reduces latency for multiple independent SQL queries | Sequential execution | #5 |
| Remove dashboard instruction | Avoids unnecessary 3.5s API round trip at startup | Keep dashboard for "freshness" | #5 |
| Path validation in initConfig | Prevent obscure ENOENT errors on startup/tests | No validation (silent failure) | #5 |
| Switch to Sonnet 3.7 | Faster response times and better reasoning for tool batching | Sonnet 3.5 (slower RTT) | #6 |
| Context Pruning (10 msgs) | Keeps prompt size small for faster processing | Full history (grows latency over time) | #6 |
| Tool Batching Instructions | Explicitly tells model to call multiple tools at once | Implicit behavior (resulted in sequential rounds) | #6 |
| Tool Error Logging | Wrap parse failures and unknown tools in timed() to expose "ghost" rounds | Silent failures | #7 |
| Markdown Stripping | Clean tool arguments of ```json blocks | Strict JSON parse | #7 |
| Result Truncation | Limit SQL results to 15k chars to prevent context bloat | Unlimited results | #7 |
| execute_batch_sql tool | Structural forcing of parallel execution | Purely prompt-based batching | #8 |
| Headless Analyst Mode | Prohibit conversational filler to prevent turn-ending | Mixed content (text + tools) | #8 |
| Strip Conversational Filler | Clear `msg.content` if tool calls exist to prevent history pollution | Feeding filler back to LLM | #9 |
| Aggressive Truncation | Lowered SQL truncation limits from 15k/25k to 4k/8k to prevent bloat | Leaving massive JSON in prompt | #9 |
| Lower SQL Limits | Prompt instructs `LIMIT 15` instead of 50 | Allowing 50 rows per query | #9 |
| localIntentRouter | Intercept common queries locally to inject context | Always going to cloud for intent | #11 |
| Standardized Charts | Pre-baked Python scripts for 10x faster rendering | Generating Python on the fly | #12 |

## Conventions Verified

(Patterns confirmed from existing codebase)

## Test Cases

| ID | Description | Type | Status | Entry |
|----|-------------|------|--------|-------|
| T1 | loadEnv parses KEY=VALUE correctly | Unit | COMPLETED | #1 |
| T2 | loadEnv strips trailing whitespace/comments | Unit | COMPLETED | #1 |
| T3 | runFinanceCommand passes args correctly | Unit | COMPLETED | #1 |
| T4 | queryDB SQL with spaces passes as single arg | Unit/Regression | COMPLETED | #1 |
| T5 | queryDB parses JSON result to columns/rows | Unit | COMPLETED | #1 |
| T6 | handleChat single-turn no tool calls | Unit | COMPLETED | #1 |
| T7 | handleChat execute_sql tool loop | Unit | COMPLETED | #1 |
| T8 | handleChat run_finance_command tool loop | Unit | COMPLETED | #1 |
| T9 | generate_chart unlinkSync guarded in finally | Unit/Regression | COMPLETED | #1 |
| T10 | handleChat API error propagates | Unit | COMPLETED | #1 |
| T11 | initConfig throws if Python missing | Unit | COMPLETED | #5 |
| T12 | initConfig throws if finance script missing | Unit | COMPLETED | #5 |
| T13 | handleChat response includes timing info | Unit | COMPLETED | #5 |
| T14 | Conversational filler is stripped | Unit | COMPLETED | #10 |
| T15 | Massive SQL results are truncated | Unit | COMPLETED | #10 |
| T16 | History is pruned to last 10 messages | Unit | COMPLETED | #10 |

---

## Implementation Log (Append-Only)

...

### Entry #11 — 2026-03-12 — Phase 2: Implementation (UX & Local Intelligence)

**What**: Orchestrator implemented "Local Knowledge First" architecture and a hybrid Dashboard/Chat UX.
**Findings**:
- Even with model optimization, 8 sequential cloud round trips were taking 50s+.
- Intercepting "dashboard" intent locally and pre-fetching SQL results reduced rounds to 1.
- Missing `pandas` in venv caused chart generation failures.
**Changes**:
- `electron/finance-core.ts`: Added `localIntentRouter` to inject context before the first API call.
- `src/components/Sidebar.tsx`, `Dashboard.tsx`, `TransactionsView.tsx`: New navigation-based hybrid UX.
- Installed `pandas` in project venv.
**Status**: COMPLETED

### Entry #12 — 2026-03-12 — Phase 2: Implementation (Standardized Charts & Fixes)

**What**: Fixed "Unknown tool" error for charts and resolved UI resizing issues.
**Findings**:
- `generate_standard_chart` was registered in `TOOLS` but missing from the backend execution loop, causing 30s latency as the LLM fell back to slow manual coding.
- Charts were not resizing correctly in the message bubbles, causing horizontal overflow.
**Changes**:
- `electron/finance-core.ts`: Implemented backend execution for `generate_standard_chart` using pre-baked Python templates.
- `src/styles.css`: Added responsive CSS for `.chart-container` and `.chart-image`.
**Next**: Human review.
**Status**: READY_FOR_REVIEW
