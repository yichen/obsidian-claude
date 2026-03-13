# Finance Demo App — Implementation

## What Was Built

The original `electron/index.ts` monolith mixed Electron lifecycle code with all business logic, making it impossible to unit test without spawning a real Electron window. The refactor extracted all testable logic into `electron/finance-core.ts` using dependency injection, leaving `electron/index.ts` as a thin shell. A full Vitest test suite covers every public function with mocks — no Electron runtime, no network, no filesystem required.

Recent updates transformed the app into a high-performance **Hybrid Dashboard + Chat** application with local intelligence and standardized charting.

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
| Standard Chart Unknown Tool | High | `handleChat` | Implemented missing backend execution loop for `generate_standard_chart`, enabling the fast local path. |
| Chart Resizing Overflow | Low | `styles.css` | Added responsive CSS to ensure charts fit within message bubbles without horizontal scrolling. |

## Performance Optimizations

### Local Intent Router (Entry #11)
To eliminate the "Planning" round trip, I added a `localIntentRouter` that intercepts common dashboard requests. It pre-fetches the 3 most important SQL datasets locally and injects them as `assistant` context before the first cloud API call.

### Standardized Charts (Entry #12)
Instead of Claude writing 100+ lines of Python code (which takes 10s+ to type), I added `generate_standard_chart`. This tool uses pre-baked local Python templates for "monthly_cashflow" and "spending_by_category," executing them in milliseconds.

### Headless Analyst Mode & Filler Stripping
The `SYSTEM_PROMPT` was updated to **Headless Analyst Mode**. We now actively **strip `msg.content`** from assistant messages containing tool calls. This prevents Claude from reading its own conversational filler, which previously tricked it into sequential "chatty" behavior.

### Aggressive Context Reduction
- **Result Truncation**: SQL results are truncated at **4,000 characters** (single) and **8,000 characters** (batch) to prevent context window bloat.
- **Message Pruning**: History is pruned to the last 10 messages (`messages.slice(-10)`).
- **SQL Limits**: The prompt enforces **LIMIT 15** on all queries.

## New UX Features

### Home Dashboard
A new landing page displaying high-level metrics (Savings Rate, Runway, Cashflow) with one-click "Ask AI" deep-dive buttons.

### Searchable Transactions
A unified view to search across all accounts, categories, and descriptions in real-time using local SQL `LIKE` queries.

### Sidebar Navigation
Persistent navigation to toggle between Home, Transactions, and Chat.

## Test Infrastructure

### Running Tests

```bash
npm test
```
*(Runs from project root or `demo-app` directory)*

### Test Coverage

| Area | Tests | Description |
|------|-------|-------------|
| `loadEnv` | 5 | Parses KEY=VALUE, strips whitespace, skips comments. |
| `runFinanceCommand` | 5 | Correct argv construction, stdout returned. |
| `queryDB` | 5 | JSON array → `{columns, rows}`, exception handling. |
| `handleChat` | 7 | Single-turn stop, tool loops, timing info validation. |
| `initConfig` | 3 | Validates critical paths (Python, scripts). |
| `Context Bloat` | 4 | **NEW**: Filler stripping, truncation, history pruning. |
| `Integrity` | 2 | **NEW**: Validates `SYSTEM_PROMPT` and `TOOLS` load correctly. |

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `electron/finance-core.ts` | Modified | Core engine with local router, parallel tools, and filler stripping. |
| `src/components/*` | New | `Sidebar`, `Dashboard`, `TransactionsView` components. |
| `src/styles.css` | Modified | Complete layout and responsive chart styling. |
| `electron/mcp-server.ts` | New | Reference implementation for a standalone MCP sidecar. |
| `start.sh` | New | Pre-flight environment checks. |
| `package.json` | Modified | Root proxy for easy command execution. |
