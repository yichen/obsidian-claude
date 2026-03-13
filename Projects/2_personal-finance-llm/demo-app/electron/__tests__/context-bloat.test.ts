import { describe, it, expect, vi } from 'vitest'
import { handleChat } from '../finance-core'
import {
  makeOpenAIMock,
  makeExecFileMock,
  makeEventSender,
  makeTestDeps
} from './electron-mock'

describe('handleChat: Context Bloat & Performance Regressions', () => {
  it('strips conversational filler from messages with tool calls', async () => {
    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        content: 'I will look that up for you right now...', // Filler text
        tool_calls: [
          {
            id: 'call_filler',
            function: {
              name: 'execute_sql',
              arguments: JSON.stringify({ sql: 'SELECT 1' })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Final answer.' }
    ])
    const execFile = makeExecFileMock([{ stdout: '[{"res":1}]', stderr: '' }])
    const deps = makeTestDeps({ openai, execFile })
    const sender = makeEventSender()

    await handleChat([{ role: 'user', content: 'query' }], sender, deps)

    const createFn = openai.chat.completions.create as ReturnType<typeof vi.fn>
    // Inspect the 2nd API call
    const secondCallMessages = createFn.mock.calls[1][0].messages
    const assistantMsg = secondCallMessages.find((m: any) => m.role === 'assistant' && m.tool_calls)
    
    // The filler text should be GONE (stripped to empty string)
    expect(assistantMsg.content).toBe('')
  })

  it('truncates massive SQL results to 4000 characters', async () => {
    // Generate a massive string (> 4000 chars)
    const massiveData = Array(500).fill({ note: 'this is a long string to bloat context' })
    const massiveJson = JSON.stringify(massiveData)
    expect(massiveJson.length).toBeGreaterThan(4000)

    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_massive',
            function: {
              name: 'execute_sql',
              arguments: JSON.stringify({ sql: 'SELECT *' })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Done.' }
    ])
    const execFile = makeExecFileMock([{ stdout: massiveJson, stderr: '' }])
    const deps = makeTestDeps({ openai, execFile })
    const sender = makeEventSender()

    await handleChat([{ role: 'user', content: 'massive query' }], sender, deps)

    const createFn = openai.chat.completions.create as ReturnType<typeof vi.fn>
    const secondCallMessages = createFn.mock.calls[1][0].messages
    const toolMsg = secondCallMessages.find((m: any) => m.role === 'tool')
    
    // Verify truncation occurred
    expect(toolMsg.content.length).toBeLessThanOrEqual(4000 + 50) // plus small buffer for the "[TRUNCATED]" tag
    expect(toolMsg.content).toContain('TRUNCATED')
  })

  it('truncates massive batch SQL results to 8000 characters', async () => {
    const massiveData = Array(1000).fill({ note: 'even longer string for batch bloat' })
    const massiveJson = JSON.stringify(massiveData)
    expect(massiveJson.length).toBeGreaterThan(8000)

    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_batch',
            function: {
              name: 'execute_batch_sql',
              arguments: JSON.stringify({ queries: ['SELECT 1', 'SELECT 2'] })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Batch done.' }
    ])
    // Two queries return massive data
    const execFile = makeExecFileMock([
      { stdout: massiveJson, stderr: '' },
      { stdout: massiveJson, stderr: '' }
    ])
    const deps = makeTestDeps({ openai, execFile })
    const sender = makeEventSender()

    await handleChat([{ role: 'user', content: 'batch query' }], sender, deps)

    const createFn = openai.chat.completions.create as ReturnType<typeof vi.fn>
    const secondCallMessages = createFn.mock.calls[1][0].messages
    const toolMsg = secondCallMessages.find((m: any) => m.role === 'tool')
    
    expect(toolMsg.content.length).toBeLessThanOrEqual(8000 + 50)
    expect(toolMsg.content).toContain('TRUNCATED')
  })

  it('prunes history to the last 10 messages', async () => {
    // Create 15 messages: chat 0 to chat 14
    const manyMessages = Array.from({ length: 15 }, (_, i) => ({ 
      role: 'user' as const, 
      content: `chat ${i}` 
    }))
    
    const openai = makeOpenAIMock([
      { finish_reason: 'stop', content: 'Response' }
    ])
    const deps = makeTestDeps({ openai })
    const sender = makeEventSender()

    await handleChat(manyMessages, sender, deps)

    const createFn = openai.chat.completions.create as ReturnType<typeof vi.fn>
    const sentMessages = createFn.mock.calls[0][0].messages
    
    // 1 system message + 10 history items + 1 assistant response (pushed to same array ref) = 12
    expect(sentMessages).toHaveLength(12)
    expect(sentMessages[0].role).toBe('system')
    expect(sentMessages[1].content).toBe('chat 5')
    expect(sentMessages[10].content).toBe('chat 14')
    expect(sentMessages[11].role).toBe('assistant')
  })
})
