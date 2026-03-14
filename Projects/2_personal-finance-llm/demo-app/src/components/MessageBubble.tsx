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
  pinnedCharts?: PinnedChart[]
}

export function MessageBubble({ message, onPinChart, pinnedCharts }: Props): React.ReactElement {
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

          {message.charts?.map((c, i) => {
            const isPinned = pinnedCharts?.some(p =>
              (c.type && p.chartType === c.type && p.chartMonths === (c.months ?? 6)) ||
              p.chartData === c.data
            ) ?? false
            return (
              <div key={i} className="chat-chart-card">
                <img src={c.data} alt="Chart" className="chart-image" />
                {onPinChart && (
                  <button
                    onClick={() => !isPinned && onPinChart({
                      title: message.content.split('\n')[0].substring(0, 40) || 'Financial Chart',
                      chartData: c.data,
                      chartPath: c.path,
                      chartType: c.type,
                      chartMonths: c.months ?? 6
                    })}
                    className={`pin-action-btn ${isPinned ? 'pin-action-btn--pinned' : ''}`}
                    disabled={isPinned}
                  >
                    <Pin size={12} strokeWidth={3} /> {isPinned ? '\u2713 In Dashboard' : 'Pin to Dashboard'}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
