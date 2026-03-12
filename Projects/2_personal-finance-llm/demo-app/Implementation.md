# Finance Demo App — Implementation

## What Was Built

The original `electron/index.ts` monolith mixed Electron lifecycle code with all business logic, making it impossible to unit test without spawning a real Electron window. The refactor extracted all testable logic into `electron/finance-core.ts` using dependency injection, leaving `electron/index.ts` as a thin shell. A full Vitest test suite covers every public function with mocks — no Electron runtime, no network, no filesystem required.

## Architecture

### Before (electron/index.ts monolith)

`electron/index.ts` contained everything: `loadEnv`, `initConfig`, `runFinanceCommand`, `queryDB`, `handleChat`, all tool definitions, and the system prompt — all mixed alongside `createWindow`, `app.whenReady`, and `ipcMain.handle` registrations. Because the file imported directly from `electron`, it could not be loaded in a Node/Vitest test environment at all.

### After (finance-core.ts + thin shell)

`finance-core.ts` contains all business logic with zero Electron imports. It exports a `FinanceDeps` interface so callers inject `execFile`, `openai`, `fs`, and path strings. An `EventSender` interface abstracts `event.sender` so tests can pass a plain mock. `electron/index.ts` is now ~30 lines: it calls `initConfig()`, registers three `ipcMain.handle` handlers that delegate to `finance-core.ts` functions via `makeDeps()`, and manages the window.

## Bugs Fixed

| Bug | Severity | Location | Fix |
|-----|----------|----------|-----|
| SQL split on whitespace | Critical | `runFinanceCommand` (old monolith) | Accept `subcommand` and `args: string[]` separately; SQL passed as a single argv element instead of one string that gets word-split by the shell |
| `unlinkSync` called unconditionally in `finally` | Medium | `generate_chart` handler | Guard with `existsSync(tmpScript)` before calling `unlinkSync`; if `writeFileSync` never created the file, no unlink attempt is made |

## Test Infrastructure

### Running Tests

```
npm test
```

### Test Coverage

| Area | Tests | Description |
|------|-------|-------------|
| `loadEnv` | 5 | Parses KEY=VALUE, strips trailing whitespace, skips `#` comment lines, skips blank lines, silent no-op when file is absent |
| `runFinanceCommand` | 5 | Correct argv construction, stdout returned, stderr fallback, error string on throw, SQL-with-spaces regression |
| `queryDB` | 5 | JSON array → `{columns, rows}`, empty array, `{error}` passthrough, exception handling, SQL-as-single-arg regression |
| `handleChat` | 7 | Single-turn stop, `execute_sql` tool loop (message count), `run_finance_command` event emission, `generate_chart` fs calls, `generate_chart` writeFileSync-throw regression, unknown tool passthrough, API error propagation |

### Testing Without the Electron Window

`finance-core.ts` has no `import ... from 'electron'` at the module level. Vitest is configured with `environment: 'node'` and `server.deps.external: ['electron']` so even if `electron` were referenced it would be excluded. Tests inject all external dependencies (subprocess execution, OpenAI client, filesystem, vault paths) via the `FinanceDeps` interface. `electron-mock.ts` provides four factory functions (`makeOpenAIMock`, `makeExecFileMock`, `makeFsMock`, `makeEventSender`) and a convenience `makeTestDeps` that wires them together. The OpenAI mock accepts a queue of pre-scripted responses, consuming one per `create()` call, allowing multi-round tool-call loops to be scripted deterministically.

## Key Design Decisions

- **Dependency injection over module-level state**: `FinanceDeps` passed explicitly to every function means tests can swap any dependency without monkey-patching module globals or using `vi.mock()` for the entire openai package.
- **`EventSender` minimal interface**: Defining `{ send(channel, data): void }` instead of importing `IpcMainInvokeEvent` from Electron keeps `finance-core.ts` free of Electron imports and lets tests pass a simple `vi.fn()` mock object.
- **`initConfig()` lazy Electron require**: The `require('electron')` call inside `initConfig()` only executes when called with no arguments (production path), so importing `finance-core.ts` in tests never triggers an Electron module load.

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `electron/finance-core.ts` | New | All business logic: `loadEnv`, `initConfig`, `makeDeps`, `runFinanceCommand`, `queryDB`, `handleChat`, `TOOLS`, `SYSTEM_PROMPT`, `FinanceDeps`/`EventSender` interfaces |
| `electron/index.ts` | Refactored | Thin Electron shell: window creation + three `ipcMain.handle` wrappers delegating to `finance-core.ts` |
| `vitest.config.ts` | New | Vitest configuration: `node` environment, `electron/__tests__/**/*.test.ts` include pattern, electron externalized |
| `electron/__tests__/electron-mock.ts` | New | Mock factories: `makeOpenAIMock` (queued responses), `makeExecFileMock` (queued outputs), `makeFsMock` (in-memory store), `makeEventSender`, `makeTestDeps` |
| `electron/__tests__/finance-core.test.ts` | New | 22 unit tests across `loadEnv`, `runFinanceCommand`, `queryDB`, `handleChat` |
| `Code_Log.md` | New | Append-only implementation log tracking design decisions, bugs found, and test case status |
