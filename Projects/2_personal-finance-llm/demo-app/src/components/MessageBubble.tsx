import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Message } from '../lib/types'

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props): React.ReactElement {
  if (message.role === 'tool') {
    return (
      <div className="tool-call">
        <span className="tool-icon">⚙</span>
        <span className="tool-label">{message.content}</span>
      </div>
    )
  }

  if (message.isLoading) {
    return (
      <div className="message assistant">
        <div className="avatar">AI</div>
        <div className="bubble loading">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>
      </div>
    )
  }

  return (
    <div className={`message ${message.role}`}>
      {message.role === 'assistant' && <div className="avatar">AI</div>}
      <div className="bubble">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '')
              const inline = !match
              return inline ? (
                <code className={className} {...props}>
                  {children}
                </code>
              ) : (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              )
            }
          }}
        >
          {message.content}
        </ReactMarkdown>
        {message.chartData && (
          <div className="chart-container">
            <img
              src={message.chartData}
              alt="Finance chart"
              className="chart-image"
            />
          </div>
        )}
      </div>
      {message.role === 'user' && <div className="avatar user-avatar">Yi</div>}
    </div>
  )
}
