import { execFile } from 'child_process'
import { promisify } from 'util'
import OpenAI from 'openai'
import * as fs from 'fs'

// ── Dependency injection interface ────────────────────────────────────────

export interface FinanceDeps {
  execFile: (
    bin: string,
    args: string[],
    opts: object
  ) => Promise<{ stdout: string; stderr: string }>
  openai: OpenAI
  fs: {
    existsSync(path: string): boolean
    readFileSync(path: string, encoding: string): string
    writeFileSync(path: string, content: string): void
    mkdirSync(path: string, opts?: object): void
    unlinkSync(path: string): void
  }
  vaultPath: string
  pythonBin: string
  financeScript: string
}

export interface ChatResult {
  text: string
  chartPath?: string
  chartData?: string  // base64 data URL: "data:image/png;base64,..."
}

export interface EventSender {
  send(channel: string, data: unknown): void
}

// ── Config state (module-level, initialized by initConfig) ────────────────

export let VAULT_PATH: string = '/Users/yichen/Obsidian'
export let PYTHON_BIN: string = `${VAULT_PATH}/Scripts/venv/bin/python3`
export let FINANCE_SCRIPT: string = `${VAULT_PATH}/.claude/scripts/finance_db.py`
export let openrouterClient: OpenAI | undefined

// ── Environment loading ──────────────────────────────────────────────────

export function loadEnv(envPath: string, fsImpl: Pick<typeof fs, 'existsSync' | 'readFileSync'> = fs): void {
  if (!fsImpl.existsSync(envPath)) {
    console.warn('[env] .env not found at', envPath)
    return
  }
  const lines = fsImpl.readFileSync(envPath, 'utf-8').split('\n')
  for (const line of lines) {
    const m = line.match(/^([^=#\s][^=]*)=(.*)$/)
    if (m) process.env[m[1].trim()] = m[2].trim()
  }
  console.log('[env] loaded from', envPath)
}

// ── Init config ──────────────────────────────────────────────────────────

export function initConfig(deps?: Partial<FinanceDeps>): void {
  if (!deps) {
    // Production path: load env from app path, configure from process.env
    const { app } = require('electron')
    const { join } = require('path')
    loadEnv(join(app.getAppPath(), '.env'))
  }

  VAULT_PATH = deps?.vaultPath || process.env.VAULT_PATH || '/Users/yichen/Obsidian'
  PYTHON_BIN = deps?.pythonBin || `${VAULT_PATH}/Scripts/venv/bin/python3`
  FINANCE_SCRIPT = deps?.financeScript || `${VAULT_PATH}/.claude/scripts/finance_db.py`

  if (deps?.openai) {
    openrouterClient = deps.openai
  } else {
    const apiKey = process.env.OPENROUTER_API_KEY || ''
    console.log('[config] API key:', apiKey ? 'present' : 'MISSING')
    openrouterClient = new OpenAI({
      baseURL: 'https://openrouter.ai/api/v1',
      apiKey,
      defaultHeaders: {
        'HTTP-Referer': 'finance-demo-app',
        'X-Title': 'Finance Demo'
      }
    })
  }
}

// ── Make default deps from module state ──────────────────────────────────

const execFileAsync = promisify(execFile)

export function makeDeps(): FinanceDeps {
  if (!openrouterClient) {
    throw new Error('initConfig() must be called before makeDeps()')
  }
  return {
    execFile: execFileAsync as FinanceDeps['execFile'],
    openai: openrouterClient,
    fs: {
      existsSync: fs.existsSync,
      readFileSync: fs.readFileSync as (path: string, encoding: string) => string,
      writeFileSync: fs.writeFileSync as (path: string, content: string) => void,
      mkdirSync: fs.mkdirSync,
      unlinkSync: fs.unlinkSync
    },
    vaultPath: VAULT_PATH,
    pythonBin: PYTHON_BIN,
    financeScript: FINANCE_SCRIPT
  }
}

// ── Finance script helper ────────────────────────────────────────────────
// FIX: Accept subcommand and args separately to avoid splitting SQL on whitespace

export async function runFinanceCommand(
  subcommand: string,
  args: string[],
  deps: FinanceDeps
): Promise<string> {
  try {
    const { stdout, stderr } = await deps.execFile(
      deps.pythonBin,
      [deps.financeScript, subcommand, ...args],
      { cwd: deps.vaultPath, timeout: 30000 }
    )
    return stdout || stderr
  } catch (err: unknown) {
    const error = err as { stdout?: string; stderr?: string; message?: string }
    return error.stdout || error.stderr || error.message || String(err)
  }
}

// ── SQLite helper ────────────────────────────────────────────────────────

export async function queryDB(
  sql: string,
  deps: FinanceDeps
): Promise<{ columns: string[]; rows: unknown[][] } | { error: string }> {
  try {
    const output = await runFinanceCommand('query', [sql], deps)
    const parsed = JSON.parse(output)
    if (parsed.error) return { error: parsed.error }
    if (Array.isArray(parsed) && parsed.length === 0) return { columns: [], rows: [] }
    if (Array.isArray(parsed) && parsed.length > 0) {
      const columns = Object.keys(parsed[0])
      return { columns, rows: parsed.map((r: Record<string, unknown>) => columns.map((c) => r[c])) }
    }
    return { columns: [], rows: [], ...parsed }
  } catch (err) {
    return { error: String(err) }
  }
}

// ── Tool definitions for OpenRouter ──────────────────────────────────────

export const TOOLS: OpenAI.Chat.ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'execute_sql',
      description:
        'Execute a SQL query against the local finance SQLite database. Use this to answer spending questions, look up transactions, compute totals, etc.',
      parameters: {
        type: 'object',
        properties: {
          sql: {
            type: 'string',
            description: 'The SQL SELECT statement to execute'
          }
        },
        required: ['sql']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'run_finance_command',
      description:
        'Run a finance_db.py command. Valid commands: dashboard, status, uncategorized, validate, categorize, match-pending.',
      parameters: {
        type: 'object',
        properties: {
          command: {
            type: 'string',
            description: 'The command to run (e.g. "dashboard" or "status")'
          }
        },
        required: ['command']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'generate_chart',
      description:
        'Generate a chart and save it as a PNG. Provide a self-contained Python script that queries finance.db and saves a chart to Finance/reports/.',
      parameters: {
        type: 'object',
        properties: {
          filename: {
            type: 'string',
            description: 'Output filename (e.g. "monthly-spending.png")'
          },
          script: {
            type: 'string',
            description: 'Complete Python script using matplotlib and sqlite3'
          }
        },
        required: ['filename', 'script']
      }
    }
  }
]

// ── System prompt ────────────────────────────────────────────────────────

export const SYSTEM_PROMPT = `You are a personal finance analyst with access to a SQLite database of credit card transactions, payslips, Amazon orders, and tax documents for a user named Yi Chen.

**Database**: /Users/yichen/Obsidian/Finance/finance.db
**Tables**: transactions, categories, accounts, categorization_rules, payslips, payslip_line_items, tax_documents, tax_line_items, amazon_orders

**Key schema rules**:
- Spending queries: always filter WHERE t.is_transfer = 0, use ABS(t.amount) (charges are negative)
- Category join: LEFT JOIN categories c ON c.id = t.category_id
- Parent category: LEFT JOIN categories cp ON cp.id = c.parent_id
- Account join: JOIN accounts a ON a.id = t.account_id
- Use COALESCE(cp.name, c.name) for top-level category grouping

**Common patterns**:
- Last N months: WHERE t.date >= date('now', '-N months')
- Monthly breakdown: strftime('%Y-%m', t.date) as month
- Top merchants: GROUP BY t.description ORDER BY SUM(ABS(t.amount)) DESC

**Income data**: payslips table has pay_date, gross_pay, net_pay, employer. payslip_line_items has section (pre_tax_deductions, employee_taxes, post_tax_deductions), description, amount.

**Amazon**: amazon_orders table with order_date, total_amount, category_id. Join to categories same as transactions.

**Tax**: tax_documents (form_type, tax_year, payer_name) + tax_line_items (box_name, box_value). W-2 box 1_wages, box 2_fed_tax_withheld, box 12_D (401k). 1040 has summary.adjusted_gross_income, summary.total_tax, summary.refund_or_owed.

Always run execute_sql or run_finance_command to get real data before answering. Do not make up numbers. Present results as clean markdown tables.

**CHARTS**: When the user asks for any chart, graph, or visualization — ALWAYS call the generate_chart tool to produce a matplotlib PNG. NEVER render charts as ASCII art, Unicode characters, or text diagrams. The app renders the PNG image inline in the chat, so text-based charts are unnecessary and harder to read.

Start each session by running run_finance_command("dashboard") to check data freshness.`

// ── Chat handler ─────────────────────────────────────────────────────────

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export async function handleChat(
  messages: Message[],
  eventSender: EventSender,
  deps: FinanceDeps
): Promise<ChatResult> {
  const apiMessages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    { role: 'system', content: SYSTEM_PROMPT },
    ...messages.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
  ]

  let continueLoop = true
  let lastChartPath: string | undefined
  let lastChartData: string | undefined
  const MAX_TOOL_ROUNDS = 15
  let rounds = 0

  // ── Timing ────────────────────────────────────────────────────────────────
  interface TimingEntry { label: string; ms: number }
  const timings: TimingEntry[] = []
  const t0 = Date.now()
  const elapsed = (): number => Date.now() - t0
  const timed = async <T>(label: string, fn: () => Promise<T>): Promise<T> => {
    const start = Date.now()
    const result = await fn()
    const ms = Date.now() - start
    timings.push({ label, ms })
    console.log(`[timing] ${label}: ${ms}ms`)
    return result
  }

  while (continueLoop && rounds++ < MAX_TOOL_ROUNDS) {
    const response = await timed(`API call #${rounds}`, () =>
      deps.openai.chat.completions.create({
        model: 'anthropic/claude-sonnet-4-5',
        messages: apiMessages,
        tools: TOOLS,
        max_tokens: 4096
      })
    )
    const choice = response.choices[0]
    const msg = choice.message
    apiMessages.push(msg)
    console.log(`[chat] round ${rounds}: ${choice.finish_reason}, ${msg.tool_calls?.length ?? 0} tool call(s), elapsed ${elapsed()}ms`)

    if (choice.finish_reason === 'tool_calls' && msg.tool_calls) {
      for (const toolCall of msg.tool_calls) {
        let args: Record<string, string>
        try {
          args = JSON.parse(toolCall.function.arguments)
        } catch {
          apiMessages.push({ role: 'tool', tool_call_id: toolCall.id, content: JSON.stringify({ error: 'Failed to parse tool arguments' }) })
          continue
        }
        let result: string

        if (toolCall.function.name === 'execute_sql') {
          const shortSql = args.sql.replace(/\s+/g, ' ').substring(0, 50)
          const dbResult = await timed(`SQL: ${shortSql}…`, () => queryDB(args.sql, deps))
          result = JSON.stringify(dbResult)
          eventSender.send('chat:tool-result', { tool: 'execute_sql', sql: args.sql, result: dbResult })
        } else if (toolCall.function.name === 'run_finance_command') {
          result = await timed(`cmd: ${args.command}`, () => runFinanceCommand(args.command, [], deps))
          eventSender.send('chat:tool-result', { tool: 'run_finance_command', command: args.command, result })
        } else if (toolCall.function.name === 'generate_chart') {
          const reportDir = `${deps.vaultPath}/Finance/reports`
          if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true })
          const tmpScript = `/tmp/chart_${Date.now()}.py`
          try {
            deps.fs.writeFileSync(tmpScript, args.script)
            const { stdout, stderr } = await timed(`chart: ${args.filename}`, () =>
              deps.execFile(deps.pythonBin, [tmpScript], {
                cwd: deps.vaultPath,
                timeout: 30000,
                env: { ...process.env, MPLBACKEND: 'Agg' }
              })
            )
            const chartPath = `${reportDir}/${args.filename}`
            if (deps.fs.existsSync(chartPath)) {
              lastChartPath = chartPath
              const b64 = fs.readFileSync(chartPath).toString('base64')
              lastChartData = `data:image/png;base64,${b64}`
              result = JSON.stringify({ success: true, path: chartPath })
            } else {
              result = JSON.stringify({ success: false, stdout, stderr })
            }
          } catch (err) {
            result = JSON.stringify({ error: String(err) })
          } finally {
            if (deps.fs.existsSync(tmpScript)) deps.fs.unlinkSync(tmpScript)
          }
        } else {
          result = JSON.stringify({ error: 'Unknown tool' })
        }

        apiMessages.push({ role: 'tool', tool_call_id: toolCall.id, content: result })
      }
    } else {
      continueLoop = false
      const totalMs = elapsed()
      const timingLine = buildTimingLine(timings, totalMs)
      console.log(`[timing] total: ${totalMs}ms — ${timingLine}`)
      const text = (msg.content || '') + '\n\n' + timingLine
      return { text, chartPath: lastChartPath, chartData: lastChartData }
    }
  }
  return { text: '(max tool rounds reached without final response)' }
}

function buildTimingLine(timings: { label: string; ms: number }[], totalMs: number): string {
  const fmt = (ms: number): string => ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
  const parts = timings.map(t => `${t.label} **${fmt(t.ms)}**`)
  return `\`⏱ ${fmt(totalMs)} total\` — ${parts.join(' · ')}`
}
