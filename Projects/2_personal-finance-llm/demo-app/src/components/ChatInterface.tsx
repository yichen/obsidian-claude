import React, { useState, useRef, useEffect, useCallback } from 'react'
import { MessageBubble } from './MessageBubble'
import { Message, ToolResult, PinnedChart } from '../lib/types'
import { Send, Eraser, Sparkles, PieChart, Baby, Tag, LineChart, Loader2 } from 'lucide-react'

const SUGGESTIONS = [
  { label: 'Spending Dashboard', icon: <PieChart size={18} style={{ color: '#3b82f6' }} />, prompt: 'Show me a spending dashboard' },
  { label: 'Kids Spending', icon: <Baby size={18} style={{ color: '#f43f5e' }} />, prompt: 'How much did I spend on kids last 3 months?' },
  { label: 'Top Categories', icon: <Tag size={18} style={{ color: '#f59e0b' }} />, prompt: 'What are my top spending categories this year?' },
  { label: 'Monthly Cashflow', icon: <LineChart size={18} style={{ color: '#10b981' }} />, prompt: 'Show monthly cash flow for 2025' }
]

let msgCounter = 0
function nextId(): string {
  return String(++msgCounter)
}

declare global {
  interface Window {
    api: {
      sendChat: (
        messages: { role: string; content: string }[]
      ) => Promise<{ text: string; charts?: Array<{ path: string; data: string }> }>
      onToolResult: (cb: (data: ToolResult) => void) => () => void
      onStreamToken: (cb: (data: { token: string }) => void) => () => void
      dbQuery: (sql: string) => Promise<unknown>
      financeCommand: (command: string) => Promise<string>
    }
  }
}

interface ChatInterfaceProps {
  initialMessage?: string
  onClearInitial?: () => void
  persistedMessages?: Message[]
  onMessagesChange?: (messages: Message[]) => void
  onPinChart?: (chart: Omit<PinnedChart, 'id' | 'timestamp'>) => void
}

export function ChatInterface({ 
  initialMessage, 
  onClearInitial, 
  persistedMessages, 
  onMessagesChange,
  onPinChart
}: ChatInterfaceProps): React.ReactElement {
  const [messages, setMessages] = useState<Message[]>(persistedMessages?.length ? persistedMessages : [
    {
      id: nextId(),
      role: 'assistant',
      content: "Hi! I'm your personal finance AI. I've analyzed your local transactions and records. How can I help you optimize your finances today?"
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeTool, setActiveTool] = useState<string | null>(null)
  
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const sentInitialRef = useRef<string | null>(null)

  useEffect(() => {
    onMessagesChange?.(messages)
  }, [messages, onMessagesChange])

  useEffect(() => {
    if (!initialMessage) {
      sentInitialRef.current = null
      return
    }
    if (!isLoading && sentInitialRef.current !== initialMessage) {
      const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
      if (lastUserMsg?.content !== initialMessage) {
        sentInitialRef.current = initialMessage
        sendMessage(initialMessage)
      }
      onClearInitial?.()
    }
  }, [initialMessage, messages, isLoading])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeTool])

  const clearSession = () => {
    if (isLoading) return
    setMessages([{
      id: nextId(),
      role: 'assistant',
      content: "Workspace reset. What's on your mind?"
    }])
  }

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return
      setInput('')
      setIsLoading(true)
      setActiveTool(null)

      const userMsg: Message = { id: nextId(), role: 'user', content: text }
      const loadingId = nextId()
      const loadingMsg: Message = { id: loadingId, role: 'assistant', content: '', isLoading: true }

      setMessages((prev) => [...prev, userMsg, loadingMsg])

      const history = [...messages, userMsg]
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .filter((m) => !m.isLoading && m.content !== '')
        .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))

      const cleanupTool = window.api.onToolResult((data) => {
        const label = data.tool === 'execute_sql' ? 'Analyzing database...' :
                     data.tool === 'run_finance_command' ? `Executing ${data.command}...` :
                     'Visualizing data...'
        setActiveTool(label)
      })

      let streamedText = ''
      const cleanupStream = window.api.onStreamToken(({ token }) => {
        streamedText += token
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingId ? { ...m, content: streamedText } : m
          )
        )
      })

      try {
        const result = await window.api.sendChat(history)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingId
              ? { ...m, isLoading: false, content: result.text, charts: result.charts }
              : m
          )
        )
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingId ? { ...m, isLoading: false, content: `System Error: ${String(err)}` } : m
          )
        )
      } finally {
        cleanupTool()
        cleanupStream()
        setIsLoading(false)
        setActiveTool(null)
      }
    },
    [messages, isLoading]
  )

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="chat-header-left">
          <span className="chat-header-icon"><Sparkles size={16} /></span>
          <h1>Financial Analyst</h1>
        </div>
        <button
          onClick={clearSession}
          disabled={isLoading}
          className="new-session-btn"
        >
          <Eraser size={14} /> Reset Session
        </button>
      </header>

      <div className="messages-area">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} onPinChart={onPinChart} />
        ))}
        {activeTool && (
          <div className="thinking-indicator">
            <span className="spinner-dot" />
            <span className="thinking-text">{activeTool}</span>
          </div>
        )}
        <div ref={bottomRef} style={{ height: '16px' }} />
      </div>

      {messages.length === 1 && (
        <div className="suggestions-grid">
          {SUGGESTIONS.map((s) => (
            <button key={s.prompt} className="suggestion-card" onClick={() => sendMessage(s.prompt)}>
              <span className="suggestion-icon">{s.icon}</span>
              <span className="suggestion-label">{s.label}</span>
            </button>
          ))}
        </div>
      )}

      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your finances or search records..."
            disabled={isLoading}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? <Loader2 size={18} className="loader-spin" /> : <Send size={18} />}
          </button>
        </div>
      </div>
    </div>
  )
}
