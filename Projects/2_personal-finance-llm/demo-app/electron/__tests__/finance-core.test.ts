import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  loadEnv,
  runFinanceCommand,
  queryDB,
  handleChat
} from '../finance-core'
import {
  makeOpenAIMock,
  makeExecFileMock,
  makeFsMock,
  makeEventSender,
  makeTestDeps
} from './electron-mock'

// ── loadEnv ──────────────────────────────────────────────────────────────

describe('loadEnv', () => {
  beforeEach(() => {
    // Clean up env vars set by loadEnv
    delete process.env.TEST_KEY
    delete process.env.ANOTHER_KEY
    delete process.env.OPENROUTER_API_KEY
  })

  it('parses simple KEY=VALUE', () => {
    const fsImpl = {
      existsSync: () => true,
      readFileSync: () => 'TEST_KEY=hello\nANOTHER_KEY=world'
    }
    loadEnv('/fake/.env', fsImpl as any)
    expect(process.env.TEST_KEY).toBe('hello')
    expect(process.env.ANOTHER_KEY).toBe('world')
  })

  it('strips trailing whitespace from values', () => {
    const fsImpl = {
      existsSync: () => true,
      readFileSync: () => 'TEST_KEY=hello   \n'
    }
    loadEnv('/fake/.env', fsImpl as any)
    expect(process.env.TEST_KEY).toBe('hello')
  })

  it('ignores lines starting with #', () => {
    const fsImpl = {
      existsSync: () => true,
      readFileSync: () => '# comment\nTEST_KEY=value'
    }
    loadEnv('/fake/.env', fsImpl as any)
    expect(process.env.TEST_KEY).toBe('value')
  })

  it('ignores blank lines', () => {
    const fsImpl = {
      existsSync: () => true,
      readFileSync: () => '\n\nTEST_KEY=value\n\n'
    }
    loadEnv('/fake/.env', fsImpl as any)
    expect(process.env.TEST_KEY).toBe('value')
  })

  it('does not crash if file does not exist', () => {
    const fsImpl = {
      existsSync: () => false,
      readFileSync: () => {
        throw new Error('should not be called')
      }
    }
    expect(() => loadEnv('/fake/.env', fsImpl as any)).not.toThrow()
  })
})

// ── runFinanceCommand ────────────────────────────────────────────────────

describe('runFinanceCommand', () => {
  it('calls execFile with [pythonBin, financeScript, subcommand, ...args]', async () => {
    const execFile = makeExecFileMock([{ stdout: 'ok', stderr: '' }])
    const deps = makeTestDeps({ execFile })
    await runFinanceCommand('dashboard', [], deps)
    expect(execFile).toHaveBeenCalledWith(
      deps.pythonBin,
      [deps.financeScript, 'dashboard'],
      { cwd: deps.vaultPath, timeout: 30000 }
    )
  })

  it('returns stdout when populated', async () => {
    const deps = makeTestDeps({
      execFile: makeExecFileMock([{ stdout: 'output here', stderr: '' }])
    })
    const result = await runFinanceCommand('status', [], deps)
    expect(result).toBe('output here')
  })

  it('returns stderr when stdout is empty', async () => {
    const deps = makeTestDeps({
      execFile: makeExecFileMock([{ stdout: '', stderr: 'error output' }])
    })
    const result = await runFinanceCommand('status', [], deps)
    expect(result).toBe('error output')
  })

  it('returns error string when execFile throws', async () => {
    const execFile = vi.fn().mockRejectedValue(new Error('exit code 1'))
    const deps = makeTestDeps({ execFile: execFile as any })
    const result = await runFinanceCommand('bad', [], deps)
    expect(result).toBe('exit code 1')
  })

  it('passes SQL with spaces and newlines as single unbroken argument (regression)', async () => {
    const execFile = makeExecFileMock([{ stdout: '[]', stderr: '' }])
    const deps = makeTestDeps({ execFile })
    const sql = 'SELECT * FROM transactions WHERE date >= "2024-01-01" ORDER BY date'
    await runFinanceCommand('query', [sql], deps)
    // The SQL must be a single argument, not split on whitespace
    expect(execFile).toHaveBeenCalledWith(
      deps.pythonBin,
      [deps.financeScript, 'query', sql],
      expect.any(Object)
    )
  })
})

// ── queryDB ──────────────────────────────────────────────────────────────

describe('queryDB', () => {
  it('parses JSON array response into {columns, rows}', async () => {
    const data = [
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' }
    ]
    const deps = makeTestDeps({
      execFile: makeExecFileMock([{ stdout: JSON.stringify(data), stderr: '' }])
    })
    const result = await queryDB('SELECT * FROM users', deps)
    expect(result).toEqual({
      columns: ['id', 'name'],
      rows: [
        [1, 'Alice'],
        [2, 'Bob']
      ]
    })
  })

  it('returns {columns:[], rows:[]} for empty array', async () => {
    const deps = makeTestDeps({
      execFile: makeExecFileMock([{ stdout: '[]', stderr: '' }])
    })
    const result = await queryDB('SELECT * FROM empty', deps)
    expect(result).toEqual({ columns: [], rows: [] })
  })

  it('returns {error} when JSON contains {error: "..."}', async () => {
    const deps = makeTestDeps({
      execFile: makeExecFileMock([{ stdout: '{"error":"bad query"}', stderr: '' }])
    })
    const result = await queryDB('BAD SQL', deps)
    expect(result).toEqual({ error: 'bad query' })
  })

  it('returns {error} when runFinanceCommand throws', async () => {
    const execFile = vi.fn().mockRejectedValue(new Error('boom'))
    const deps = makeTestDeps({ execFile: execFile as any })
    // runFinanceCommand catches and returns the error string, but JSON.parse will fail
    const result = await queryDB('SELECT 1', deps)
    expect(result).toHaveProperty('error')
  })

  it('passes the raw SQL string as a single arg (not split on whitespace)', async () => {
    const execFile = makeExecFileMock([{ stdout: '[]', stderr: '' }])
    const deps = makeTestDeps({ execFile })
    const sql = 'SELECT COUNT(*) FROM transactions WHERE amount > 100'
    await queryDB(sql, deps)
    // queryDB calls runFinanceCommand('query', [sql], deps)
    // which calls execFile(pythonBin, [financeScript, 'query', sql], ...)
    expect(execFile).toHaveBeenCalledWith(
      deps.pythonBin,
      [deps.financeScript, 'query', sql],
      expect.any(Object)
    )
  })
})

// ── handleChat ───────────────────────────────────────────────────────────

describe('handleChat', () => {
  it('single turn, finish_reason=stop: returns {text, charts:undefined}', async () => {
    const openai = makeOpenAIMock([
      { finish_reason: 'stop', content: 'Hello there!' }
    ])
    const deps = makeTestDeps({ openai })
    const sender = makeEventSender()
    const result = await handleChat(
      [{ role: 'user', content: 'hi' }],
      sender,
      deps
    )
    expect(result.text).toContain('Hello there!')
    expect(result.charts).toBeUndefined()
  })

  it('one execute_sql tool call: verifies apiMessages has 4 entries on 2nd call', async () => {
    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_1',
            function: {
              name: 'execute_sql',
              arguments: JSON.stringify({ sql: 'SELECT 1' })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Got it.' }
    ])
    const execFile = makeExecFileMock([
      { stdout: '[{"val":1}]', stderr: '' }
    ])
    const deps = makeTestDeps({ openai, execFile })
    const sender = makeEventSender()
    const result = await handleChat(
      [{ role: 'user', content: 'query' }],
      sender,
      deps
    )
    expect(result.text).toContain('Got it.')

    // The apiMessages array is passed by reference. By the time we inspect it,
    // the 2nd response's assistant message has also been pushed, giving 5:
    // [system, user, assistant(tool_calls), tool_result, assistant(stop)]
    const createFn = openai.chat.completions.create as ReturnType<typeof vi.fn>
    expect(createFn).toHaveBeenCalledTimes(2)
    const secondCallArgs = createFn.mock.calls[1][0]
    expect(secondCallArgs.messages).toHaveLength(5)
  })

  it('one run_finance_command tool call: verifies eventSender.send called', async () => {
    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_2',
            function: {
              name: 'run_finance_command',
              arguments: JSON.stringify({ command: 'dashboard' })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Dashboard loaded.' }
    ])
    const execFile = makeExecFileMock([
      { stdout: '[]', stderr: '' }, // router: categories
      { stdout: '[]', stderr: '' }, // router: trend
      { stdout: '[]', stderr: '' }, // router: merchants
      { stdout: '[]', stderr: '' }, // router: income
      { stdout: 'dashboard output', stderr: '' } // tool: dashboard
    ])
    const deps = makeTestDeps({ openai, execFile })
    const sender = makeEventSender()
    await handleChat([{ role: 'user', content: 'show dashboard' }], sender, deps)
    expect(sender.send).toHaveBeenCalledWith('chat:tool-result', {
      tool: 'run_finance_command',
      command: 'dashboard',
      result: 'dashboard output'
    })
  })

  it('generate_chart tool call: verifies fs.writeFileSync and fs.unlinkSync called', async () => {
    const fsMock = makeFsMock()
    // Make the chart path exist after execFile runs
    const execFile = vi.fn().mockImplementation(async () => {
      // Simulate chart being created by the script
      ;(fsMock.writeFileSync as any)('/test/vault/Finance/reports/chart.png', 'png data')
      return { stdout: '', stderr: '' }
    })
    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_3',
            function: {
              name: 'generate_chart',
              arguments: JSON.stringify({
                filename: 'chart.png',
                script: 'import matplotlib; ...'
              })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Chart generated.' }
    ])
    const deps = makeTestDeps({ openai, execFile: execFile as any, fs: fsMock })
    const sender = makeEventSender()
    const result = await handleChat(
      [{ role: 'user', content: 'make a chart' }],
      sender,
      deps
    )
    expect(result.text).toContain('Chart generated.')
    expect(result.charts).toHaveLength(1)
    expect(result.charts![0].path).toBe('/test/vault/Finance/reports/chart.png')
    // writeFileSync called for the tmp script
    expect(fsMock.writeFileSync).toHaveBeenCalled()
    // unlinkSync called in finally to clean up
    expect(fsMock.unlinkSync).toHaveBeenCalled()
  })

  it('generate_chart when writeFileSync throws: unlinkSync NOT called (regression)', async () => {
    const fsMock = makeFsMock()
    // Make writeFileSync throw before the file is created
    ;(fsMock.writeFileSync as ReturnType<typeof vi.fn>).mockImplementation(() => {
      throw new Error('disk full')
    })
    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_4',
            function: {
              name: 'generate_chart',
              arguments: JSON.stringify({
                filename: 'chart.png',
                script: 'import matplotlib; ...'
              })
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Failed.' }
    ])
    const execFile = makeExecFileMock([])
    const deps = makeTestDeps({ openai, execFile, fs: fsMock })
    const sender = makeEventSender()
    await handleChat(
      [{ role: 'user', content: 'make a chart' }],
      sender,
      deps
    )
    // existsSync returns false for the tmp file since writeFileSync threw,
    // so unlinkSync should NOT be called
    expect(fsMock.unlinkSync).not.toHaveBeenCalled()
  })

  it('unknown tool: loop continues without crash, tool result contains Unknown tool', async () => {
    const openai = makeOpenAIMock([
      {
        finish_reason: 'tool_calls',
        tool_calls: [
          {
            id: 'call_5',
            function: {
              name: 'nonexistent_tool',
              arguments: '{}'
            }
          }
        ]
      },
      { finish_reason: 'stop', content: 'Handled unknown.' }
    ])
    const deps = makeTestDeps({ openai })
    const sender = makeEventSender()
    const result = await handleChat(
      [{ role: 'user', content: 'do something' }],
      sender,
      deps
    )
    expect(result.text).toContain('Handled unknown.')

    // Verify the tool result message sent to the API contains 'Unknown tool'
    const createFn = openai.chat.completions.create as ReturnType<typeof vi.fn>
    const secondCallMessages = createFn.mock.calls[1][0].messages
    const toolMsg = secondCallMessages.find(
      (m: any) => m.role === 'tool' && m.tool_call_id === 'call_5'
    )
    expect(toolMsg.content).toContain('Unknown tool')
  })

  it('API throws error: error propagates from handleChat', async () => {
    const openai = {
      chat: {
        completions: {
          create: vi.fn().mockRejectedValue(new Error('API rate limited'))
        }
      }
    } as unknown as ReturnType<typeof makeOpenAIMock>
    const deps = makeTestDeps({ openai })
    const sender = makeEventSender()
    await expect(
      handleChat([{ role: 'user', content: 'hi' }], sender, deps)
    ).rejects.toThrow('API rate limited')
  })
})
