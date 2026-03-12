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

export function makeOpenAIMock(responses: MockAPIResponse[]): OpenAI {
  const queue = [...responses]
  const createFn = vi.fn().mockImplementation(async () => {
    const resp = queue.shift()
    if (!resp) throw new Error('No more mock API responses in queue')
    return {
      choices: [
        {
          finish_reason: resp.finish_reason,
          message: {
            role: 'assistant',
            content: resp.content ?? null,
            tool_calls: resp.tool_calls
              ? resp.tool_calls.map((tc) => ({
                  id: tc.id,
                  type: 'function' as const,
                  function: tc.function
                }))
              : undefined
          }
        }
      ]
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
