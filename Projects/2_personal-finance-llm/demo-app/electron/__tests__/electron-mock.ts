import { vi } from 'vitest'
import type { FinanceDeps, EventSender } from '../finance-core'
import type OpenAI from 'openai'

// ── Mock API response shape ──────────────────────────────────────────────

export interface MockAPIResponse {
  finish_reason: 'stop' | 'tool_calls'
  content?: string
  tool_calls?: { id: string; function: { name: string; arguments: string } }[]
}

// ── Factory: OpenAI mock ─────────────────────────────────────────────────

/** Convert a MockAPIResponse into an async-iterable stream of chunks */
function makeStreamChunks(resp: MockAPIResponse): object[] {
  const chunks: object[] = []

  if (resp.finish_reason === 'tool_calls' && resp.tool_calls) {
    // Optional filler content alongside tool calls
    if (resp.content) {
      chunks.push({ choices: [{ delta: { content: resp.content }, finish_reason: null }] })
    }
    // One chunk per tool call: id + name in first chunk, arguments in second
    for (let i = 0; i < resp.tool_calls.length; i++) {
      const tc = resp.tool_calls[i]
      chunks.push({
        choices: [{
          delta: {
            tool_calls: [{ index: i, id: tc.id, type: 'function', function: { name: tc.function.name, arguments: '' } }]
          },
          finish_reason: null
        }]
      })
      if (tc.function.arguments) {
        chunks.push({
          choices: [{
            delta: { tool_calls: [{ index: i, function: { arguments: tc.function.arguments } }] },
            finish_reason: null
          }]
        })
      }
    }
    chunks.push({ choices: [{ delta: {}, finish_reason: 'tool_calls' }] })
  } else {
    if (resp.content) {
      chunks.push({ choices: [{ delta: { content: resp.content }, finish_reason: null }] })
    }
    chunks.push({ choices: [{ delta: {}, finish_reason: 'stop' }] })
  }

  return chunks
}

export function makeOpenAIMock(responses: MockAPIResponse[]): OpenAI {
  const queue = [...responses]
  const createFn = vi.fn().mockImplementation(async () => {
    const resp = queue.shift()
    if (!resp) throw new Error('No more mock API responses in queue')
    const chunks = makeStreamChunks(resp)
    return {
      [Symbol.asyncIterator]: async function* () {
        for (const chunk of chunks) {
          yield chunk
        }
      }
    }
  })

  return {
    chat: {
      completions: {
        create: createFn
      }
    }
  } as unknown as OpenAI
}

// ── Factory: execFile mock ───────────────────────────────────────────────

export function makeExecFileMock(
  outputs: { stdout: string; stderr: string }[]
): FinanceDeps['execFile'] {
  const queue = [...outputs]
  return vi.fn().mockImplementation(async () => {
    const out = queue.shift()
    if (!out) throw new Error('No more execFile mock outputs in queue')
    return out
  }) as unknown as FinanceDeps['execFile']
}

// ── Factory: fs mock ─────────────────────────────────────────────────────

export function makeFsMock(files?: Record<string, string>): FinanceDeps['fs'] {
  const store: Record<string, string> = { ...(files || {}) }
  return {
    existsSync: vi.fn().mockImplementation((path: string) => path in store),
    readFileSync: vi.fn().mockImplementation((path: string, _encoding: string) => {
      if (!(path in store)) throw new Error(`ENOENT: ${path}`)
      return store[path]
    }),
    writeFileSync: vi.fn().mockImplementation((path: string, content: string) => {
      store[path] = content
    }),
    mkdirSync: vi.fn(),
    unlinkSync: vi.fn().mockImplementation((path: string) => {
      delete store[path]
    })
  }
}

// ── Factory: EventSender mock ────────────────────────────────────────────

export function makeEventSender(): EventSender & {
  send: ReturnType<typeof vi.fn>
  calls: [string, unknown][]
} {
  const calls: [string, unknown][] = []
  const send = vi.fn().mockImplementation((channel: string, data: unknown) => {
    calls.push([channel, data])
  })
  return { send, calls }
}

// ── Factory: full test deps ──────────────────────────────────────────────

export function makeTestDeps(overrides?: Partial<FinanceDeps>): FinanceDeps {
  return {
    execFile: overrides?.execFile ?? makeExecFileMock([{ stdout: '', stderr: '' }]),
    openai: overrides?.openai ?? makeOpenAIMock([]),
    fs: overrides?.fs ?? makeFsMock(),
    vaultPath: overrides?.vaultPath ?? '/test/vault',
    pythonBin: overrides?.pythonBin ?? '/usr/bin/python3',
    financeScript: overrides?.financeScript ?? '/test/finance_db.py'
  }
}
