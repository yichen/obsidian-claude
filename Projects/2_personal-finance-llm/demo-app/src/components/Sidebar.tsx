import React from 'react'

interface SidebarProps {
  activeView: 'dashboard' | 'chat' | 'transactions'
  onViewChange: (view: 'dashboard' | 'chat' | 'transactions') => void
}

export function Sidebar({ activeView, onViewChange }: SidebarProps): React.ReactElement {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="app-logo">Y</div>
        <h2>Finance AI</h2>
      </div>
      
      <nav className="sidebar-nav">
        <button 
          className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
          onClick={() => onViewChange('dashboard')}
        >
          <span className="nav-icon">🏠</span>
          <span className="nav-label">Dashboard</span>
        </button>
        <button 
          className={`nav-item ${activeView === 'transactions' ? 'active' : ''}`}
          onClick={() => onViewChange('transactions')}
        >
          <span className="nav-icon">📋</span>
          <span className="nav-label">Transactions</span>
        </button>
        <button 
          className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
          onClick={() => onViewChange('chat')}
        >
          <span className="nav-icon">💬</span>
          <span className="nav-label">AI Chat</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="user-goal">
          <span className="goal-label">Active Goal</span>
          <span className="goal-value">Cashflow Positive</span>
        </div>
      </div>
    </div>
  )
}
