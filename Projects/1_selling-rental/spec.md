# Specification: Sell Rental Property at 2516 175th Ave NE

## Goal

Execute the sale of the rental property at 2516 175th Ave NE, Redmond WA to eliminate debt, create a cash reserve, and achieve near-breakeven monthly cash flow — enabling eventual transition to single-job sustainability before spousal maintenance ends (~late 2028).

## Background

Yi Chen owns a rental property at 2516 175th Ave NE, purchased in 2005 for $320,000, rented since December 2014. The property is cash-flow negative at -$405/mo (income $1,995 - mortgage $1,780 - HOA $620). Mr. Cooper estimates equity at ~$703K; Yi estimates a realistic sale price of ~$760K given deferred maintenance.

Yi currently works two full-time jobs (Salesforce + ServiceTitan) with combined take-home of ~$25,823/mo (after ESPP stopped Mar 2026, after-tax 401k already $0 at both employers). Monthly fixed obligations are $23,833, including $10,000/mo spousal maintenance (ends ~late 2028) and $1,254/mo child support. After recent spending cuts (legal costs eliminated post-divorce, hobby spending freeze on electronics/camping/photography, subscription cancellations), CC spending baseline is ~$2,723/mo, yielding a near-breakeven deficit of -$733/mo.

Selling the rental and using proceeds to pay off HELOC ($151K), SoFi loan ($41K), and Tesla loan ($45K) would create a $137K cash reserve and free $6,522/mo in debt payments. This changes the picture from -$733/mo to +$3,794/mo surplus with two jobs, and provides 23-31 months of runway on SF salary alone — enough to survive until spousal maintenance ends.

### Key Financial Facts

| Item | Value |
|------|-------|
| Property address | 2516 175th Ave NE, Redmond WA |
| Purchase price (2005) | $320,000 |
| Rental since | December 2014 |
| Mortgage lender | Mr. Cooper, Loan 694006164 |
| Mortgage balance | $219,493 |
| Estimated sale price | ~$760,000 |
| Net proceeds (pre-tax) | ~$497,500 |
| Capital gains tax estimate | ~$123,400 |
| Net cash after tax | ~$374,000 |
| After debt payoff | $137,000 cash reserve |
| Depreciation recapture | $100,400 (building $240K / 27.5yr x 11.5yr) |
| Spousal maintenance ends | ~late 2028 (~30 months from Mar 2026) |

## Acceptance Criteria

- [ ] Property listed with a real estate agent and sale process initiated
- [ ] Sale proceeds used to pay off HELOC, SoFi loan, and Tesla loan in full
- [ ] Cash reserve of ~$137K (or actual post-payoff remainder) established in accessible account
- [ ] Capital gains tax obligation estimated with CPA and estimated payment plan in place
- [ ] Tenant notified per WA landlord-tenant law requirements
- [ ] Monthly cash flow turns positive (or deficit reduced to < $500/mo) after sale closes

## Constraints

### Musts
- Notify current tenant per Washington State landlord-tenant law (60 days notice for month-to-month tenancy)
- Pay capital gains tax (estimated $123K) — either via estimated payments or with 2026 tax return `[INFERRED]`
- Use sale proceeds to pay off HELOC ($151K), SoFi ($41K), Tesla ($45K) before discretionary use `[INFERRED]`
- Consult CPA on actual depreciation recapture amount — the $100.4K estimate assumes 75/25 land/building split and "allowed or allowable" depreciation `[INFERRED]`
- Verify actual capital improvements made to property (would increase basis and reduce taxable gain) `[ASSUMED]`

### Must Nots
- Do NOT pursue 1031 exchange — defeats the liquidity purpose of this sale `[INFERRED]`
- Do NOT accept a sale price that results in less than $100K cash reserve after debt payoff and taxes `[ASSUMED]`
- Do NOT sign listing agreement without understanding commission structure and timeline `[ASSUMED]`

### Preferences
- Prefer selling vacant (better showings, higher price) — tenant is month-to-month, can give 60 days notice
- Prefer traditional sale over iBuyer/investor offer for higher net proceeds `[ASSUMED]`
- Target listing spring 2026, closing by summer 2026

### Escalation Triggers
- Stop and reassess if comparable sales suggest price significantly below $700K (would reduce cash reserve below $100K) `[ASSUMED]`
- Stop and reassess if tenant disputes notice or sale timeline `[ASSUMED]`
- Stop and consult CPA if capital improvements documentation changes the tax estimate by more than $10K `[ASSUMED]`
- Stop and reassess if either job is lost before sale closes — urgency and strategy may change `[ASSUMED]`

## Decomposition

| # | Sub-task | Estimated Effort | Dependencies | Break Pattern |
|---|----------|-----------------|--------------|---------------|
| 1 | Research WA landlord-tenant law for rental sale | Small | None | Check lease type (month-to-month vs fixed), required notice period, tenant rights |
| 2 | Engage real estate agent | Small | None | Agent already identified — confirm listing terms, commission, timeline |
| 3 | Determine property condition and needed repairs | Medium | None | Get agent walk-through assessment, decide on pre-sale repairs vs as-is pricing |
| 4 | Notify tenant per legal requirements | Small | 1 | Draft notice, send via required method, document |
| 5 | Gather capital improvement records | Small | None | Check receipts, contractor invoices, permits — increases basis and reduces tax |
| 6 | Consult CPA on capital gains tax strategy | Medium | 5 | Share basis, depreciation, improvements; get actual tax estimate; plan estimated payments |
| 7 | List property and manage sale process | Large | 2, 3, 4 | Agent handles showings, offers, negotiations; Yi reviews and approves |
| 8 | Close sale and receive proceeds | Medium | 7 | Title, escrow, mortgage payoff handled at closing |
| 9 | Pay off HELOC, SoFi, Tesla with proceeds | Small | 8 | Three payoff calls/transfers, confirm zero balances |
| 10 | Park remaining cash in accessible account | Small | 9 | High-yield savings or money market for the $137K reserve |
| 11 | Update cash flow analysis with actual numbers | Small | 9 | Actual sale price, actual tax, actual reserve → update projections |

## Evaluation

| # | Test Case | Input | Expected Output | Verification Method |
|---|-----------|-------|-----------------|---------------------|
| 1 | Sale price adequate | Listing and offers | >= $700K sale price | Compare to comps and minimum reserve threshold |
| 2 | Debts paid off | Sale proceeds | HELOC, SoFi, Tesla balances = $0 | Lender confirmation letters / zero balance statements |
| 3 | Cash reserve adequate | Post-payoff cash | >= $100K in accessible account | Bank statement |
| 4 | Tax obligation planned | CPA consultation | Estimated tax payment schedule in place | CPA letter or payment confirmation |
| 5 | Cash flow improved | Post-sale monthly budget | Monthly net >= +$2,000 (two jobs) or deficit <= $5,000 (SF only) | Updated cash flow spreadsheet |
| 6 | Single-job runway | Reserve / monthly deficit | >= 24 months on SF salary alone | Math: $137K / $4,342 = 31 months |

## Data Sources

| Source | Location | Purpose |
|--------|----------|---------|
| Cash flow analysis | `Finance/Planning/2026-03-01_Cash-Flow-Analysis-and-Rental-Sale-Decision.md` | Full financial analysis with scenarios |
| Finance database | `Finance/finance.db` | Income, spending, debt balances |
| Rental mortgage details | Mr. Cooper, Loan 694006164 | Payoff amount, process |
| HELOC details | BECU account 2019617876 | Balance $150,904, payoff process |
| SoFi loan | Account 0210879651 | Balance $41,356, payoff process |
| Tesla loan | Wells Fargo | Balance ~$45K, payoff process |
| Tax documents | `Finance/tax/` | Historical depreciation, basis info |
| Memory | `memory/MEMORY.md` — Rental Property, Cash Flow Analysis sections | Running context |

## Related Work

- `Finance/Planning/2026-03-01_Cash-Flow-Analysis-and-Rental-Sale-Decision.md` — comprehensive analysis recommending the sale
- Cash flow revision (Mar 2026 conversation): deficit reduced from -$6,785 to -$733/mo after hobby freeze + legal eliminated + ESPP stopped — sale is now optional deleveraging, not survival necessity
- Single-job analysis: SF only post-sale = -$4,342/mo with $137K reserve lasting 31 months (with reduced W-4), surviving until spousal ends ~late 2028
