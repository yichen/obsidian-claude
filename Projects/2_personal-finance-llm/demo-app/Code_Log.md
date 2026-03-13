# Code Log: Finance Demo App — Verification & Test Infrastructure

Started: 2026-03-12
Last Updated: 2026-03-12
Status: READY_FOR_REVIEW
**Branch**: feature/finance-demo-app-tests

---

## Implementation Tracker

| ID | File/Component | Status | Entry | Notes |
|----|---------------|--------|-------|-------|
| 1 | electron/finance-core.ts | COMPLETED | #9 | Aggressive Context Reduction |
| 2 | electron/index.ts | COMPLETED | #2 | Thin Electron shell after extraction |
| 3 | vitest.config.ts | COMPLETED | #2 | NEW — test runner config |
| 4 | electron/__tests__/electron-mock.ts | COMPLETED | #3 | NEW — mock factories |
| 5 | electron/__tests__/finance-core.test.ts | COMPLETED | #5 | Updated for timing info |
| 6 | electron/__tests__/config.test.ts | COMPLETED | #5 | NEW — path validation tests |
| 7 | Implementation.md | COMPLETED | #9 | Updated |

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

---

## Implementation Log (Append-Only)

...

### Entry #7 — 2026-03-12 — Phase 2: Implementation (Robustness & Traceability)

**What**: Orchestrator improved tool parsing robustness and timing trace visibility.
**Findings**:
- Claude sometimes wrapped JSON arguments in markdown blocks (e.g. ` ```json `), causing silent parse failures and "ghost" API calls (10s+ latency with no visible tool execution).
- Massive SQL results were bloating the context window, causing subsequent API calls to take 10-12s.
- The `SYSTEM_PROMPT` still implicitly encouraged sequential tool execution.
**Changes**:
- `electron/finance-core.ts`: Updated `SYSTEM_PROMPT` to aggressively ban conversational filler and mandate LIMIT 50.
- `electron/finance-core.ts`: Added markdown stripping to the tool arguments JSON parser.
- `electron/finance-core.ts`: Wrapped parse errors and unknown tool fallbacks in `timed()` to expose them in the timing trace.
- `electron/finance-core.ts`: Added 15,000 character truncation to massive SQL results to prevent context explosion.
**Next**: Human review.
**Status**: COMPLETED

### Entry #8 — 2026-03-12 — Phase 2: Implementation (Structural Parallelism)

**What**: Orchestrator introduced a new tool and a "Headless" prompt mode to force tool batching.
**Findings**:
- Claude 3.7 was ignoring "EFFICIENCY" prompts and doing 8 sequential rounds for a dashboard.
- Conversational filler text like "I'll pull that data..." was triggering model-side stops, preventing batching.
- Multi-tool parallelism is supported by the code but the model needs a structural hint (single tool with array) to use it reliably.
**Changes**:
- `electron/finance-core.ts`: Added `execute_batch_sql` tool taking an array of queries.
- `electron/finance-core.ts`: Refactored `handleChat` to process batched queries in parallel via `Promise.all`.
- `electron/finance-core.ts`: Switched to "HEADLESS ANALYST MODE" in `SYSTEM_PROMPT`, strictly prohibiting conversational filler before data is ready.
**Next**: Human review.
**Status**: COMPLETED

### Entry #9 — 2026-03-12 — Phase 2: Implementation (Aggressive Context Reduction)

**What**: Orchestrator implemented extreme measures to prevent context bloat and sequential rounds.
**Findings**:
- Claude was *still* generating conversational filler ("I'll fetch that...") before executing tools, which we discovered by reading the `debug/chat_request_round_*.json` files. This text was fed back into the context in the next round, tricking the LLM out of "Headless" mode and causing it to execute sequentially.
- The 15k/25k character truncation limits were too generous. 25,000 characters is ~6,000 tokens, which was causing the massive latency spikes.
**Changes**:
- `electron/finance-core.ts`: Added logic to actively strip `msg.content` if `msg.tool_calls` exists, entirely removing the conversational filler from the history loop.
- `electron/finance-core.ts`: Lowered `execute_sql` truncation limit to 4,000 characters.
- `electron/finance-core.ts`: Lowered `execute_batch_sql` truncation limit to 8,000 characters.
- `electron/finance-core.ts`: Updated `SYSTEM_PROMPT` to mandate `LIMIT 15` instead of `LIMIT 50`.
**Next**: Human review and latency verification.
**Status**: READY_FOR_REVIEW
