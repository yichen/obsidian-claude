import React, { useState, useEffect } from 'react'
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

function fmt(n: number, prefix = '', suffix = ''): string {
  return `${prefix}${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}${suffix}`
}

export function Dashboard({ onDeepDive, pinnedCharts, onUnpin }: DashboardProps): React.ReactElement {
  const [metrics, setMetrics] = useState<Metric[]>([
    { label: 'Savings Rate', value: '—' },
    { label: 'Financial Runway', value: '—' },
    { label: 'Net Cashflow', value: '—' }
  ])

  const [insights] = useState<Insight[]>([
    { id: '1', type: 'success', text: "You're saving more than your 3-month average. Great momentum!" },
    { id: '2', type: 'alert', text: "Open AI Chat to get personalized insights from your transaction history." }
  ])

  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        const [spendRes, incomeRes, cmaRes, avgRes] = await Promise.all([
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
      } catch (err) {
        console.error('[Dashboard] Failed to load metrics:', err)
      }
    }
    load()
  }, [])

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Financial Overview</h1>
        <p className="subtitle">Real-time analysis of your local records</p>
      </header>

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

      <section className="pins-section">
        <div className="section-header">
          <h2>Pinned Insights</h2>
        </div>
        <div className="pins-grid">
          {pinnedCharts && pinnedCharts.length > 0 ? (
            pinnedCharts.map((pin) => (
              <div key={pin.id} className="pin-card">
                <div className="pin-header">
                  <span className="pin-title">{pin.title}</span>
                  <button className="unpin-btn" onClick={() => onUnpin?.(pin.id)}>✕</button>
                </div>
                <div className="pin-body">
                  <img src={pin.chartData} alt={pin.title} className="pin-image" />
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
}
