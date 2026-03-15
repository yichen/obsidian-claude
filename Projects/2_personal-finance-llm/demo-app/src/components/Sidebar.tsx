import React, { useState, useEffect, useRef } from 'react'

interface SidebarProps {
  activeView: 'dashboard' | 'chat' | 'transactions'
  onViewChange: (view: 'dashboard' | 'chat' | 'transactions') => void
}

const DEFAULT_PROFILE = { name: 'Yi Chen', email: 'yichen@gmail.com' }

function getUserProfile() {
  try {
    const stored = localStorage.getItem('finance_user_profile')
    if (stored) return { ...DEFAULT_PROFILE, ...JSON.parse(stored) }
  } catch {}
  return DEFAULT_PROFILE
}

export function Sidebar({ activeView, onViewChange }: SidebarProps): React.ReactElement {
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const popoverRef = useRef<HTMLDivElement>(null)
  const profile = getUserProfile()
  const initials = profile.name.split(' ').map((n: string) => n[0]).join('').toUpperCase()

  useEffect(() => {
    if (!showProfileMenu) return
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false)
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setShowProfileMenu(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [showProfileMenu])

  return (
    <div className="sidebar">
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

      <div className="sidebar-footer" ref={popoverRef}>
        {showProfileMenu && (
          <div className="profile-popover">
            <div className="profile-popover-email">{profile.email}</div>
            <div className="profile-popover-divider" />
            <button className="profile-popover-item" onClick={() => setShowProfileMenu(false)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <span>Settings</span>
            </button>
            <button className="profile-popover-item" onClick={() => setShowProfileMenu(false)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>About</span>
            </button>
          </div>
        )}
        <button className="sidebar-profile-btn" onClick={() => setShowProfileMenu(prev => !prev)}>
          <div className="profile-avatar">{initials}</div>
          <div className="profile-info">
            <span className="profile-name">{profile.name}</span>
            <span className="profile-email">{profile.email}</span>
          </div>
        </button>
      </div>
    </div>
  )
}
