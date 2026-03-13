# Finance Demo App — Implementation

## What Was Built

The original `electron/index.ts` monolith mixed Electron lifecycle code with all business logic, making it impossible to unit test without spawning a real Electron window. The refactor extracted all testable logic into `electron/finance-core.ts` using dependency injection, leaving `electron/index.ts` as a thin shell. A full Vitest test suite covers every public function with mocks — no Electron runtime, no network, no filesystem required.

Recent updates added performance optimizations for tool call handling and robust startup validation to prevent obscure environment errors.

## Architecture

### Before (electron/index.ts monolith)

`electron/index.ts` contained everything: `loadEnv`, `initConfig`, `runFinanceCommand`, `queryDB`, `handleChat`, all tool definitions, and the system prompt — all mixed alongside `createWindow`, `app.whenReady`, and `ipcMain.handle` registrations. Because the file imported directly from `electron`, it could not be loaded in a Node/Vitest test environment at all.

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

## Performance Optimizations

### Parallel Tool Execution
The `handleChat` loop now processes `msg.tool_calls` concurrently. For complex questions that require multiple SQL queries (e.g., comparing spending across several categories), all queries run in parallel. This reduces total latency from `Sum(tool_times)` to `Max(tool_times)`.

### System Prompt Streamlining
Removed the "Start each session by running run_finance_command('dashboard')" instruction. While useful for freshness, it forced a 3rd API round trip for every single interaction. Claude now decides when it needs the dashboard versus when it can jump straight to SQL queries.

## Test Infrastructure

### Running Tests

```bash
cd demo-app
npm test
```

### Test Coverage

| Area | Tests | Description |
|------|-------|-------------|
| `loadEnv` | 5 | Parses KEY=VALUE, strips trailing whitespace, skips `#` comment lines, skips blank lines |
| `runFinanceCommand` | 5 | Correct argv construction, stdout returned, stderr fallback, error string on throw |
| `queryDB` | 5 | JSON array → `{columns, rows}`, empty array, `{error}` passthrough, exception handling |
| `handleChat` | 7 | Single-turn stop, `execute_sql` tool loop, `run_finance_command` event emission, `generate_chart` fs calls, timing info validation |
| `initConfig` | 3 | **NEW**: Validates existence of Python binary and finance script, throws descriptive errors on failure |

### Testing Without the Electron Window

`finance-core.ts` has no `import ... from 'electron'` at the module level. Vitest is configured with `environment: 'node'` and `server.deps.external: ['electron']`. Tests inject all external dependencies (subprocess execution, OpenAI client, filesystem, vault paths) via the `FinanceDeps` interface. `electron-mock.ts` provides four factory functions (`makeOpenAIMock`, `makeExecFileMock`, `makeFsMock`, `makeEventSender`) and a convenience `makeTestDeps` that wires them together.

## Key Design Decisions

- **Dependency injection over module-level state**: `FinanceDeps` passed explicitly to every function means tests can swap any dependency without monkey-patching module globals.
- **Parallel safety in `generate_chart`**: Added unique random suffixes to temporary Python script filenames to prevent collisions during parallel execution.
- **`initConfig()` lazy Electron require**: The `require('electron')` call inside `initConfig()` only executes when called with no arguments (production path), so importing `finance-core.ts` in tests never triggers an Electron module load.

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `electron/finance-core.ts` | Modified | Added parallel tool execution, timing info, and path validation |
| `electron/index.ts` | Refactored | Thin Electron shell delegating to `finance-core.ts` |
| `vitest.config.ts` | New | Vitest configuration |
| `electron/__tests__/finance-core.test.ts` | Modified | Updated tests for new response format (timing info) |
| `electron/__tests__/config.test.ts` | New | Unit tests for `initConfig` validation logic |
| `Code_Log.md` | Modified | Append-only implementation log tracking design decisions and performance optimizations |
| `start.sh` | New | Root-level script for environment pre-flight checks and safe startup |
