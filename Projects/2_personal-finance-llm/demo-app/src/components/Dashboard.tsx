import React, { useState } from 'react'
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

export function Dashboard({ onDeepDive, pinnedCharts, onUnpin }: DashboardProps): React.ReactElement {
  const [metrics] = useState<Metric[]>([
    { label: 'Savings Rate', value: '32.4%' },
    { label: 'Financial Runway', value: '18.5 mo' },
    { label: 'Net Cashflow', value: '+$2,450' }
  ])

  const [insights] = useState<Insight[]>([
    { id: '1', type: 'success', text: "You're saving 12% more this week than your average. Great momentum!" },
    { id: '2', type: 'alert', text: "Unusual $150 charge detected at 'Home Depot'—is this expected?" }
  ])

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
