import React, { useState, useRef, useEffect, useCallback } from 'react'
import { MessageBubble } from './MessageBubble'
import { Message, ToolResult } from '../lib/types'

const SUGGESTIONS = [
  'Show me a spending dashboard',
  'How much did I spend on kids last 3 months?',
  'What are my top spending categories this year?',
  'Show monthly cash flow for 2025',
  'What did I spend on dining vs groceries?',
  'Generate a chart of monthly spending by category'
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
      ) => Promise<{ text: string; chartPath?: string; chartData?: string }>
      onToolResult: (cb: (data: ToolResult) => void) => () => void
      dbQuery: (sql: string) => Promise<unknown>
      financeCommand: (command: string) => Promise<string>
    }
  }
}

export function ChatInterface(): React.ReactElement {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: nextId(),
      role: 'assistant',
      content:
        "Hi! I'm your personal finance AI. I have access to your transactions, payslips, Amazon orders, and tax documents. What would you like to know?"
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return
      setInput('')
      setIsLoading(true)

      const userMsg: Message = { id: nextId(), role: 'user', content: text }
      const loadingId = nextId()
      const loadingMsg: Message = { id: loadingId, role: 'assistant', content: '', isLoading: true }

      setMessages((prev) => [...prev, userMsg, loadingMsg])

      // Collect the history for the API (exclude tool messages and loading)
      const history = [...messages, userMsg]
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .filter((m) => !m.isLoading && m.content !== '')
        .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))

      // Listen for live tool-call progress updates
      const cleanupTool = window.api.onToolResult((data) => {
        const label =
          data.tool === 'execute_sql'
            ? `Running SQL: ${String(data.sql ?? '').substring(0, 60)}…`
            : data.tool === 'run_finance_command'
              ? `Running: ${data.command}`
              : `Generating chart…`
        setMessages((prev) => [...prev, { id: nextId(), role: 'tool', content: label }])
      })

      try {
        // Final response comes back as the resolved Promise value — no race condition
        const result = await window.api.sendChat(history)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingId
              ? { ...m, isLoading: false, content: result.text, chartPath: result.chartPath, chartData: result.chartData }
              : m
          )
        )
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === loadingId
              ? { ...m, isLoading: false, content: `Error: ${String(err)}` }
              : m
          )
        )
      } finally {
        cleanupTool()
        setIsLoading(false)
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

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
    setInput(e.target.value)
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Finance AI</h1>
        <span className="model-badge">claude-sonnet via OpenRouter</span>
      </div>

      <div className="messages-area">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="suggestion-chip" onClick={() => sendMessage(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="input-area">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your finances… (Enter to send, Shift+Enter for new line)"
          disabled={isLoading}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={() => sendMessage(input)}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '⏳' : '↑'}
        </button>
      </div>
    </div>
  )
}
