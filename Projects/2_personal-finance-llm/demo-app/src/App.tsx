import React, { useState, useEffect, useCallback } from 'react'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './components/Dashboard'
import { ChatInterface } from './components/ChatInterface'
import { TransactionsView } from './components/TransactionsView'
import { Message, PinnedChart } from './lib/types'
import './styles.css'

export default function App(): React.ReactElement {
  const [activeView, setActiveView] = useState<'dashboard' | 'chat' | 'transactions'>('dashboard')
  const [initialChatMessage, setInitialChatMessage] = useState<string | undefined>()
  const [prefetchedTransactions, setPrefetchedTransactions] = useState<unknown[][] | undefined>()
  const [chatHistory, setChatHistory] = useState<Message[]>([])
  const [pinnedCharts, setPinnedCharts] = useState<PinnedChart[]>([])

  // Load pins from localStorage on startup
  useEffect(() => {
    const saved = localStorage.getItem('finance_pins')
    if (saved) {
      try {
        setPinnedCharts(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to load pins:', e)
      }
    }
  }, [])

  // Save pins whenever they change
  useEffect(() => {
    localStorage.setItem('finance_pins', JSON.stringify(pinnedCharts))
  }, [pinnedCharts])

  const handlePinChart = useCallback((chart: Omit<PinnedChart, 'id' | 'timestamp'>) => {
    const newPin: PinnedChart = {
      ...chart,
      id: Math.random().toString(36).substring(7),
      timestamp: Date.now()
    }
    setPinnedCharts(prev => [...prev, newPin])
  }, [])

  const handleUnpinChart = useCallback((id: string) => {
    setPinnedCharts(prev => prev.filter(p => p.id !== id))
  }, [])

  // Pre-fetch transactions in the background
  useEffect(() => {
    const prefetch = async () => {
      try {
        // Add a small delay to ensure window.api is injected
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        const sql = `
          SELECT t.date, t.description, COALESCE(c.name, 'Uncategorized') as category, a.name as account, t.amount
          FROM transactions t
          LEFT JOIN categories c ON c.id = t.category_id
          JOIN accounts a ON a.id = t.account_id
          WHERE t.is_transfer = 0 
          ORDER BY t.date DESC
          LIMIT 100
        `
        const result = await window.api.dbQuery(sql) as { rows?: unknown[][] }
        if (result.rows) {
          setPrefetchedTransactions(result.rows)
        }
      } catch (e) {
        console.warn('Prefetch failed:', e)
      }
    }
    prefetch()
  }, [])

  const handleDeepDive = (topic: string) => {
    setInitialChatMessage(topic)
    setActiveView('chat')
  }

  return (
    <div className="app-layout">
      <div className="window-drag-bar" />
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      <main className="main-content">
        {activeView === 'dashboard' && (
          <Dashboard 
            onDeepDive={handleDeepDive} 
            pinnedCharts={pinnedCharts} 
            onUnpin={handleUnpinChart}
          />
        )}
        {activeView === 'transactions' && <TransactionsView initialData={prefetchedTransactions} />}
        {activeView === 'chat' && (
          <ChatInterface 
            initialMessage={initialChatMessage} 
            onClearInitial={() => setInitialChatMessage(undefined)}
            persistedMessages={chatHistory}
            onMessagesChange={setChatHistory}
            onPinChart={handlePinChart}
          />
        )}
      </main>
    </div>
  )
}
