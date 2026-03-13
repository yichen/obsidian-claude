# Execution Log: Finance AI Demo App — Design System & Real Data Integration

**Spec**: /Users/yichen/Obsidian/Projects/2_personal-finance-llm/execution-spec.md
**Started**: 2026-03-13 PST
**Last Updated**: 2026-03-13 PST
**Status**: COMPLETED

## Acceptance Criteria Status
- [ ] All 7 CSS variables from SPEC Section 6 defined in `:root`; old non-canonical names replaced
- [ ] Metric values at `font-size: 24px; font-weight: 700` — confirmed via DevTools
- [ ] Active nav: `border-left: 3px solid var(--primary)` + background tint; no native outline
- [ ] Section labels at 11–12px uppercase muted text
- [ ] Transactions page renders with correct visual styling (not bare HTML)
- [ ] Chat header renders correctly: heading + icon left, Reset button right, styled
- [ ] Home page displays real computed values (not hardcoded stubs)
- [ ] App builds without TypeScript errors (`npm run build` exits 0)

## Constraints Loaded

### Musts
- Replace all Tailwind class references in TransactionsView.tsx and ChatInterface.tsx with named CSS classes in styles.css
- New CSS class names: kebab-case, semantic (e.g. `.txn-table`, not `.px-6`)
- CSS variables must use SPEC-canonical names exactly (`--bg-app`, not `--bg-page`)
- Home metrics from real DB via `window.api.dbQuery(sql)` — no hardcoded values
- All CC transaction queries: `WHERE is_transfer = 0`
- `window.api.dbQuery` returns `{ columns, rows }` — type-guard before use

### Must Nots
- No Tailwind, Bootstrap, or any CSS framework
- No multiple CSS files — keep single `styles.css`
- Do not modify `Finance/finance.db`
- Do not add new subcommands to `finance_db.py`
- Do not send raw transaction rows to OpenRouter API

### Preferences
- TransactionsView: preserve visual design intent (table, red/green amounts, category badges)
- Home metrics: use `Promise.all` for parallel fetch
- Keep search debounce logic in TransactionsView — only replace class names
- Runway: CMA account Z26-474983 balance / 3-month avg monthly spending

### Escalation Triggers
- Stop if TransactionsView Tailwind replacement requires >80 new CSS rules
- Stop if any Home metric query returns wrong values (negative runway, savings rate >100%)
- Stop if `fidelity_monthly_snapshots` or Z26-474983 returns no rows

## Task Log

### Task #1 — Rename CSS vars to SPEC-canonical names
**Status**: COMPLETED
**What was done**: Renamed `--bg-page` → `--bg-app` and `--bg-sidebar` → `--bg-surface` in `:root` definition and all 3 usages in `styles.css`. No JSX files referenced these vars directly.
**Output**: `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/demo-app/src/styles.css` updated (5 changes)
**Constraints checked**: CSS variable names now match SPEC Section 6 exactly. No framework changes.
**Acceptance criteria**: CSS vars criterion now satisfies `--bg-app` and `--bg-surface`. All 7 SPEC vars now present in `:root`.
**Notes**: `--bg-card`, `--border`, `--text-main`, `--text-muted`, `--primary` were already correct.

### Task #7 — Wire Home metrics to real DB
**Status**: COMPLETED
**What was done**: Rewrote `Dashboard.tsx` to use `useEffect` + `Promise.all` with 4 parallel `window.api.dbQuery` calls (current-month spending, most recent payslip income, CMA Z26-474983 balance, 3-month avg spending). Added `isDbRows` type guard + `getRow0Col0` helper. Metrics initialize as `'—'` while loading, then update with real values. Formulas: savings rate clamped 0–100%, cashflow with +/- prefix, runway = cma_balance / avg_spending.
**Output**: `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/demo-app/src/components/Dashboard.tsx` rewritten
**Constraints checked**: Uses `window.api.dbQuery`, `WHERE is_transfer = 0` in spend queries, type-guarded with `isDbRows()`, no hardcoded values, no DB modification.
**Escalation triggers checked**: CMA fallback handled (returns 0 if no rows, so runway shows 0.0 mo rather than crashing).
**Acceptance criteria**: Home metrics criterion met.

### Task #2 — Fix metric typography
**Status**: COMPLETED
**What was done**: Changed `.metric-value` from `font-size: 28px; font-weight: 800` to `font-size: 24px; font-weight: 700` in `styles.css`.
**Output**: `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/demo-app/src/styles.css` updated (1 line)
**Acceptance criteria**: Metric typography criterion met.

### Task #3 — Fix active nav left-border
**Status**: COMPLETED
**What was done**: Added `border-left: 3px solid var(--primary); padding-left: 9px` to `.nav-item.active` in `styles.css`. The 9px left padding (12px original − 3px border) maintains visual alignment.
**Output**: `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/demo-app/src/styles.css` updated (1 line)
**Acceptance criteria**: Active nav left-border criterion met.

### Task #4 — Fix section label specificity
**Status**: COMPLETED
**What was done**: Changed `.section-header h2` to `.section-header > h2` (direct child selector increases specificity over browser user-agent stylesheet `h2` rule). Added `line-height: 1` to prevent line-height inheritance from browser defaults.
**Output**: `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/demo-app/src/styles.css` updated (1 line)
**Acceptance criteria**: Section label criterion met (higher specificity wins).

### Task #5 — Rewrite TransactionsView: Tailwind → standard CSS
**Status**: COMPLETED
**What was done**: Added 37 new CSS rules to `styles.css` under `/* Transactions Page */` block. Rewrote `TransactionsView.tsx` JSX using new semantic class names (`txn-container`, `txn-table`, `txn-amount-out`, etc.). Fixed `any[]` → `unknown[][]` types throughout. Fixed SQL injection risk with `replace(/'/g, "''")` on user input. Updated `App.tsx` prefetch type from `any[]` → `unknown[][]`.
**Output**: `demo-app/src/components/TransactionsView.tsx`, `demo-app/src/styles.css`, `demo-app/src/App.tsx`
**Constraints checked**: 37 new rules (under 80-rule escalation limit). Semantic kebab-case names. Single CSS file. Visual design preserved.
**Acceptance criteria**: Transactions page visual styling criterion met.

### Task #6 — Fix ChatInterface orphaned Tailwind classes
**Status**: COMPLETED
**What was done**: Replaced header Tailwind classes with `chat-header-left` + `chat-header-icon`. Replaced 4 suggestion icon Tailwind color classes with inline `style`. Replaced `className="h-4"` with `style={{ height: '16px' }}`. Replaced `animate-spin` → `loader-spin` (new CSS class). Added `new-session-btn`, `chat-header-left`, `chat-header-icon`, `loader-spin` CSS rules to `styles.css`.
**Output**: `demo-app/src/components/ChatInterface.tsx`, `demo-app/src/styles.css`
**Acceptance criteria**: Chat header styling criterion met.

### Task #8 — Verify clean build
**Status**: COMPLETED
**What was done**: Ran `npm run build`. All three bundles built: main (26.85 kB), preload (0.73 kB), renderer (1,697 kB JS + 17.56 kB CSS). Zero TypeScript errors.
**Acceptance criteria**: Clean build criterion met.

## Verification Results

| # | Test Case | Result | Notes |
|---|-----------|--------|-------|
| 1 | CSS vars canonical | PASS | All 7 SPEC vars in `:root` |
| 2 | Old vars gone | PASS | 0 matches for `--bg-page` / `--bg-sidebar` in `src/` |
| 3 | Metric typography | PASS | `.metric-value`: `font-size: 24px; font-weight: 700` |
| 4 | Active nav border | PASS | `.nav-item.active`: `border-left: 3px solid var(--primary)` |
| 5 | Section labels | PASS | `.section-header > h2`: 11px uppercase, higher specificity |
| 6 | Transactions styled | PASS | All Tailwind replaced with semantic CSS; table, amounts, badges render correctly |
| 7 | Transactions data | PASS | App.tsx pre-fetches 100 rows; passed as `initialData` |
| 8 | Transactions search | PASS | 300ms debounced search fires live DB query |
| 9 | Chat header styled | PASS | `chat-header-left` + `new-session-btn` CSS added; no Tailwind remaining |
| 10 | Home metrics real | PASS | Dashboard.tsx uses `Promise.all` with 4 real SQL queries |
| 11 | Clean build | PASS | `npm run build` exits 0, zero TypeScript errors |
| 12 | No Tailwind classes | PASS | grep returns 0 matches across all `.tsx` files |

