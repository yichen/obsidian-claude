import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { FinanceDeps, EventSender } from './finance-core'

// ── Helpers ─────────────────────────────────────────────────────────────────

/** Build an async-iterable that yields chunks like the OpenAI streaming API */
function makeStream(chunks: object[]) {
  return {
    [Symbol.asyncIterator]: async function* () {
      for (const chunk of chunks) {
        yield chunk
      }
    }
  }
}

function makeMockDeps(openaiCreate: ReturnType<typeof vi.fn>): FinanceDeps {
  return {
    execFile: vi.fn().mockResolvedValue({ stdout: '[]', stderr: '' }),
    openai: {
      chat: { completions: { create: openaiCreate } }
    } as unknown as FinanceDeps['openai'],
    fs: {
      existsSync: vi.fn().mockReturnValue(false),
      readFileSync: vi.fn().mockReturnValue(''),
      writeFileSync: vi.fn(),
      mkdirSync: vi.fn(),
      unlinkSync: vi.fn()
    },
    vaultPath: '/test/vault',
    pythonBin: '/test/python',
    financeScript: '/test/finance.py'
  }
}

function makeSender(): EventSender & { calls: unknown[] } {
  const calls: unknown[] = []
  return { send: (ch: string, d: unknown) => calls.push({ ch, d }), calls }
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('handleChat — streaming response', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('returns non-empty text when LLM streams a direct text response', async () => {
    const { handleChat } = await import('./finance-core')

    const stream = makeStream([
      { choices: [{ delta: { role: 'assistant', content: '' }, finish_reason: null }] },
      { choices: [{ delta: { content: 'You spent ' }, finish_reason: null }] },
      { choices: [{ delta: { content: '$500 on kids.' }, finish_reason: null }] },
      { choices: [{ delta: {}, finish_reason: 'stop' }] }
    ])

    const create = vi.fn().mockResolvedValue(stream)
    const deps = makeMockDeps(create)
    const sender = makeSender()

    const result = await handleChat(
      [{ role: 'user', content: 'How much did I spend on groceries?' }],
      sender,
      deps
    )

    expect(result.text).toContain('You spent $500 on kids.')
  })

  it('emits chat:stream-token events as tokens arrive', async () => {
    const { handleChat } = await import('./finance-core')

    const stream = makeStream([
      { choices: [{ delta: { content: 'Hello ' }, finish_reason: null }] },
      { choices: [{ delta: { content: 'world.' }, finish_reason: null }] },
      { choices: [{ delta: {}, finish_reason: 'stop' }] }
    ])

    const create = vi.fn().mockResolvedValue(stream)
    const deps = makeMockDeps(create)
    const sender = makeSender()

    await handleChat([{ role: 'user', content: 'Hi' }], sender, deps)

    const tokenEvents = sender.calls.filter((c: any) => c.ch === 'chat:stream-token')
    expect(tokenEvents.length).toBe(2)
    expect((tokenEvents[0] as any).d.token).toBe('Hello ')
    expect((tokenEvents[1] as any).d.token).toBe('world.')
  })

  it('processes one tool call round then returns final text', async () => {
    const { handleChat } = await import('./finance-core')

    const toolStream = makeStream([
      {
        choices: [{
          delta: {
            tool_calls: [{ index: 0, id: 'tc_1', type: 'function', function: { name: 'execute_sql', arguments: '' } }]
          },
          finish_reason: null
        }]
      },
      {
        choices: [{
          delta: { tool_calls: [{ index: 0, function: { arguments: '{"sql":"SELECT 1"}' } }] },
          finish_reason: null
        }]
      },
      { choices: [{ delta: {}, finish_reason: 'tool_calls' }] }
    ])

    const finalStream = makeStream([
      { choices: [{ delta: { content: 'Total: $42.' }, finish_reason: null }] },
      { choices: [{ delta: {}, finish_reason: 'stop' }] }
    ])

    // execFile returns JSON for the SQL query
    const execFile = vi.fn().mockResolvedValue({ stdout: JSON.stringify([{ total: 42 }]), stderr: '' })
    const create = vi.fn()
      .mockResolvedValueOnce(toolStream)
      .mockResolvedValueOnce(finalStream)

    const deps = makeMockDeps(create)
    deps.execFile = execFile as FinanceDeps['execFile']
    const sender = makeSender()

    const result = await handleChat([{ role: 'user', content: 'What is my total?' }], sender, deps)

    expect(create).toHaveBeenCalledTimes(2)
    expect(result.text).toContain('Total: $42.')
  })

  it('strips conversational filler when tool calls are present', async () => {
    const { handleChat } = await import('./finance-core')

    const toolStream = makeStream([
      // Content appears alongside tool calls — should be stripped
      { choices: [{ delta: { content: 'Let me look that up...' }, finish_reason: null }] },
      {
        choices: [{
          delta: {
            tool_calls: [{ index: 0, id: 'tc_1', type: 'function', function: { name: 'execute_sql', arguments: '{"sql":"SELECT 1"}' } }]
          },
          finish_reason: null
        }]
      },
      { choices: [{ delta: {}, finish_reason: 'tool_calls' }] }
    ])

    const finalStream = makeStream([
      { choices: [{ delta: { content: 'The answer is 5.' }, finish_reason: null }] },
      { choices: [{ delta: {}, finish_reason: 'stop' }] }
    ])

    const execFile = vi.fn().mockResolvedValue({ stdout: JSON.stringify([{ v: 5 }]), stderr: '' })
    const create = vi.fn()
      .mockResolvedValueOnce(toolStream)
      .mockResolvedValueOnce(finalStream)

    const deps = makeMockDeps(create)
    deps.execFile = execFile as FinanceDeps['execFile']
    const sender = makeSender()

    const result = await handleChat([{ role: 'user', content: 'What is 5?' }], sender, deps)

    // Final text should NOT contain the filler
    expect(result.text).not.toContain('Let me look that up')
    expect(result.text).toContain('The answer is 5.')
  })
})

describe('handleChat — local context injection conversation structure', () => {
  it('places local context BEFORE the last user message, not after', async () => {
    const { handleChat } = await import('./finance-core')

    let capturedMessages: unknown[] = []
    const stream = makeStream([
      { choices: [{ delta: { content: 'Answer.' }, finish_reason: null }] },
      { choices: [{ delta: {}, finish_reason: 'stop' }] }
    ])
    const create = vi.fn().mockImplementation((params: { messages: unknown[] }) => {
      capturedMessages = params.messages
      return Promise.resolve(stream)
    })

    // Use a message that triggers the router (contains 'spending')
    const execFile = vi.fn().mockResolvedValue({ stdout: '[]', stderr: '' })
    const create2 = vi.fn().mockImplementation((params: any) => {
      capturedMessages = [...params.messages] // snapshot before push(msg) mutates the array
      return Promise.resolve(makeStream([
        { choices: [{ delta: { content: 'Done.' }, finish_reason: null }] },
        { choices: [{ delta: {}, finish_reason: 'stop' }] }
      ]))
    })
    const deps = makeMockDeps(create2)
    deps.execFile = execFile as FinanceDeps['execFile']
    const sender = makeSender()

    await handleChat(
      [{ role: 'user', content: 'What is my spending?' }],
      sender,
      deps
    )

    // The LAST message sent to the API must always be from 'user' (not 'assistant')
    const lastMsg = capturedMessages[capturedMessages.length - 1] as { role: string }
    expect(lastMsg.role).toBe('user')
  })
})

describe('initCategoryContext', () => {
  it('builds DISTINCT comma-separated category list', async () => {
    vi.resetModules()
    const { initCategoryContext } = await import('./finance-core')

    // execFile returns duplicate category names (parent + child rows)
    const execFile = vi.fn().mockResolvedValue({
      stdout: JSON.stringify([
        { name: 'Food & Drink' },
        { name: 'Food & Drink' }, // duplicate — should be deduplicated by DISTINCT
        { name: 'Travel' },
        { name: 'Kids & Family' }
      ]),
      stderr: ''
    })
    const deps = makeMockDeps(vi.fn())
    deps.execFile = execFile as FinanceDeps['execFile']

    await initCategoryContext(deps)

    // Verify the SQL query used DISTINCT (no duplicates in result)
    const sql = (execFile.mock.calls[0][1] as string[])[2]
    expect(sql).toContain('DISTINCT')
  })
})

describe('generateLocalSummary — cache behavior', () => {
  it('returns cached summary on second call without running SQL', async () => {
    vi.resetModules()
    const { initFinanceCache, handleChat } = await import('./finance-core')

    // buildSummary runs 4 SQL queries; track call count
    let sqlCallCount = 0
    const execFile = vi.fn().mockImplementation(() => {
      sqlCallCount++
      return Promise.resolve({ stdout: '[]', stderr: '' })
    })

    const create = vi.fn().mockResolvedValue(makeStream([
      { choices: [{ delta: { content: 'ok' }, finish_reason: null }] },
      { choices: [{ delta: {}, finish_reason: 'stop' }] }
    ]))
    const deps = makeMockDeps(create)
    deps.execFile = execFile as FinanceDeps['execFile']

    // Warm the cache
    await initFinanceCache(deps)
    const callsAfterWarm = sqlCallCount

    // Trigger handleChat with a 'spending' keyword to invoke router + generateLocalSummary
    sqlCallCount = 0 // reset counter
    const sender = makeSender()
    await handleChat([{ role: 'user', content: 'spending' }], sender, deps)

    // generateLocalSummary should have hit the cache (0 SQL calls for summary)
    // (the API call itself runs but no summary SQL queries)
    expect(sqlCallCount).toBe(0)
  })
})
