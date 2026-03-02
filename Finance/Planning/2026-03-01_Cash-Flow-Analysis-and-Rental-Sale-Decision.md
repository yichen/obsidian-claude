# Cash Flow Analysis & Rental Sale Decision

**Date**: 2026-03-01
**Status**: Analysis complete, decision pending

## Data Sources

All figures from finance.db as of Mar 1, 2026:
- Payslips: Feb 2026 salary deposits (Salesforce + ServiceTitan)
- BECU statements: checking + HELOC through Feb 2026
- SoFi loan statements: through Feb 2026
- Fidelity CMA transactions: through Jan 2026
- CC spending: through Feb 2026

## Debt Summary (Feb 2026)

| Debt | Lender | Balance | Rate | Monthly Payment | Notes |
|------|--------|--------:|-----:|----------------:|-------|
| HELOC | BECU | $150,904 | 6.99% | $1,358 min | $230K limit, $79K available. Variable + 2 fixed rate advances |
| SoFi Loan | SoFi | $41,356 | ~2.1% | $1,764 | Draw period expired, declining ~$1.7K/mo |
| Tesla Auto Loan | Wells Fargo | ~$45,000 | TBD | $1,000 | Started Nov 2025, $1K/mo via BECU auto-draft |
| Rental Mortgage | Mr. Cooper | $219,493 | TBD | $1,780 | 2516 175th Ave NE, conventional 30-yr |
| Primary Mortgage | Mr. Cooper | TBD | TBD | $4,957 | Sammamish residence |
| **Total (excl primary)** | | **~$456K** | | **$5,902** | |

## Monthly Income (Feb 2026 Baseline)

| Source | Monthly | Notes |
|--------|--------:|-------|
| Salesforce salary deposits | $10,817 | 401k after-tax already reduced ($2,573→$123/chk). ESPP still deducting ~$1,638/chk |
| ServiceTitan salary deposits | $9,736 | 401k after-tax still deducting $1,442/chk |
| Rental income (Airbnb) | $1,995 | Consumed by rental property costs |
| **Total** | **$22,548** | |

### Pending adjustments

| Change | Cash freed | When |
|--------|----------:|------|
| Salesforce ESPP suspended | +$3,275/mo | Jun 2026 (current period ends May 31) |
| ServiceTitan after-tax 401k stopped | +$2,885/mo | Next pay period (still deducting in Feb) |
| **Total** | **+$6,160/mo** | |

### Bonus & RSU (deposit $0 currently)

RSU vestings and bonuses deposit $0 to bank — the after-tax 401k mega backdoor offset consumes everything after taxes:

| Event | Gross | Taxes | After-tax 401k | Deposit |
|-------|------:|------:|---------------:|--------:|
| RSU vest (Feb 2026) | $21,849 | $9,813 | $12,035 | $0 |
| RSU vest (Nov 2025) | $26,799 | $10,674 | $16,125 | $0 |
| Bonus (Sep 2025) | $14,587 | $3,552 | $11,035 | $0 |

Annual bonus ~$20K gross, quarterly RSU vesting ~$10K/quarter — all go to retirement.

## Monthly Obligations

| Obligation | Monthly | Paid from |
|------------|--------:|-----------|
| Spousal maintenance | $10,000 | CMA |
| Primary mortgage | $4,957 | CMA |
| Rental mortgage | $1,780 | CMA |
| SoFi loan | $1,764 | CMA |
| HELOC min payment | $1,358 | BECU checking |
| Child support | $1,254 | CMA |
| Tesla loan | $1,000 | BECU checking |
| Rental HOA | $620 | CMA (SAMMAMISH FORE) |
| Insurance (life/auto/home) | $550 | CMA |
| Kids costs (OFW net) | ~$500 | CMA (variable) |
| Primary HOA | $50 | CMA (check, $300/6mo) |
| **Total fixed** | **$23,833** | |

CC spending baseline: ~$5,500/mo (excluding travel spikes)

## Rental Property P&L

2516 175th Ave NE — rental since Dec 2014.

| Item | Monthly |
|------|--------:|
| Rental income | +$1,995 |
| Mortgage | -$1,780 |
| HOA | -$620 |
| **Net** | **-$405** |

The rental is cash-flow negative. Equity ~$703K per Mr. Cooper estimate.

## Cash Flow Scenarios

### Current state

| Scenario | Income | Fixed | CC | **Net/mo** |
|----------|-------:|------:|---:|----------:|
| Two jobs (Feb 2026) | $22,548 | $23,833 | $5,500 | **-$6,785** |
| Two jobs (Jun 2026+, after adjustments) | $28,708 | $23,833 | $5,500 | **-$625** |
| SF only (lose ST) | ~$15,700 | $23,833 | $5,500 | **-$13,600** |
| ST only (lose SF) | ~$12,800 | $23,833 | $5,500 | **-$16,500** |

Single-job estimates: current deposits + freed after-tax deductions + freed W-4 extra withholding.

**Key risk**: Only $79K HELOC availability remaining. At -$6,785/mo burn, HELOC exhausted by ~Oct 2026. Losing one job = insolvent in ~5 months.

### After selling rental + paying off debts

#### Sale proceeds estimate

| Item | Amount |
|------|-------:|
| Estimated sale price | ~$760,000 |
| Agent commission (5%) | -$38,000 |
| Closing/title/escrow | -$5,000 |
| Mortgage payoff | -$219,500 |
| **Net proceeds (pre-tax)** | **~$497,500** |

#### Capital gains tax estimate

Purchased 2005 for $320K. Rental since Dec 2014 (~11.5 years).

| Item | Amount | Notes |
|------|-------:|-------|
| Original cost basis | $320,000 | |
| Depreciation (must recapture) | -$100,400 | Building $240K (75%) / 27.5yr x 11.5yr |
| Adjusted basis | $219,600 | |
| Capital gain | $497,400 | $760K - $219.6K basis - $43K selling costs |

| Tax component | Gain | Rate | Tax |
|---------------|-----:|-----:|----:|
| Depreciation recapture | $100,400 | 25% | $25,100 |
| Long-term capital gain | $397,000 | 20% | $79,400 |
| Net Investment Income Tax | $497,400 | 3.8% | $18,900 |
| WA state | — | 0% | $0 |
| **Total tax** | | | **$123,400** |

**Cash after tax: ~$374,000**

Caveats:
- Capital improvements to the property would increase basis and reduce gain
- Depreciation recapture applies to "allowed or allowable" depreciation regardless of whether claimed
- Land/building split assumed 75/25; county tax assessment may differ
- 1031 exchange could defer all taxes but defeats the liquidity purpose
- Tax due with 2026 return or via estimated payments

#### Debt payoff with $374K

| Action | Cost | Remaining |
|--------|-----:|----------:|
| Starting cash | | $374,000 |
| Pay off HELOC ($151K) | -$151,000 | $223,000 |
| Pay off SoFi ($41K) | -$41,000 | $182,000 |
| Pay off Tesla (~$45K) | -$45,000 | $137,000 |
| **Cash reserve** | | **$137,000** |

#### Post-sale cash flow (Jun 2026+)

Obligations drop from $23,833 → $17,326 (eliminate rental mortgage/HOA, HELOC, SoFi, Tesla).

| Scenario | Income | Fixed | CC | **Net/mo** | $137K reserve lasts |
|----------|-------:|------:|---:|----------:|---:|
| Two jobs | $28,708 | $17,326 | $5,500 | **+$5,882** | indefinite |
| SF only | ~$15,700 | $17,326 | $5,500 | **-$7,100** | 19 months |
| ST only | ~$12,800 | $17,326 | $5,500 | **-$10,000** | 14 months |

## Recommendation

**Sell the rental.** Rationale:

1. **Rental is cash-flow negative** (-$405/mo) — it costs money to hold
2. **Eliminates 3 debts** (HELOC, SoFi, Tesla) + rental carrying costs = $6,500/mo freed
3. **Creates $137K cash reserve** — 14-19 months of single-job runway
4. **Enables sustainable mega backdoor** — +$5,882/mo surplus funds retirement contributions from cash flow, not HELOC debt at 6.99%
5. **Reduces job risk** — two overlapping full-time jobs is unsustainable; with the sale, losing one job is survivable
6. **Spousal maintenance ($10K/mo) ends ~late 2028** — after that, even single-job cash flow turns positive

Without selling: need ~$210K more HELOC draws over 2.5 years, but only $79K available. HELOC exhausted by ~Oct 2026.

### Timeline comparison

| | Don't sell | Sell + payoff |
|--|--|--|
| Two jobs (Jun+) | Breakeven, zero margin | +$5,900/mo surplus |
| Lose one job | Insolvent in ~5 months | 14-19 month runway |
| Spousal ends (late 2028) | Still tight on one job | One job fully sustainable |
| Mega backdoor | Funded by 6.99% HELOC debt | Funded by cash surplus |
| Emergency reserve | $0 (HELOC = reserve) | $137K cash |
