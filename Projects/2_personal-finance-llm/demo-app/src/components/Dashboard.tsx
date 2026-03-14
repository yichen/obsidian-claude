import React, { useState, useEffect, useRef, useMemo } from 'react'
import { PinnedChart } from '../lib/types'

interface DashboardProps {
  onDeepDive: (topic: string) => void
  pinnedCharts?: PinnedChart[]
  onUnpin?: (id: string) => void
}

interface Metric {
  label: string
  value: string
}

interface Insight {
  id: string
  type: 'success' | 'alert'
  text: string
}

interface UpcomingEvent {
  id: string
  label: string
  date: string
  amount: number
  type: 'income' | 'expense'
  confidence: 'high' | 'medium'
}

interface DbRows {
  rows: unknown[][]
}

function isDbRows(r: unknown): r is DbRows {
  return typeof r === 'object' && r !== null && 'rows' in r && Array.isArray((r as DbRows).rows)
}

function getRow0Col0(r: unknown): number {
  if (isDbRows(r) && r.rows.length > 0 && r.rows[0].length > 0) {
    return Number(r.rows[0][0]) || 0
  }
  return 0
}

function getRow0Col1(r: unknown): number {
  if (isDbRows(r) && r.rows.length > 0 && r.rows[0].length > 1) {
    return Number(r.rows[0][1]) || 0
  }
  return 0
}

function fmt(n: number, prefix = '', suffix = ''): string {
  return `${prefix}${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}${suffix}`
}

function formatRelativeDate(dateStr: string): string {
  const target = new Date(dateStr + 'T00:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffDays = Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Tomorrow'
  if (diffDays <= 7) return `In ${diffDays} days`
  return target.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export const Dashboard = React.memo(function Dashboard({ onDeepDive, pinnedCharts, onUnpin }: DashboardProps): React.ReactElement {
  const [metrics, setMetrics] = useState<Metric[]>([
    { label: 'Savings Rate', value: '—' },
    { label: 'Financial Runway', value: '—' },
    { label: 'Net Cashflow', value: '—' }
  ])

  const [insights, setInsights] = useState<Insight[]>([
    { id: 'placeholder', type: 'success', text: 'Loading insights…' }
  ])

  const [recentTopics, setRecentTopics] = useState<string[]>([])
  const [refreshedCharts, setRefreshedCharts] = useState<Record<string, string>>({})
  const [overviewCharts, setOverviewCharts] = useState<{ income: string | null; incomePie: string | null; spending: string | null; spendingPie: string | null }>({ income: null, incomePie: null, spending: null, spendingPie: null })
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([])

  // Lazy-load: track when pinned section is visible
  const pinsRef = useRef<HTMLDivElement>(null)
  const [pinsVisible, setPinsVisible] = useState(false)

  useEffect(() => {
    if (!pinsRef.current) return
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setPinsVisible(true) },
      { rootMargin: '200px' }
    )
    observer.observe(pinsRef.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        const [spendRes, incomeRes, cmaRes, avgRes, spendCompRes, uncatRes] = await Promise.all([
          window.api.dbQuery(
            `SELECT SUM(ABS(t.amount)) as spending FROM transactions t WHERE t.is_transfer = 0 AND t.amount < 0 AND strftime('%Y-%m', t.date) = strftime('%Y-%m', 'now')`
          ),
          window.api.dbQuery(
            `SELECT SUM(p.net_pay) as income FROM payslips p WHERE strftime('%Y-%m', p.pay_date) = (SELECT strftime('%Y-%m', pay_date) FROM payslips ORDER BY pay_date DESC LIMIT 1)`
          ),
          window.api.dbQuery(
            `SELECT fms.ending_value as cma_balance FROM fidelity_monthly_snapshots fms JOIN fidelity_accounts fa ON fa.id = fms.account_id WHERE fa.account_number = 'Z26-474983' ORDER BY fms.statement_date DESC LIMIT 1`
          ),
          window.api.dbQuery(
            `SELECT AVG(monthly) as avg_spending FROM (SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as monthly FROM transactions WHERE is_transfer = 0 AND amount < 0 AND date >= date('now', '-3 months') GROUP BY m)`
          ),
          window.api.dbQuery(
            `SELECT (SELECT SUM(ABS(amount)) FROM transactions WHERE is_transfer=0 AND amount<0 AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')) as this_month, AVG(monthly) as avg FROM (SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as monthly FROM transactions WHERE is_transfer=0 AND amount<0 AND date >= date('now', '-4 months') AND strftime('%Y-%m', date) != strftime('%Y-%m', 'now') GROUP BY m)`
          ),
          window.api.dbQuery(
            `SELECT COUNT(*) FROM transactions WHERE is_transfer=0 AND category_id IS NULL AND date >= date('now', '-3 months')`
          )
        ])

        const spending = getRow0Col0(spendRes)
        const income = getRow0Col0(incomeRes)
        const cmaBalance = getRow0Col0(cmaRes)
        const avgSpending = getRow0Col0(avgRes)

        const savingsRate = income > 0 ? Math.min(100, Math.max(0, ((income - spending) / income) * 100)) : 0
        const netCashflow = income - spending
        const runway = avgSpending > 0 ? cmaBalance / avgSpending : 0

        setMetrics([
          { label: 'Savings Rate', value: `${savingsRate.toFixed(1)}%` },
          { label: 'Financial Runway', value: `${runway.toFixed(1)} mo` },
          { label: 'Net Cashflow', value: netCashflow >= 0 ? `+$${fmt(netCashflow)}` : `-$${fmt(Math.abs(netCashflow))}` }
        ])

        // Build dynamic insights
        const newInsights: Insight[] = []

        const thisMonth = getRow0Col0(spendCompRes)
        const threeMonthAvg = getRow0Col1(spendCompRes)

        if (thisMonth > 0 && threeMonthAvg > 0) {
          const ratio = thisMonth / threeMonthAvg
          const pct = Math.round(Math.abs(ratio - 1) * 100)
          if (ratio > 1.1) {
            newInsights.push({
              id: 'spend-compare',
              type: 'alert',
              text: `Spending is ${pct}% above your 3-month average ($${fmt(thisMonth)} vs $${fmt(threeMonthAvg)} avg)`
            })
          } else if (ratio < 0.9) {
            newInsights.push({
              id: 'spend-compare',
              type: 'success',
              text: `Spending is ${pct}% below your 3-month average. Great discipline! ($${fmt(thisMonth)} vs $${fmt(threeMonthAvg)} avg)`
            })
          } else {
            newInsights.push({
              id: 'spend-compare',
              type: 'success',
              text: `Spending is on track with your 3-month average ($${fmt(thisMonth)})`
            })
          }
        }

        const uncatCount = getRow0Col0(uncatRes)
        if (uncatCount > 5) {
          newInsights.push({
            id: 'uncat',
            type: 'alert',
            text: `You have ${uncatCount} uncategorized transactions in the last 3 months`
          })
        }

        if (newInsights.length === 0) {
          newInsights.push({ id: 'fallback', type: 'success', text: 'Open AI Chat to get personalized insights from your transaction history.' })
        }

        setInsights(newInsights)
      } catch (err) {
        console.error('[Dashboard] Failed to load metrics:', err)
      }

      // Load recent session topics
      try {
        const topics = await window.api.recentTopics()
        if (Array.isArray(topics)) setRecentTopics(topics)
      } catch (_) {
        // optional — silently skip if not available
      }
    }
    load()
  }, [])

  // Dynamic refresh of pinned charts — only refresh new pins, only when visible
  useEffect(() => {
    if (!pinsVisible) return
    const refreshPins = async () => {
      for (const pin of pinnedCharts ?? []) {
        if (pin.chartType && !refreshedCharts[pin.id]) {
          const freshData = await window.api.generateChart(pin.chartType, pin.chartMonths ?? 6)
          if (freshData) {
            setRefreshedCharts(prev => ({ ...prev, [pin.id]: freshData }))
          }
        }
      }
    }
    refreshPins()
  }, [pinnedCharts, pinsVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  // Load overview charts
  useEffect(() => {
    const loadOverview = async () => {
      try {
        const [incomeBar, incomePie, spendingBar, spendingPie] = await Promise.all([
          window.api.generateChart('monthly_income', 6).catch(() => null),
          window.api.generateChart('income_by_source', 6).catch(() => null),
          window.api.generateChart('monthly_spending', 6).catch(() => null),
          window.api.generateChart('spending_by_category', 6).catch(() => null),
        ])
        setOverviewCharts({ income: incomeBar || '', incomePie, spending: spendingBar || '', spendingPie })
      } catch {
        setOverviewCharts({ income: '', incomePie: null, spending: '', spendingPie: null })
      }
    }
    loadOverview()
  }, [])

  // Load upcoming predicted financial events
  useEffect(() => {
    const loadUpcoming = async () => {
      try {
        const events: UpcomingEvent[] = []
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        const thirtyDaysOut = new Date(today)
        thirtyDaysOut.setDate(thirtyDaysOut.getDate() + 30)

        // 1. Predict next paychecks from payslips table
        const paycheckRes = await window.api.dbQuery(`
          SELECT employer, MAX(pay_date) as last_pay_date, net_pay as last_net_pay,
            CAST(AVG(gap) AS INTEGER) as avg_interval_days
          FROM (
            SELECT employer, pay_date, net_pay,
              julianday(pay_date) - julianday(LAG(pay_date) OVER (PARTITION BY employer ORDER BY pay_date)) as gap
            FROM payslips
          )
          WHERE gap IS NOT NULL
          GROUP BY employer
        `)
        if (isDbRows(paycheckRes)) {
          for (const row of paycheckRes.rows) {
            const employer = String(row[0])
            const lastPayDate = new Date(String(row[1]) + 'T00:00:00')
            const netPay = Number(row[2]) || 0
            const interval = Number(row[3]) || 14
            const nextDate = new Date(lastPayDate)
            nextDate.setDate(nextDate.getDate() + interval)
            // Advance if next date is in the past
            while (nextDate < today) nextDate.setDate(nextDate.getDate() + interval)
            if (nextDate <= thirtyDaysOut) {
              events.push({
                id: `paycheck-${employer}`,
                label: `Paycheck (${employer})`,
                date: nextDate.toISOString().slice(0, 10),
                amount: netPay,
                type: 'income',
                confidence: 'high'
              })
            }
          }
        }

        // 2. Detect recurring CMA payments
        const recurringRes = await window.api.dbQuery(`
          SELECT category, COUNT(*) as occurrences,
            ROUND(AVG(ABS(amount)), 2) as avg_amount,
            MAX(date) as last_date,
            CAST(AVG(gap) AS INTEGER) as avg_interval_days
          FROM (
            SELECT category, date, amount,
              julianday(date) - julianday(LAG(date) OVER (PARTITION BY category ORDER BY date)) as gap
            FROM fidelity_cma_transactions
            WHERE date >= date('now', '-6 months')
              AND amount < 0
              AND category NOT LIKE 'Transfer%'
              AND category IS NOT NULL
              AND category != ''
          )
          WHERE gap IS NOT NULL
          GROUP BY category
          HAVING occurrences >= 3 AND avg_interval_days BETWEEN 7 AND 45
          ORDER BY avg_amount DESC
        `)
        if (isDbRows(recurringRes)) {
          for (const row of recurringRes.rows) {
            const category = String(row[0])
            const avgAmount = Number(row[2]) || 0
            const lastDate = new Date(String(row[3]) + 'T00:00:00')
            const interval = Number(row[4]) || 30
            const occurrences = Number(row[1]) || 0
            const nextDate = new Date(lastDate)
            nextDate.setDate(nextDate.getDate() + interval)
            while (nextDate < today) nextDate.setDate(nextDate.getDate() + interval)
            if (nextDate <= thirtyDaysOut) {
              events.push({
                id: `recurring-${category}`,
                label: category,
                date: nextDate.toISOString().slice(0, 10),
                amount: -avgAmount,
                type: 'expense',
                confidence: occurrences >= 5 ? 'high' : 'medium'
              })
            }
          }
        }

        events.sort((a, b) => a.date.localeCompare(b.date))
        setUpcomingEvents(events)
      } catch (err) {
        console.error('[Dashboard] Failed to load upcoming events:', err)
      }
    }
    loadUpcoming()
  }, [])

  // Memoize pinned chart display data
  const pinnedDisplayData = useMemo(() =>
    (pinnedCharts ?? []).map(pin => ({
      ...pin,
      src: refreshedCharts[pin.id] ?? pin.chartData
    })),
    [pinnedCharts, refreshedCharts]
  )

  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div className="page-header-left">
          <h1>Financial Overview</h1>
          <p className="subtitle">Real-time analysis of your local records</p>
        </div>
      </header>

      <section className="overview-charts-section">
        <div className="section-header">
          <h2>Overview</h2>
        </div>
        <div className="overview-charts-grid">
          <div className="overview-chart-card">
            <div className="overview-chart-title">Income <span className="overview-chart-subtitle">Recent 6 Months</span></div>
            {overviewCharts.income
              ? <img src={overviewCharts.income} alt="Income" className="pin-image" />
              : overviewCharts.income === null
                ? <div className="overview-chart-loading">Loading...</div>
                : <div className="overview-chart-loading">No data available</div>}
            {overviewCharts.incomePie && (
              <>
                <div className="overview-chart-divider" />
                <div className="overview-chart-subtitle-row">By Source</div>
                <img src={overviewCharts.incomePie} alt="Income by Source" className="pin-image" />
              </>
            )}
          </div>
          <div className="overview-chart-card">
            <div className="overview-chart-title">Spending <span className="overview-chart-subtitle">Recent 6 Months</span></div>
            {overviewCharts.spending
              ? <img src={overviewCharts.spending} alt="Spending" className="pin-image" />
              : overviewCharts.spending === null
                ? <div className="overview-chart-loading">Loading...</div>
                : <div className="overview-chart-loading">No data available</div>}
            {overviewCharts.spendingPie && (
              <>
                <div className="overview-chart-divider" />
                <div className="overview-chart-subtitle-row">By Category</div>
                <img src={overviewCharts.spendingPie} alt="Spending by Category" className="pin-image" />
              </>
            )}
          </div>
        </div>
      </section>

      <section className="upcoming-section">
        <div className="section-header">
          <h2>Upcoming</h2>
        </div>
        <div className="upcoming-list">
          {upcomingEvents.length > 0 ? (
            upcomingEvents.map(event => (
              <div key={event.id} className={`upcoming-item ${event.type}`}>
                <div className="upcoming-date">{formatRelativeDate(event.date)}</div>
                <div className="upcoming-label">{event.label}</div>
                <div className={`upcoming-amount ${event.type}`}>
                  {event.type === 'income' ? '+' : '\u2212'}${fmt(Math.abs(event.amount))}
                </div>
              </div>
            ))
          ) : (
            <div className="upcoming-empty">No upcoming events predicted</div>
          )}
        </div>
      </section>

      <section>
        <div className="section-header">
          <h2>Today's Insights</h2>
        </div>
        <div className="insights-grid">
          {insights.map((insight) => (
            <div key={insight.id} className={`insight-card ${insight.type}`}>
              <div className="insight-content">
                <p>{insight.text}</p>
                <button className="insight-action" onClick={() => onDeepDive(`Deep dive: ${insight.text}`)}>
                  Deep Dive
                </button>
              </div>
            </div>
          ))}
        </div>

        {recentTopics.length > 0 && (
          <div className="recent-topics-section">
            <div className="recent-topics-label">You recently asked about:</div>
            <div className="recent-topics-chips">
              {recentTopics.map((topic, i) => (
                <button key={i} className="topic-chip" onClick={() => onDeepDive(topic)}>
                  {topic.length > 60 ? topic.slice(0, 60) + '…' : topic}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      <section>
        <div className="section-header">
          <h2>Key Metrics</h2>
        </div>
        <div className="metrics-grid">
          {metrics.map((m) => (
            <div key={m.label} className="metric-card">
              <div className="metric-label">{m.label}</div>
              <div className="metric-value">{m.value}</div>
              <button className="deep-dive-btn" onClick={() => onDeepDive(`Deep dive into my ${m.label}`)}>
                Deep Dive
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="pins-section" ref={pinsRef}>
        <div className="section-header">
          <h2>Pinned Insights</h2>
        </div>
        <div className="pins-grid">
          {pinnedDisplayData.length > 0 ? (
            pinnedDisplayData.map((pin) => (
              <div key={pin.id} className="pin-card">
                <div className="pin-header">
                  <span className="pin-title">{pin.title}</span>
                  <button className="unpin-btn" onClick={() => onUnpin?.(pin.id)}>✕</button>
                </div>
                <div className="pin-body">
                  <img src={pin.src} alt={pin.title} className="pin-image" />
                </div>
              </div>
            ))
          ) : (
            <div className="pin-card placeholder">
              <div className="pin-empty-state">
                <span>📌</span>
                <p>No charts pinned yet. Generate a chart in chat to see it here.</p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
})
