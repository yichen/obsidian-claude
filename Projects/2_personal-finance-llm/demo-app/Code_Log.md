# Code Log: Finance Demo App — Verification & Test Infrastructure

Started: 2026-03-12
Last Updated: 2026-03-12
Status: READY_FOR_REVIEW
**Branch**: feature/finance-demo-app-tests

---

## Implementation Tracker

| ID | File/Component | Status | Entry | Notes |
|----|---------------|--------|-------|-------|
| 1 | electron/finance-core.ts | COMPLETED | #6 | Performance + Validation + Model 3.7 |
| 2 | electron/index.ts | COMPLETED | #2 | Thin Electron shell after extraction |
| 3 | vitest.config.ts | COMPLETED | #2 | NEW — test runner config |
| 4 | electron/__tests__/electron-mock.ts | COMPLETED | #3 | NEW — mock factories |
| 5 | electron/__tests__/finance-core.test.ts | COMPLETED | #5 | Updated for timing info |
| 6 | electron/__tests__/config.test.ts | COMPLETED | #5 | NEW — path validation tests |
| 7 | Implementation.md | COMPLETED | #6 | Updated for new features |

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

### Entry #1 — 2026-03-12 — Phase 1: Architecture Design

**What**: Architect explored all source files and designed test infrastructure.
**Findings**:
- CRITICAL: `queryDB` calls `runFinanceCommand("query \"<sql>\"")` which splits on whitespace, shattering the SQL into broken argv tokens. Every `execute_sql` tool call is broken.
- MEDIUM: `generate_chart` `finally` block calls `unlinkSync` unconditionally — if `writeFileSync` never created the file, `unlinkSync` throws a masking error.
- LOW: `openrouter` is `undefined` until `initConfig()` runs; safe in production lifecycle but blocks unit testing.
- `SYSTEM_PROMPT` and `handleChat` ordering is fine (no bug).
- `electron/index.ts` conflates Electron lifecycle + business logic — needs extraction for testability.
**Changes**: None (design phase only). Code_Log.md created.
**Next**: Implement in order: finance-core.ts, index.ts refactor, vitest.config.ts, mock helpers, test suite.
**Status**: Proceeding to Phase 2 (Implementation)

### Entry #2 — 2026-03-12 — Phase 2: Implementation

**What**: Implementer extracted `finance-core.ts`, rewrote `electron/index.ts` as thin shell, created `vitest.config.ts`, `electron/__tests__/electron-mock.ts`, `electron/__tests__/finance-core.test.ts`.
**Findings**: All 22 tests pass on first run (242ms). CRITICAL SQL bug fixed in `runFinanceCommand`. MEDIUM `unlinkSync` bug fixed in `generate_chart`.
**Changes**: 5 files created/modified.
**Next**: Code Review + Convention Check.
**Status**: Completed

### Entry #3 — 2026-03-12 — Phase 3+5: Code Review + Convention Check

**What**: Code Reviewer (opus) audited all files. Convention Checker (sonnet) verified patterns.
**Findings**:
- Code Reviewer: ACCEPT WITH CHANGES — 2 required fixes (JSON.parse try/catch; API key log reduction), 3 recommended (loop cap, dead code, spread bug)
- Convention Checker: ACCEPT — all 7 dimensions pass
**Changes**: Applied all 5 fixes. Tests still 22/22 green.
**Next**: Tester writes Implementation.md.
**Status**: Completed

### Entry #4 — 2026-03-12 — Phase 6: Test & Documentation

**What**: Tester ran final `npm test`, wrote `Implementation.md`.
**Findings**: 22/22 tests, 231ms. Implementation.md covers architecture, bugs fixed, test approach.
**Changes**: `Implementation.md` created.
**Next**: Human review.
**Status**: READY_FOR_REVIEW

### Entry #5 — 2026-03-12 — Phase 2: Implementation (Performance & Validation)

**What**: Orchestrator implemented performance optimizations and startup validation.
**Findings**:
- Sequential tool calls were causing 20s+ latency. Parallelizing reduced this for multiple queries.
- Removing mandatory "dashboard" call saved one full API round trip (~3.5s).
- Missing Python/script files caused obscure errors; added explicit `existsSync` checks in `initConfig`.
**Changes**:
- `electron/finance-core.ts`: Parallelized `handleChat`, added timing info to response, added `initConfig` validation, optimized `SYSTEM_PROMPT`.
- `electron/__tests__/finance-core.test.ts`: Updated to handle new response format.
- `electron/__tests__/config.test.ts`: Created new test suite for path validation.
**Next**: Finalize Implementation.md and run full test suite.
**Status**: COMPLETED

### Entry #6 — 2026-03-12 — Phase 2: Implementation (Model & Context Optimization)

**What**: Orchestrator upgraded model and optimized context handling to further reduce latency.
**Findings**:
- Sonnet 3.5 on OpenRouter was occasionally slow; 3.7 offers better performance.
- Unlimited context history increases per-token latency; pruning to 10 messages keeps it snappy.
- The model needed explicit "EFFICIENCY" instructions to favor batching tool calls.
**Changes**:
- `electron/finance-core.ts`: Switched model to `anthropic/claude-3.7-sonnet`.
- `electron/finance-core.ts`: Added `messages.slice(-10)` pruning in `handleChat`.
- `electron/finance-core.ts`: Added `EFFICIENCY` section to `SYSTEM_PROMPT`.
**Next**: Human review and verification of batching behavior.
**Status**: READY_FOR_REVIEW
