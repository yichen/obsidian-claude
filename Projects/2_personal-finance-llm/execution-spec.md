# Specification: Finance AI Demo App — Design System & Real Data Integration

## Goal
Bring the existing Electron/React demo app (`demo-app/`) into full compliance with the product SPEC.md by: (1) canonicalizing CSS variables across all pages, (2) replacing Tailwind-only class usage in TransactionsView and ChatInterface with standard CSS, (3) wiring the Home page to real SQLite metrics instead of hardcoded values, and (4) fixing remaining typography and nav state inconsistencies.

## Background

A working Electron + React + TypeScript demo app exists at `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/demo-app/`. It has three pages and a full backend:

**What is already working:**
- **IPC bridge**: `window.api.dbQuery(sql)` is live. `preload.ts` exposes it; `index.ts` handles `db:query` via `finance-core.ts → queryDB() → finance_db.py query <sql>`.
- **Chat page**: Fully functional — wired to OpenRouter (Claude 3.7), has `execute_sql`, `execute_batch_sql`, `generate_chart`, `generate_standard_chart`, `run_finance_command` tools, local intent router, and base64 chart rendering.
- **Transactions data**: App.tsx pre-fetches 100 rows via `window.api.dbQuery` on startup and passes them as `initialData` to `TransactionsView`. Search also triggers live DB queries via `window.api.dbQuery`.

**What is broken / not done:**

| Area | Problem |
|------|---------|
| `TransactionsView.tsx` | **Entire component uses Tailwind classes** (`flex-1`, `bg-gray-50`, `px-6`, `py-4`, `rounded-xl`, `text-rose-600`, etc.). No Tailwind is installed. Nothing renders styled. |
| `ChatInterface.tsx` | Uses Tailwind in the header (`flex items-center gap-2`, `text-emerald-500`, `h-4`) and suggestion icon colors (`text-blue-500`, `text-rose-500`, etc.). Missing `new-session-btn` CSS rule. |
| CSS variables | `:root` uses non-canonical names: `--bg-page` (should be `--bg-app`), `--bg-sidebar` (should be `--bg-surface`). SPEC Section 6 defines the canonical names. |
| Metric typography | `.metric-value` is `font-size: 28px; font-weight: 800`. SPEC requires `24px / weight 700` uniformly. |
| Active nav state | `.nav-item.active` has background tint but NO left-border indicator. SPEC requires `border-left: 3px solid var(--primary)`. |
| Section labels | `.section-header h2` CSS rule may lose to browser-default `<h2>` specificity, rendering at ~18px instead of 11px uppercase. |
| Home metrics | Dashboard shows hardcoded `32.4%`, `18.5 mo`, `+$2,450`. Should be computed from real DB data. |

**Tech stack:**
- Electron (Node main process + React renderer), `titleBarStyle: 'hiddenInset'`
- React + TypeScript, Vite build via electron-vite
- Single CSS file: `demo-app/src/styles.css` — standard CSS only, no Tailwind, no CSS modules
- Finance DB: `/Users/yichen/Obsidian/Finance/finance.db` (SQLite, read-only)
- Finance script: `Scripts/venv/bin/python3 .claude/scripts/finance_db.py query <sql>` → returns JSON array

**Reference documents:**
- Product SPEC: `/Users/yichen/Obsidian/Projects/2_personal-finance-llm/SPEC.md` — Sections 6, 7, 8 (design system, layout, constraints)
- Finance DB schema: `Finance/CLAUDE.md` — tables: `transactions`, `accounts`, `categories`, `payslips`, `fidelity_monthly_snapshots`, `fidelity_accounts`
- Theme tokens: `Projects/2_personal-finance-llm/theme-tokens.json`

## Acceptance Criteria

- [ ] All 7 CSS variables from SPEC Section 6 (`--bg-app`, `--bg-surface`, `--bg-card`, `--border`, `--text-main`, `--text-muted`, `--primary`) are defined in `:root`; old non-canonical names (`--bg-page`, `--bg-sidebar`) are replaced throughout
- [ ] Metric values render at exactly `font-size: 24px; font-weight: 700` — confirmed via DevTools computed styles on `.metric-value`
- [ ] Active nav item shows `border-left: 3px solid var(--primary)` plus background tint; no native browser `outline` visible on focus
- [ ] Section labels render at 11–12px uppercase muted text — confirmed by inspecting `.section-header h2` computed styles
- [ ] Transactions page renders with correct visual styling: headers, table rows, search bar, and amount colors all visually styled (not bare HTML)
- [ ] Chat page header area renders correctly: "Financial Analyst" heading + Sparkles icon left-aligned, "Reset Session" button right-aligned, styled (not bare HTML)
- [ ] Home page displays real computed values for Savings Rate, Net Cashflow, and Financial Runway — values differ from the hardcoded stubs
- [ ] App builds without TypeScript errors (`npm run build` in `demo-app/` exits 0)

## Constraints

### Musts
- Replace all Tailwind class references in `TransactionsView.tsx` and `ChatInterface.tsx` with named CSS classes defined in `styles.css`
- New CSS class names must follow the existing naming convention in `styles.css` (kebab-case, semantic names like `.txn-table`, `.search-bar`, not utility names)
- CSS variables must use the SPEC-canonical names exactly (`--bg-app`, not `--bg-page`) to prevent future drift
- Home metrics must come from real DB data via `window.api.dbQuery(sql)` — no hardcoded values
- All DB queries must include `WHERE is_transfer = 0` for CC transactions to exclude internal transfers
- `window.api.dbQuery` returns `{ columns: string[], rows: unknown[][] }` — type-guard before use

### Must Nots
- Do not add Tailwind, Bootstrap, or any CSS framework
- Do not create multiple CSS files — keep the single `styles.css` architecture
- Do not modify `Finance/finance.db` — the app is read-only
- Do not add new subcommands to `finance_db.py` — `query <sql>` already works
- Do not send raw transaction rows to the OpenRouter API — only aggregated summaries

### Preferences
- For `TransactionsView.tsx`: preserve the visual design intent (table layout, amount color coding red/green, category badges) but implement with standard CSS classes
- For Home metrics: use `Promise.all` to fetch all three metrics in parallel — one `window.api.dbQuery` per metric
- Keep `TransactionsView`'s existing search debounce logic (300ms setTimeout) — only replace class names, not behavior
- Runway: use most recent Fidelity CMA balance (account Z26-474983) divided by 3-month avg monthly spending

### Escalation Triggers
- Stop and ask if replacing Tailwind classes in `TransactionsView.tsx` requires more than 80 new CSS rules (may indicate the scope is larger than a CSS migration)
- Stop and ask if any Home metric query returns a value that looks wrong (negative runway, savings rate > 100%, zero income with non-zero payslips)
- Stop and ask if `fidelity_monthly_snapshots` or `fidelity_accounts` tables don't exist or return no rows for the CMA account

## Decomposition

| # | Sub-task | Estimated Effort | Dependencies | Break Pattern |
|---|----------|-----------------|--------------|---------------|
| 1 | Rename CSS vars in `styles.css` and all JSX files: `--bg-page` → `--bg-app`, `--bg-sidebar` → `--bg-surface`. Add missing vars (`--bg-surface`) to `:root`. | Small | None | Grep all `.tsx`/`.css` files for old var names; do each file |
| 2 | Fix metric typography in `styles.css`: `.metric-value { font-size: 24px; font-weight: 700 }` | Small | #1 | None |
| 3 | Fix active nav: add `border-left: 3px solid var(--primary)` to `.nav-item.active` in `styles.css`; verify `outline: none` is present | Small | #1 | None |
| 4 | Fix section label specificity: change `.section-header h2` to `.section-header > h2` and verify computed size is 11–12px | Small | #1 | If specificity still loses, replace `<h2>` with `<span class="section-label">` in Dashboard.tsx |
| 5 | Rewrite `TransactionsView.tsx` JSX: replace all Tailwind class names with semantic CSS class names; add all new rules to `styles.css` | Large | #1 | Split into: (a) container/header CSS, (b) search bar CSS, (c) table/thead CSS, (d) tbody row CSS, (e) amount color/icon CSS |
| 6 | Fix `ChatInterface.tsx`: replace Tailwind classes in chat header (`flex items-center gap-2`, etc.) with CSS classes; add `new-session-btn` CSS; replace Tailwind icon color classes with inline `style` or CSS | Small | #1 | Only the header div and suggestion icon spans need changes |
| 7 | Wire Home metrics to real DB: add `useEffect` + `Promise.all([dbQuery(spendSql), dbQuery(incomeSql), dbQuery(cmaSql)])` in `Dashboard.tsx`; compute savings rate, cashflow, runway | Medium | None | Three separate queries: (a) current-month CC spend, (b) most recent payslip month net pay, (c) CMA balance for runway |
| 8 | Verify clean build: `npm run build` exits 0; fix any TypeScript errors introduced | Small | #5, #6, #7 | Fix type errors file by file; add `DbResult` type for `window.api.dbQuery` return |

## Evaluation

| # | Test Case | Input | Expected Output | Verification Method |
|---|-----------|-------|-----------------|---------------------|
| 1 | CSS vars canonical | DevTools → Elements → `:root` | `--bg-app`, `--bg-surface`, `--bg-card`, `--border`, `--text-main`, `--text-muted`, `--primary` present | DevTools computed panel |
| 2 | Old vars gone | Grep for `--bg-page` and `--bg-sidebar` in codebase | Zero matches | `grep -r "bg-page\|bg-sidebar" src/` |
| 3 | Metric typography | Inspect `.metric-value` computed | `font-size: 24px`, `font-weight: 700` | DevTools |
| 4 | Active nav border | Click any nav item | 3px blue left border visible, no dotted outline ring | Visual + DevTools |
| 5 | Section labels | Inspect `.section-header h2` or `.section-label` computed | `font-size ≤ 12px`, `text-transform: uppercase` | DevTools |
| 6 | Transactions styled | Open Transactions page | Table has visible borders, colored amounts (red/green), styled search bar — not bare HTML | Visual |
| 7 | Transactions data | Open Transactions page | ≥1 row with real description, date, amount | Visual — not "No transactions" placeholder |
| 8 | Transactions search | Type "Amazon" | Table filters to Amazon rows | Visual |
| 9 | Chat header styled | Open Chat page | "Financial Analyst" + Sparkles icon left-aligned, "Reset Session" button right-aligned, styled | Visual |
| 10 | Home metrics real | Open Home page | Values differ from 32.4% / 18.5 mo / +$2,450 stubs | Compare to `/finance` query output |
| 11 | Clean build | `npm run build` in `demo-app/` | Exit code 0 | Terminal |
| 12 | No Tailwind classes | Grep for Tailwind patterns | Zero `className="... flex ...` or `className="... px-` patterns in `.tsx` files | `grep -r "px-[0-9]\|py-[0-9]\|text-gray\|text-rose\|text-emerald\|bg-gray\|rounded-xl\|flex-1\|flex-col" src/` |

## Data Sources

- **Finance DB**: `/Users/yichen/Obsidian/Finance/finance.db` (read-only)
- **IPC**: `window.api.dbQuery(sql: string)` → `Promise<{ columns: string[]; rows: unknown[][] } | { error: string }>`
- **DB tables used**: `transactions`, `accounts`, `categories`, `payslips`, `fidelity_monthly_snapshots`, `fidelity_accounts`
- **App source**: `Projects/2_personal-finance-llm/demo-app/src/`
- **CSS**: `Projects/2_personal-finance-llm/demo-app/src/styles.css`

**Home metrics queries:**

```sql
-- Current month CC spending
SELECT SUM(ABS(t.amount)) as spending
FROM transactions t
WHERE t.is_transfer = 0 AND t.amount < 0
AND strftime('%Y-%m', t.date) = strftime('%Y-%m', 'now');

-- Most recent payslip month net pay (across all employers)
SELECT SUM(p.net_pay) as income
FROM payslips p
WHERE strftime('%Y-%m', p.pay_date) = (
  SELECT strftime('%Y-%m', pay_date) FROM payslips ORDER BY pay_date DESC LIMIT 1
);

-- CMA liquid cash balance (account Z26-474983) for runway
SELECT fms.ending_value as cma_balance
FROM fidelity_monthly_snapshots fms
JOIN fidelity_accounts fa ON fa.id = fms.account_id
WHERE fa.account_number = 'Z26-474983'
ORDER BY fms.statement_date DESC LIMIT 1;

-- 3-month avg monthly spending (for runway denominator)
SELECT AVG(monthly) as avg_spending FROM (
  SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as monthly
  FROM transactions
  WHERE is_transfer = 0 AND amount < 0
  AND date >= date('now', '-3 months')
  GROUP BY m
);
```

**Derived metric formulas:**
- `savings_rate = ((income - spending) / income * 100).toFixed(1) + '%'` — clamp to 0–100%
- `net_cashflow = income - spending` — format as `+$X,XXX` or `-$X,XXX`
- `runway_months = (cma_balance / avg_monthly_spending).toFixed(1) + ' mo'`

## Related Work

- `Projects/2_personal-finance-llm/SPEC.md` — product requirements (Sections 6, 7, 8)
- `Projects/2_personal-finance-llm/demo-app/src/styles.css` — existing CSS (CSS fixes applied 2026-03-13)
- `Projects/2_personal-finance-llm/demo-app/electron/finance-core.ts` — `queryDB` implementation
- `Projects/2_personal-finance-llm/demo-app/electron/preload.ts` — `window.api.dbQuery` exposed
- `Projects/1_selling-rental/spec.md` — prior spec format reference
- `Finance/CLAUDE.md` — authoritative DB schema and key query patterns
