import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Message, PinnedChart } from '../lib/types'
import { Pin, Bot, User } from 'lucide-react'

interface Props {
  message: Message
  onPinChart?: (chart: Omit<PinnedChart, 'id' | 'timestamp'>) => void
}

export function MessageBubble({ message, onPinChart }: Props): React.ReactElement {
  if (message.role === 'tool') return <></>

  const isAssistant = message.role === 'assistant'

  return (
    <div className={`message-row ${message.role}`}>
      <div className="message-meta">
        <div className="avatar-wrapper">
          {isAssistant ? <Bot size={14} strokeWidth={2.5} /> : <User size={14} strokeWidth={2.5} />}
        </div>
        <span className="author-name">{isAssistant ? 'Finance AI' : 'You'}</span>
      </div>
      
      <div className="message-content-wrapper">
        <div className="markdown-container">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table({ children }) {
                return <div className="table-container"><table>{children}</table></div>
              },
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                const inline = !match
                return inline ? (
                  <code className="inline-code" {...props}>{children}</code>
                ) : (
                  <div className="code-block-wrapper">
                    <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div">
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                )
              }
            }}
          >
            {message.content}
          </ReactMarkdown>

          {message.chartData && (
            <div className="chat-chart-card">
              <img src={message.chartData} alt="Analysis" className="chart-image" />
              {onPinChart && (
                <button 
                  onClick={() => onPinChart({ 
                    title: message.content.split('\n')[0].substring(0, 40) || 'Financial Chart', 
                    chartData: message.chartData!, 
                    chartPath: message.chartPath 
                  })}
                  className="pin-action-btn"
                >
                  <Pin size={12} strokeWidth={3} /> Pin to Dashboard
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
