# Finance Demo App — Implementation

## What Was Built

The original `electron/index.ts` monolith mixed Electron lifecycle code with all business logic, making it impossible to unit test without spawning a real Electron window. The refactor extracted all testable logic into `electron/finance-core.ts` using dependency injection, leaving `electron/index.ts` as a thin shell. A full Vitest test suite covers every public function with mocks — no Electron runtime, no network, no filesystem required.

Recent updates added performance optimizations for tool call handling, robust startup validation, and aggressive context bloat reduction.

## Architecture

### After (finance-core.ts + thin shell)

`finance-core.ts` contains all business logic with zero Electron imports. It exports a `FinanceDeps` interface so callers inject `execFile`, `openai`, `fs`, and path strings. An `EventSender` interface abstracts `event.sender` so tests can pass a plain mock. `electron/index.ts` is now ~30 lines: it calls `initConfig()`, registers three `ipcMain.handle` handlers that delegate to `finance-core.ts` functions via `makeDeps()`, and manages the window.

## Bugs Fixed

| Bug | Severity | Location | Fix |
|-----|----------|----------|-----|
| SQL split on whitespace | Critical | `runFinanceCommand` | Accept `subcommand` and `args: string[]` separately; SQL passed as a single argv element instead of one string that gets word-split by the shell |
| `unlinkSync` called unconditionally in `finally` | Medium | `generate_chart` handler | Guard with `existsSync(tmpScript)` before calling `unlinkSync`; if `writeFileSync` never created the file, no unlink attempt is made |
| Sequential tool calls latency | High | `handleChat` | Refactored tool execution loop to use `Promise.all` for parallel execution of multiple independent tool calls (e.g., 4x SQL queries) |
| Mandatory dashboard latency | Medium | `SYSTEM_PROMPT` | Removed mandatory "dashboard" instruction at startup; Claude now goes straight to relevant data, saving ~3.5s per session |
| Obscure ENOENT on startup | Medium | `initConfig` | Added explicit `existsSync` validation for Python binary and finance script with descriptive error messages |
| "Ghost" API calls | Medium | `handleChat` | Stripped ` ```json ` blocks from tool arguments; wrapped parse errors and `Unknown tool` fallbacks in `timed()` to expose them in the timing trace. |

## Performance Optimizations

### Structural Parallelism (Entry #8)
To force batching in Claude 3.7 Sonnet, I introduced the `execute_batch_sql` tool. This allows the model to specify multiple queries in a single tool call, which the backend then executes in parallel via `Promise.all`. This structurally prevents the model from waiting for individual query results.

### Headless Analyst Mode & Filler Stripping (Entry #9)
The `SYSTEM_PROMPT` was updated to **Headless Analyst Mode**. The model is strictly prohibited from speaking to the user (no conversational filler) until all data is collected. Because Claude sometimes ignores this and outputs "I will pull that data..." alongside a tool call, we now actively **strip `msg.content`** before pushing it to the history array. This prevents the filler text from tricking the model out of its headless state in subsequent rounds.

### Aggressive Context Reduction (Entry #9)
- **Result Truncation**: Massive SQL results are now truncated at **4,000 characters** for single queries and **8,000 characters** for batch queries to prevent the context window from bloating, which was previously causing subsequent API calls to take 10-12s.
- **Message Pruning**: The message history is pruned to the last 10 messages (`messages.slice(-10)`) to keep the prompt small and processing times fast.
- **SQL Limits**: The prompt now instructs the model to "Always use **LIMIT 15**... unless you are aggregating data."

### Model Upgrade
Switched to `anthropic/claude-3.7-sonnet` via OpenRouter for faster reasoning and better tool batching adherence.

## Test Infrastructure

### Running Tests

```bash
cd demo-app
npm test
```
*(You can also run `npm test` from the project root thanks to a proxy `package.json`)*

### Test Coverage

| Area | Tests | Description |
|------|-------|-------------|
| `loadEnv` | 5 | Parses KEY=VALUE, strips trailing whitespace, skips `#` comment lines, skips blank lines |
| `runFinanceCommand` | 5 | Correct argv construction, stdout returned, stderr fallback, error string on throw |
| `queryDB` | 5 | JSON array → `{columns, rows}`, empty array, `{error}` passthrough, exception handling |
| `handleChat` | 7 | Single-turn stop, `execute_sql` tool loop, `run_finance_command` event emission, `generate_chart` fs calls, timing info validation |
| `initConfig` | 3 | **NEW**: Validates existence of Python binary and finance script, throws descriptive errors on failure |

## Key Design Decisions

- **Dependency injection over module-level state**: `FinanceDeps` passed explicitly to every function means tests can swap any dependency without monkey-patching module globals.
- **Parallel safety in `generate_chart`**: Added unique random suffixes to temporary Python script filenames to prevent collisions during parallel execution.
- **`initConfig()` lazy Electron require**: The `require('electron')` call inside `initConfig()` only executes when called with no arguments (production path), so importing `finance-core.ts` in tests never triggers an Electron module load.
- **Debug Traceability**: Full request payloads are saved to `Finance/reports/debug/*.json` before every API call, including token usage and `finish_reason` in the timing output.

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `electron/finance-core.ts` | Modified | Added parallel tool execution, timing info, path validation, result truncation, markdown stripping, `execute_batch_sql` tool, headless prompt mode, and filler stripping. |
| `electron/index.ts` | Refactored | Thin Electron shell delegating to `finance-core.ts` |
| `vitest.config.ts` | New | Vitest configuration |
| `electron/__tests__/finance-core.test.ts` | Modified | Updated tests for new response format (timing info) |
| `electron/__tests__/config.test.ts` | New | Unit tests for `initConfig` validation logic |
| `Code_Log.md` | Modified | Append-only implementation log tracking design decisions and performance optimizations |
| `start.sh` | New | Root-level script for environment pre-flight checks and safe startup |
| `package.json` | New | Project root proxy for delegating `npm test` and `npm run dev` to `demo-app` |
