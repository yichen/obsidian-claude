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
  charts?: Array<{ path: string; data: string; type?: string; months?: number }>
}

export interface EventSender {
  send(channel: string, data: unknown): void
}

// ── Config state (module-level, initialized by initConfig) ────────────────

export let VAULT_PATH: string = '/Users/yichen/Obsidian'
export let PYTHON_BIN: string = `${VAULT_PATH}/Scripts/venv/bin/python3`
export let FINANCE_SCRIPT: string = `${VAULT_PATH}/.claude/scripts/finance_db.py`
export let openrouterClient: OpenAI | undefined

// ── Category context (populated at startup) ──────────────────────────────
let CATEGORY_CONTEXT = ''

// ── Finance cache ────────────────────────────────────────────────────────
interface FinanceCache { summary: string; ts: number }
let financeCache: FinanceCache | null = null
const CACHE_TTL_MS = 10 * 60 * 1000

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

  // ── Validation ─────────────────────────────────────────────────────────
  const fsImpl = deps?.fs || fs
  if (!fsImpl.existsSync(PYTHON_BIN)) {
    throw new Error(`Python binary not found at ${PYTHON_BIN}. Please check your environment or VAULT_PATH.`)
  }
  if (!fsImpl.existsSync(FINANCE_SCRIPT)) {
    throw new Error(`Finance script not found at ${FINANCE_SCRIPT}. Please check your environment or VAULT_PATH.`)
  }

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

// ── Startup initializers ─────────────────────────────────────────────────

export async function initCategoryContext(deps: FinanceDeps): Promise<void> {
  try {
    const result = await queryDB(`SELECT DISTINCT name FROM categories ORDER BY name`, deps)
    if ('rows' in result && result.rows.length > 0) {
      CATEGORY_CONTEXT = result.rows.map((r) => String(r[0])).join(', ')
      console.log(`[init] Category context loaded: ${result.rows.length} categories`)
    }
  } catch (e) {
    console.warn('[init] Failed to load category context:', e)
  }
}

export async function initFinanceCache(deps: FinanceDeps): Promise<void> {
  try {
    financeCache = { summary: await buildSummary(deps), ts: Date.now() }
    console.log('[init] Finance cache populated')
  } catch (e) {
    console.warn('[init] Failed to populate finance cache:', e)
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

// ── Pending YAML migration ────────────────────────────────────────────────

export async function migratePendingYamlToSQLite(deps: FinanceDeps): Promise<void> {
  try {
    await runFinanceCommand('import-pending-yaml', [], deps)
    console.log('[startup] migratePendingYamlToSQLite complete')
  } catch (err) {
    console.warn('[startup] migratePendingYamlToSQLite error:', err)
  }
}

// ── Tool definitions for OpenRouter ──────────────────────────────────────

export const TOOLS: OpenAI.Chat.ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'execute_batch_sql',
      description:
        'Execute multiple SQL SELECT statements in parallel. Use this to fetch all required data for a dashboard or complex question in a single round trip.',
      parameters: {
        type: 'object',
        properties: {
          queries: {
            type: 'array',
            items: { type: 'string' },
            description: 'Array of SQL SELECT statements'
          }
        },
        required: ['queries']
      }
    }
  },
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
      name: 'generate_standard_chart',
      description:
        'Generate a pre-defined financial chart (spending_by_category, monthly_cashflow, or top_merchants) instantly.',
      parameters: {
        type: 'object',
        properties: {
          type: {
            type: 'string',
            enum: ['spending_by_category', 'monthly_cashflow', 'top_merchants', 'monthly_income', 'monthly_spending', 'income_by_source'],
            description: 'The type of chart to generate'
          },
          months: {
            type: 'number',
            description: 'Months of history (default 6)',
            default: 6
          }
        },
        required: ['type']
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

Always run tools to get real data before answering. Do not make up numbers. Present results as clean markdown tables.

**HEADLESS ANALYST MODE**:
1. DO NOT speak to the user (no "I will look that up") until you have ALL the data. 
2. If a request requires multiple queries, you MUST use 'execute_batch_sql' or call multiple tools at once in your VERY FIRST response.
3. Batching is CRITICAL for low latency. Aim for a maximum of 2 tool rounds total.

**SQL LIMITS**: Always use LIMIT 15 in your SQL queries unless you are aggregating data (e.g. GROUP BY), to prevent massive context bloat.

**CHARTS**: When the user asks for any chart, graph, or visualization:
1.  **ALWAYS check if 'generate_standard_chart' can fulfill the request.** If the user asks for "cashflow", "spending by category", or "top merchants", YOU MUST use 'generate_standard_chart'. This is 10x faster.
2.  Only use the manual 'generate_chart' tool for highly custom requests that are not covered by the standard types.
3.  NEVER render charts as ASCII art, Unicode characters, or text diagrams. The app renders the PNG image inline in the chat. You have access to: 'sqlite3', 'matplotlib', 'pandas', and 'numpy'.

**BATCHING**: When you need multiple standard charts, call 'generate_standard_chart' multiple times in the SAME response — do not wait for results before requesting the next chart. The app executes all tool calls in parallel.

**CHART MARKDOWN**: Do NOT include \`![...](path)\` markdown image syntax in your response. Charts are rendered automatically below your text by the app.`

// ── Chat handler ─────────────────────────────────────────────────────────

interface Message {
  role: 'user' | 'assistant'
  content: string
}

// ── Local Intent Router (The Latency Killer) ──────────────────────────────

/**
 * Intercepts common user queries and provides instant local context
 * before the first cloud API call. This eliminates the "Planning" round trip.
 */
async function localIntentRouter(
  messages: Message[],
  deps: FinanceDeps
): Promise<string | null> {
  const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')?.content.toLowerCase() || ''
  
  // ── Optimization: Only inject if NOT already in recent history ──────────
  const hasRecentContext = messages.some(m => m.content.includes('[LOCAL CONTEXT ACQUIRED]'))
  if (hasRecentContext) return null

  // If user asks for dashboard/summary/spending/kids/etc., pre-fetch local aggregated context
  const routerKeywords = [
    'dashboard', 'summary', 'how am i doing', 'spending by category', 'cash flow',
    'kids', 'children', 'spending', 'save', 'savings', 'projection', 'forecast',
    'runway', 'categories', 'top', 'merchants', 'month', 'cashflow', 'income',
    'salary', 'invest', 'fidelity', 'portfolio'
  ]
  if (routerKeywords.some(kw => lastUserMsg.includes(kw))) {
    console.log('[router] Intercepted dashboard intent. Fetching local summary...')
    
    // For now, we call the summary logic directly since it's in the same process
    // In a full MCP setup, this would be a tool call to the sidecar.
    try {
      const summary = await generateLocalSummary(deps)
      return `[LOCAL CONTEXT ACQUIRED]\n${summary}`
    } catch (e) {
      console.warn('[router] Failed to generate local summary:', e)
    }
  }
  
  return null
}

async function buildSummary(deps: FinanceDeps): Promise<string> {
  const [categories, trend, merchants, income] = await Promise.all([
    queryDB("SELECT COALESCE(cp.name, c.name) as name, SUM(ABS(t.amount)) as total FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer = 0 AND t.date >= date('now', '-3 months') GROUP BY 1 ORDER BY total DESC LIMIT 8", deps),
    queryDB("SELECT strftime('%Y-%m', t.date) as month, SUM(ABS(t.amount)) as total FROM transactions t WHERE t.is_transfer = 0 AND t.date >= date('now', '-12 months') GROUP BY 1 ORDER BY 1 DESC", deps),
    queryDB("SELECT description, SUM(ABS(amount)) as total FROM transactions WHERE is_transfer = 0 AND date >= date('now', '-1 month') GROUP BY 1 ORDER BY total DESC LIMIT 10", deps),
    queryDB("SELECT strftime('%Y-%m', pay_date) as month, SUM(net_pay) as total FROM payslips WHERE pay_date >= date('now', '-6 months') GROUP BY 1 ORDER BY 1 DESC", deps)
  ])

  let s = "## Local Financial Intelligence (Pre-fetched Context)\n"

  if ('rows' in categories && categories.rows.length > 0) {
    s += "\n### Top Spending Categories (Last 3 Months):\n" + categories.rows.map(r => `- ${r[0]}: $${Number(r[1]).toFixed(2)}`).join('\n')
  }

  if ('rows' in income && income.rows.length > 0) {
    s += "\n\n### Income History (Last 6 Months):\n" + income.rows.map(r => `- ${r[0]}: $${Number(r[1]).toFixed(2)}`).join('\n')
  }

  if ('rows' in trend && trend.rows.length > 0) {
    s += "\n\n### Monthly Spending Trend:\n" + trend.rows.map(r => `- ${r[0]}: $${Number(r[1]).toFixed(2)}`).join('\n')
  }

  s += "\n\n**INSTRUCTION**: Use the data above to answer the user immediately. Do not run these queries again. If charts are needed, call 'generate_standard_chart' now."
  return s
}

async function generateLocalSummary(deps: FinanceDeps): Promise<string> {
  if (financeCache && Date.now() - financeCache.ts < CACHE_TTL_MS) {
    console.log('[router] Finance cache hit (<1ms)')
    return financeCache.summary
  }
  const summary = await buildSummary(deps)
  financeCache = { summary, ts: Date.now() }
  return summary
}

// ── Standalone chart generator (used by IPC + tool handler) ─────────────

export async function generateChart(
  type: string,
  months: number,
  deps: FinanceDeps
): Promise<string | null> {
  const reportDir = `${deps.vaultPath}/Finance/reports`
  if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true })
  const filename = `${type}_${Date.now()}.png`
  const chartPath = `${reportDir}/${filename}`

  let script = ''
  if (type === 'monthly_cashflow') {
    script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nimport numpy as np\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ninc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips GROUP BY 1", conn)\nexp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount < 0 GROUP BY 1", conn)\ndf = pd.merge(inc, exp, on='m', how='outer', suffixes=('_i', '_e')).fillna(0).sort_values('m').tail(${months})\nplt.figure(figsize=(10, 6))\nx = np.arange(len(df))\nplt.bar(x-0.2, df['v_i'], 0.4, label='Income', color='green')\nplt.bar(x+0.2, df['v_e'], 0.4, label='Spending', color='red')\nplt.xticks(x, df['m'], rotation=45)\nplt.legend()\nplt.tight_layout()\nplt.savefig('${chartPath}')`
  } else if (type === 'spending_by_category') {
    script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ndf = pd.read_sql_query("SELECT COALESCE(cp.name, c.name) as n, SUM(ABS(t.amount)) as v FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer=0 AND t.amount < 0 AND t.date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 8", conn)\nplt.figure(figsize=(10, 6))\nplt.pie(df['v'], labels=df['n'], autopct='%1.1f%%')\nplt.title('Spending by Category (Last ${months} Months)')\nplt.tight_layout()\nplt.savefig('${chartPath}')`
  } else if (type === 'monthly_income') {
    script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ninc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips WHERE pay_date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 1", conn)\nplt.figure(figsize=(10, 6))\nplt.bar(range(len(inc)), inc['v'], color='#22c55e')\nplt.xticks(range(len(inc)), inc['m'].tolist(), rotation=45)\nplt.title('Income')\nplt.tight_layout()\nplt.savefig('${chartPath}')`
  } else if (type === 'monthly_spending') {
    script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\nexp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount<0 AND date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 1", conn)\nplt.figure(figsize=(10, 6))\nplt.bar(range(len(exp)), exp['v'], color='#6366f1')\nplt.xticks(range(len(exp)), exp['m'].tolist(), rotation=45)\nplt.title('Spending')\nplt.tight_layout()\nplt.savefig('${chartPath}')`
  } else if (type === 'top_merchants') {
    script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ndf = pd.read_sql_query("SELECT description as n, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount<0 AND date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 10", conn)\nplt.figure(figsize=(10, 6))\nplt.barh(range(len(df)), df['v'])\nplt.yticks(range(len(df)), df['n'].tolist())\nplt.title('Top Merchants (Last ${months} Months)')\nplt.tight_layout()\nplt.savefig('${chartPath}')`
  } else if (type === 'income_by_source') {
    script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ndf = pd.read_sql_query("SELECT employer as n, SUM(net_pay) as v FROM payslips WHERE pay_date >= date('now', '-${months} months') GROUP BY employer ORDER BY v DESC", conn)\nplt.figure(figsize=(10, 6))\nplt.pie(df['v'], labels=df['n'], autopct='%1.1f%%')\nplt.title('Income by Source (Last ${months} Months)')\nplt.tight_layout()\nplt.savefig('${chartPath}')`
  } else {
    return null
  }

  const tmpScript = `/tmp/gen_chart_${type}_${Date.now()}.py`
  try {
    deps.fs.writeFileSync(tmpScript, script)
    await deps.execFile(deps.pythonBin, [tmpScript], {
      cwd: deps.vaultPath,
      env: { ...process.env, MPLBACKEND: 'Agg' }
    })
    if (deps.fs.existsSync(chartPath)) {
      const b64 = deps.fs.readFileSync(chartPath, 'base64')
      return `data:image/png;base64,${b64}`
    }
    return null
  } catch (err) {
    console.error(`[generateChart] Failed to generate ${type}:`, err)
    return null
  } finally {
    if (deps.fs.existsSync(tmpScript)) deps.fs.unlinkSync(tmpScript)
  }
}

export async function handleChat(
  messages: Message[],
  eventSender: EventSender,
  deps: FinanceDeps
): Promise<ChatResult> {
  // ── STEP 0: Check Local Router ──────────────────────────────────────────
  const localContext = await localIntentRouter(messages, deps)
  let augmentedMessages: typeof messages
  if (localContext) {
    // Insert context BEFORE the last user message so the conversation ends on the user's turn.
    // Appending after the user message causes the API to try to continue an already-complete
    // assistant message, returning empty content with finish_reason: 'stop'.
    const lastUserIdx = messages.reduceRight((found, m, i) => found === -1 && m.role === 'user' ? i : found, -1)
    if (lastUserIdx >= 0) {
      augmentedMessages = [
        ...messages.slice(0, lastUserIdx),
        { role: 'assistant' as const, content: localContext },
        messages[lastUserIdx]
      ]
    } else {
      augmentedMessages = [...messages, { role: 'assistant' as const, content: localContext }]
    }
  } else {
    augmentedMessages = [...messages]
  }

  // Prune history to keep context small and fast: last 10 messages only
  const history = augmentedMessages.slice(-10)
  const dynamicSystemPrompt = CATEGORY_CONTEXT
    ? `${SYSTEM_PROMPT}\n\nValid spending categories: ${CATEGORY_CONTEXT}`
    : SYSTEM_PROMPT
  const apiMessages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    { role: 'system', content: dynamicSystemPrompt },
    ...history.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
  ]

  let continueLoop = true
  const allCharts: Array<{ path: string; data: string; type?: string; months?: number }> = []
  const MAX_TOOL_ROUNDS = 15
  let rounds = 0

  // ── Session log setup ─────────────────────────────────────────────────────
  const sessionDir = `${deps.vaultPath}/Finance/reports/debug/sessions`
  if (!deps.fs.existsSync(sessionDir)) deps.fs.mkdirSync(sessionDir, { recursive: true })
  const sessionTimestamp = new Date().toISOString().replace('T', '_').replace(/:/g, '-').substring(0, 19)
  const sessionFile = `${sessionDir}/${sessionTimestamp}.json`
  const sessionLog: { session: string; rounds: unknown[] } = { session: new Date().toISOString(), rounds: [] }
  deps.fs.writeFileSync(sessionFile, JSON.stringify(sessionLog, null, 2))

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
    // ── Streaming API call ────────────────────────────────────────────────
    const requestSnapshot = { model: 'anthropic/claude-3.7-sonnet', messages: [...apiMessages], tools: TOOLS }
    const apiStart = Date.now()
    const stream = await deps.openai.chat.completions.create({
      model: 'anthropic/claude-3.7-sonnet',
      messages: apiMessages,
      tools: TOOLS,
      max_tokens: 4096,
      stream: true,
      stream_options: { include_usage: true }
    })

    let streamContent = ''
    let streamFinishReason: string | null = null
    const streamToolCallMap: Record<number, { id: string; type: 'function'; function: { name: string; arguments: string } }> = {}
    let usage: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number } | undefined

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta
      if (chunk.choices[0]?.finish_reason) streamFinishReason = chunk.choices[0].finish_reason

      if (delta?.content) {
        streamContent += delta.content
        eventSender.send('chat:stream-token', { token: delta.content })
      }

      if (delta?.tool_calls) {
        for (const tc of delta.tool_calls) {
          if (!streamToolCallMap[tc.index]) {
            streamToolCallMap[tc.index] = { id: '', type: 'function', function: { name: '', arguments: '' } }
          }
          if (tc.id) streamToolCallMap[tc.index].id = tc.id
          if (tc.function?.name) streamToolCallMap[tc.index].function.name += tc.function.name
          if (tc.function?.arguments) streamToolCallMap[tc.index].function.arguments += tc.function.arguments
        }
      }

      if ((chunk as any).usage) usage = (chunk as any).usage
    }

    const apiMs = Date.now() - apiStart
    const toolCallsList = Object.entries(streamToolCallMap)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([, tc]) => tc)

    // Strip conversational filler alongside tool calls
    let msgContent = streamContent
    if (toolCallsList.length > 0 && streamContent) {
      console.log(`[debug] Stripping conversational filler: ${streamContent.substring(0, 50)}...`)
      msgContent = ''
    }

    const msg: OpenAI.Chat.ChatCompletionMessageParam = {
      role: 'assistant',
      content: msgContent || null,
      ...(toolCallsList.length > 0 ? {
        tool_calls: toolCallsList.map(tc => ({ id: tc.id || `tc_${Math.random()}`, type: 'function' as const, function: tc.function }))
      } : {})
    }

    apiMessages.push(msg)
    timings.push({ label: `API call #${rounds} [${streamFinishReason}]`, ms: apiMs })
    console.log(`[timing] API call #${rounds}: ${apiMs}ms`)

    // ── Append round to session log ───────────────────────────────────────
    try {
      sessionLog.rounds.push({
        round: rounds,
        timestamp: new Date().toISOString(),
        request: requestSnapshot,
        response: {
          content: streamContent,
          tool_calls: toolCallsList,
          finish_reason: streamFinishReason,
          usage
        },
        elapsed_ms: apiMs
      })
      deps.fs.writeFileSync(sessionFile, JSON.stringify(sessionLog, null, 2))
    } catch (e) {
      console.warn(`[debug] Failed to write session log: ${e}`)
    }
    // ─────────────────────────────────────────────────────────────────────

    const trace = `round ${rounds}: ${streamFinishReason}, ${toolCallsList.length} tool call(s), elapsed ${elapsed()}ms`
    console.log(`[chat] ${trace}`)

    if (streamFinishReason === 'tool_calls' && toolCallsList.length > 0) {
      const toolResults = await Promise.all(toolCallsList.map(async (toolCall) => {
        let args: Record<string, string>
        try {
          // Claude sometimes wraps JSON in markdown blocks (e.g. ```json ... ```)
          let rawArgs = toolCall.function.arguments.trim()
          if (rawArgs.startsWith('```')) {
            rawArgs = rawArgs.replace(/^```[a-z]*\n/, '').replace(/\n```$/, '')
          }
          args = JSON.parse(rawArgs)
        } catch {
          const errRes = await timed(`Error parsing tool args: ${toolCall.function.name}`, () => Promise.resolve(''))
          return { role: 'tool' as const, tool_call_id: toolCall.id, content: JSON.stringify({ error: 'Failed to parse tool arguments' }) }
        }
        let result: string

        if (toolCall.function.name === 'execute_batch_sql') {
          const queries = (args as any).queries as string[]
          const batchResults = await Promise.all(queries.map(async (sql) => {
            const shortSql = sql.replace(/\s+/g, ' ').substring(0, 50)
            const dbResult = await timed(`SQL: ${shortSql}…`, () => queryDB(sql, deps))
            eventSender.send('chat:tool-result', { tool: 'execute_sql', sql, result: dbResult })
            return dbResult
          }))
          result = JSON.stringify(batchResults)
          if (result.length > 8000) {
            result = result.substring(0, 8000) + '... [TRUNCATED - USE LIMITS]'
          }
        } else if (toolCall.function.name === 'generate_standard_chart') {
          const type = args.type
          const months = Number(args.months || 6)
          const filename = `${type}_${Date.now()}.png`
          const reportDir = `${deps.vaultPath}/Finance/reports`
          if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true })
          const chartPath = `${reportDir}/${filename}`
          
          let script = ""
          if (type === "monthly_cashflow") {
            script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nimport numpy as np\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ninc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips GROUP BY 1", conn)\nexp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount < 0 GROUP BY 1", conn)\ndf = pd.merge(inc, exp, on='m', how='outer', suffixes=('_i', '_e')).fillna(0).sort_values('m').tail(${months})\nplt.figure(figsize=(10, 6))\nx = np.arange(len(df))\nplt.bar(x-0.2, df['v_i'], 0.4, label='Income', color='green')\nplt.bar(x+0.2, df['v_e'], 0.4, label='Spending', color='red')\nplt.xticks(x, df['m'], rotation=45)\nplt.legend()\nplt.tight_layout()\nplt.savefig('${chartPath}')`
          } else {
            script = `import sqlite3\nimport matplotlib.pyplot as plt\nimport pandas as pd\nconn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')\ndf = pd.read_sql_query("SELECT COALESCE(cp.name, c.name) as n, SUM(ABS(t.amount)) as v FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer=0 AND t.amount < 0 AND t.date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 8", conn)\nplt.figure(figsize=(10, 6))\nplt.pie(df['v'], labels=df['n'], autopct='%1.1f%%')\nplt.title('Spending by Category (Last ${months} Months)')\nplt.tight_layout()\nplt.savefig('${chartPath}')`
          }

          const tmpScript = `/tmp/std_chart_${Date.now()}.py`
          try {
            deps.fs.writeFileSync(tmpScript, script)
            await timed(`std_chart: ${type}`, () =>
              deps.execFile(deps.pythonBin, [tmpScript], {
                cwd: deps.vaultPath,
                env: { ...process.env, MPLBACKEND: 'Agg' }
              })
            )
            if (deps.fs.existsSync(chartPath)) {
              const b64 = deps.fs.readFileSync(chartPath, 'base64')
              allCharts.push({ path: chartPath, data: `data:image/png;base64,${b64}`, type, months })
              result = JSON.stringify({ success: true, path: chartPath })
            } else {
              result = JSON.stringify({ success: false, error: 'File not generated' })
            }
          } catch (err) {
            result = JSON.stringify({ error: String(err) })
          } finally {
            if (deps.fs.existsSync(tmpScript)) deps.fs.unlinkSync(tmpScript)
          }
        } else if (toolCall.function.name === 'execute_sql') {
          const shortSql = args.sql.replace(/\s+/g, ' ').substring(0, 50)
          const dbResult = await timed(`SQL: ${shortSql}…`, () => queryDB(args.sql, deps))
          result = JSON.stringify(dbResult)
          // Truncate massive results to prevent context explosion
          if (result.length > 4000) {
            result = result.substring(0, 4000) + '... [TRUNCATED - USE LIMIT OR AGGREGATION]'
          }
          eventSender.send('chat:tool-result', { tool: 'execute_sql', sql: args.sql, result: dbResult })
        } else if (toolCall.function.name === 'run_finance_command') {
          result = await timed(`cmd: ${args.command}`, () => runFinanceCommand(args.command, [], deps))
          if (result.length > 15000) {
            result = result.substring(0, 15000) + '... [TRUNCATED]'
          }
          eventSender.send('chat:tool-result', { tool: 'run_finance_command', command: args.command, result })
        } else if (toolCall.function.name === 'generate_chart') {
          const reportDir = `${deps.vaultPath}/Finance/reports`
          if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true })
          const tmpScript = `/tmp/chart_${Date.now()}_${Math.random().toString(36).substring(7)}.py`
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
              const b64 = deps.fs.readFileSync(chartPath, 'base64')
              allCharts.push({ path: chartPath, data: `data:image/png;base64,${b64}` })
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
          await timed(`Unknown tool: ${toolCall.function.name}`, () => Promise.resolve(''))
          result = JSON.stringify({ error: 'Unknown tool' })
        }
        return { role: 'tool' as const, tool_call_id: toolCall.id, content: result }
      }))
      apiMessages.push(...toolResults)
    } else {
      continueLoop = false
      const totalMs = elapsed()
      const timingLine = buildTimingLine(timings, totalMs)
      console.log(`[timing] total: ${totalMs}ms — ${timingLine}`)
      const text = (streamContent || '') + '\n\n' + timingLine
      return { text, charts: allCharts.length > 0 ? allCharts : undefined }
    }
  }
  return { text: '(max tool rounds reached without final response)' }
}

function buildTimingLine(timings: { label: string; ms: number }[], totalMs: number): string {
  const fmt = (ms: number): string => ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
  const parts = timings.map(t => `${t.label} **${fmt(t.ms)}**`)
  return `\`⏱ ${fmt(totalMs)} total\` — ${parts.join(' · ')}`
}
