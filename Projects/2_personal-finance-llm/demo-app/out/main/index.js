"use strict";
const electron = require("electron");
const path = require("path");
const fs = require("fs");
const child_process = require("child_process");
const util = require("util");
const OpenAI = require("openai");
function _interopNamespaceDefault(e) {
  const n = Object.create(null, { [Symbol.toStringTag]: { value: "Module" } });
  if (e) {
    for (const k in e) {
      if (k !== "default") {
        const d = Object.getOwnPropertyDescriptor(e, k);
        Object.defineProperty(n, k, d.get ? d : {
          enumerable: true,
          get: () => e[k]
        });
      }
    }
  }
  n.default = e;
  return Object.freeze(n);
}
const fs__namespace = /* @__PURE__ */ _interopNamespaceDefault(fs);
const is = {
  dev: !electron.app.isPackaged
};
const platform = {
  isWindows: process.platform === "win32",
  isMacOS: process.platform === "darwin",
  isLinux: process.platform === "linux"
};
const electronApp = {
  setAppUserModelId(id) {
    if (platform.isWindows)
      electron.app.setAppUserModelId(is.dev ? process.execPath : id);
  },
  setAutoLaunch(auto) {
    if (platform.isLinux)
      return false;
    const isOpenAtLogin = () => {
      return electron.app.getLoginItemSettings().openAtLogin;
    };
    if (isOpenAtLogin() !== auto) {
      electron.app.setLoginItemSettings({ openAtLogin: auto });
      return isOpenAtLogin() === auto;
    } else {
      return true;
    }
  },
  skipProxy() {
    return electron.session.defaultSession.setProxy({ mode: "direct" });
  }
};
const optimizer = {
  watchWindowShortcuts(window, shortcutOptions) {
    if (!window)
      return;
    const { webContents } = window;
    const { escToCloseWindow = false, zoom = false } = shortcutOptions || {};
    webContents.on("before-input-event", (event, input) => {
      if (input.type === "keyDown") {
        if (!is.dev) {
          if (input.code === "KeyR" && (input.control || input.meta))
            event.preventDefault();
          if (input.code === "KeyI" && (input.alt && input.meta || input.control && input.shift)) {
            event.preventDefault();
          }
        } else {
          if (input.code === "F12") {
            if (webContents.isDevToolsOpened()) {
              webContents.closeDevTools();
            } else {
              webContents.openDevTools({ mode: "undocked" });
              console.log("Open dev tool...");
            }
          }
        }
        if (escToCloseWindow) {
          if (input.code === "Escape" && input.key !== "Process") {
            window.close();
            event.preventDefault();
          }
        }
        if (!zoom) {
          if (input.code === "Minus" && (input.control || input.meta))
            event.preventDefault();
          if (input.code === "Equal" && input.shift && (input.control || input.meta))
            event.preventDefault();
        }
      }
    });
  },
  registerFramelessWindowIpc() {
    electron.ipcMain.on("win:invoke", (event, action) => {
      const win = electron.BrowserWindow.fromWebContents(event.sender);
      if (win) {
        if (action === "show") {
          win.show();
        } else if (action === "showInactive") {
          win.showInactive();
        } else if (action === "min") {
          win.minimize();
        } else if (action === "max") {
          const isMaximized = win.isMaximized();
          if (isMaximized) {
            win.unmaximize();
          } else {
            win.maximize();
          }
        } else if (action === "close") {
          win.close();
        }
      }
    });
  }
};
let VAULT_PATH = "/Users/yichen/Obsidian";
let PYTHON_BIN = `${VAULT_PATH}/Scripts/venv/bin/python3`;
let FINANCE_SCRIPT = `${VAULT_PATH}/.claude/scripts/finance_db.py`;
let openrouterClient;
let CATEGORY_CONTEXT = "";
let financeCache = null;
const CACHE_TTL_MS = 10 * 60 * 1e3;
function loadEnv(envPath, fsImpl = fs__namespace) {
  if (!fsImpl.existsSync(envPath)) {
    console.warn("[env] .env not found at", envPath);
    return;
  }
  const lines = fsImpl.readFileSync(envPath, "utf-8").split("\n");
  for (const line of lines) {
    const m = line.match(/^([^=#\s][^=]*)=(.*)$/);
    if (m) process.env[m[1].trim()] = m[2].trim();
  }
  console.log("[env] loaded from", envPath);
}
function initConfig(deps) {
  {
    const { app } = require("electron");
    const { join } = require("path");
    loadEnv(join(app.getAppPath(), ".env"));
  }
  VAULT_PATH = process.env.VAULT_PATH || "/Users/yichen/Obsidian";
  PYTHON_BIN = `${VAULT_PATH}/Scripts/venv/bin/python3`;
  FINANCE_SCRIPT = `${VAULT_PATH}/.claude/scripts/finance_db.py`;
  const fsImpl = fs__namespace;
  if (!fsImpl.existsSync(PYTHON_BIN)) {
    throw new Error(`Python binary not found at ${PYTHON_BIN}. Please check your environment or VAULT_PATH.`);
  }
  if (!fsImpl.existsSync(FINANCE_SCRIPT)) {
    throw new Error(`Finance script not found at ${FINANCE_SCRIPT}. Please check your environment or VAULT_PATH.`);
  }
  {
    const apiKey = process.env.OPENROUTER_API_KEY || "";
    console.log("[config] API key:", apiKey ? "present" : "MISSING");
    openrouterClient = new OpenAI({
      baseURL: "https://openrouter.ai/api/v1",
      apiKey,
      defaultHeaders: {
        "HTTP-Referer": "finance-demo-app",
        "X-Title": "Finance Demo"
      }
    });
  }
}
const execFileAsync = util.promisify(child_process.execFile);
function makeDeps() {
  if (!openrouterClient) {
    throw new Error("initConfig() must be called before makeDeps()");
  }
  return {
    execFile: execFileAsync,
    openai: openrouterClient,
    fs: {
      existsSync: fs__namespace.existsSync,
      readFileSync: fs__namespace.readFileSync,
      writeFileSync: fs__namespace.writeFileSync,
      mkdirSync: fs__namespace.mkdirSync,
      unlinkSync: fs__namespace.unlinkSync
    },
    vaultPath: VAULT_PATH,
    pythonBin: PYTHON_BIN,
    financeScript: FINANCE_SCRIPT
  };
}
async function initCategoryContext(deps) {
  try {
    const result = await queryDB(`SELECT DISTINCT name FROM categories ORDER BY name`, deps);
    if ("rows" in result && result.rows.length > 0) {
      CATEGORY_CONTEXT = result.rows.map((r) => String(r[0])).join(", ");
      console.log(`[init] Category context loaded: ${result.rows.length} categories`);
    }
  } catch (e) {
    console.warn("[init] Failed to load category context:", e);
  }
}
async function initFinanceCache(deps) {
  try {
    financeCache = { summary: await buildSummary(deps), ts: Date.now() };
    console.log("[init] Finance cache populated");
  } catch (e) {
    console.warn("[init] Failed to populate finance cache:", e);
  }
}
async function runFinanceCommand(subcommand, args, deps) {
  try {
    const { stdout, stderr } = await deps.execFile(
      deps.pythonBin,
      [deps.financeScript, subcommand, ...args],
      { cwd: deps.vaultPath, timeout: 3e4 }
    );
    return stdout || stderr;
  } catch (err) {
    const error = err;
    return error.stdout || error.stderr || error.message || String(err);
  }
}
async function queryDB(sql, deps) {
  try {
    const output = await runFinanceCommand("query", [sql], deps);
    const parsed = JSON.parse(output);
    if (parsed.error) return { error: parsed.error };
    if (Array.isArray(parsed) && parsed.length === 0) return { columns: [], rows: [] };
    if (Array.isArray(parsed) && parsed.length > 0) {
      const columns = Object.keys(parsed[0]);
      return { columns, rows: parsed.map((r) => columns.map((c) => r[c])) };
    }
    return { columns: [], rows: [], ...parsed };
  } catch (err) {
    return { error: String(err) };
  }
}
async function migratePendingYamlToSQLite(deps) {
  try {
    await runFinanceCommand("import-pending-yaml", [], deps);
    console.log("[startup] migratePendingYamlToSQLite complete");
  } catch (err) {
    console.warn("[startup] migratePendingYamlToSQLite error:", err);
  }
}
const TOOLS = [
  {
    type: "function",
    function: {
      name: "execute_batch_sql",
      description: "Execute multiple SQL SELECT statements in parallel. Use this to fetch all required data for a dashboard or complex question in a single round trip.",
      parameters: {
        type: "object",
        properties: {
          queries: {
            type: "array",
            items: { type: "string" },
            description: "Array of SQL SELECT statements"
          }
        },
        required: ["queries"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "execute_sql",
      description: "Execute a SQL query against the local finance SQLite database. Use this to answer spending questions, look up transactions, compute totals, etc.",
      parameters: {
        type: "object",
        properties: {
          sql: {
            type: "string",
            description: "The SQL SELECT statement to execute"
          }
        },
        required: ["sql"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "run_finance_command",
      description: "Run a finance_db.py command. Valid commands: dashboard, status, uncategorized, validate, categorize, match-pending.",
      parameters: {
        type: "object",
        properties: {
          command: {
            type: "string",
            description: 'The command to run (e.g. "dashboard" or "status")'
          }
        },
        required: ["command"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "generate_standard_chart",
      description: "Generate a pre-defined financial chart (spending_by_category, monthly_cashflow, or top_merchants) instantly.",
      parameters: {
        type: "object",
        properties: {
          type: {
            type: "string",
            enum: ["spending_by_category", "monthly_cashflow", "top_merchants", "monthly_income", "monthly_spending", "income_by_source"],
            description: "The type of chart to generate"
          },
          months: {
            type: "number",
            description: "Months of history (default 6)",
            default: 6
          }
        },
        required: ["type"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "generate_chart",
      description: "Generate a chart and save it as a PNG. Provide a self-contained Python script that queries finance.db and saves a chart to Finance/reports/.",
      parameters: {
        type: "object",
        properties: {
          filename: {
            type: "string",
            description: 'Output filename (e.g. "monthly-spending.png")'
          },
          script: {
            type: "string",
            description: "Complete Python script using matplotlib and sqlite3"
          }
        },
        required: ["filename", "script"]
      }
    }
  }
];
const SYSTEM_PROMPT = `You are a personal finance analyst with access to a SQLite database of credit card transactions, payslips, Amazon orders, and tax documents for a user named Yi Chen.

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

**CHART MARKDOWN**: Do NOT include \`![...](path)\` markdown image syntax in your response. Charts are rendered automatically below your text by the app.`;
async function localIntentRouter(messages, deps) {
  const lastUserMsg = [...messages].reverse().find((m) => m.role === "user")?.content.toLowerCase() || "";
  const hasRecentContext = messages.some((m) => m.content.includes("[LOCAL CONTEXT ACQUIRED]"));
  if (hasRecentContext) return null;
  const routerKeywords = [
    "dashboard",
    "summary",
    "how am i doing",
    "spending by category",
    "cash flow",
    "kids",
    "children",
    "spending",
    "save",
    "savings",
    "projection",
    "forecast",
    "runway",
    "categories",
    "top",
    "merchants",
    "month",
    "cashflow",
    "income",
    "salary",
    "invest",
    "fidelity",
    "portfolio"
  ];
  if (routerKeywords.some((kw) => lastUserMsg.includes(kw))) {
    console.log("[router] Intercepted dashboard intent. Fetching local summary...");
    try {
      const summary = await generateLocalSummary(deps);
      return `[LOCAL CONTEXT ACQUIRED]
${summary}`;
    } catch (e) {
      console.warn("[router] Failed to generate local summary:", e);
    }
  }
  return null;
}
async function buildSummary(deps) {
  const [categories, trend, merchants, income] = await Promise.all([
    queryDB("SELECT COALESCE(cp.name, c.name) as name, SUM(ABS(t.amount)) as total FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer = 0 AND t.date >= date('now', '-3 months') GROUP BY 1 ORDER BY total DESC LIMIT 8", deps),
    queryDB("SELECT strftime('%Y-%m', t.date) as month, SUM(ABS(t.amount)) as total FROM transactions t WHERE t.is_transfer = 0 AND t.date >= date('now', '-12 months') GROUP BY 1 ORDER BY 1 DESC", deps),
    queryDB("SELECT description, SUM(ABS(amount)) as total FROM transactions WHERE is_transfer = 0 AND date >= date('now', '-1 month') GROUP BY 1 ORDER BY total DESC LIMIT 10", deps),
    queryDB("SELECT strftime('%Y-%m', pay_date) as month, SUM(net_pay) as total FROM payslips WHERE pay_date >= date('now', '-6 months') GROUP BY 1 ORDER BY 1 DESC", deps)
  ]);
  let s = "## Local Financial Intelligence (Pre-fetched Context)\n";
  if ("rows" in categories && categories.rows.length > 0) {
    s += "\n### Top Spending Categories (Last 3 Months):\n" + categories.rows.map((r) => `- ${r[0]}: $${Number(r[1]).toFixed(2)}`).join("\n");
  }
  if ("rows" in income && income.rows.length > 0) {
    s += "\n\n### Income History (Last 6 Months):\n" + income.rows.map((r) => `- ${r[0]}: $${Number(r[1]).toFixed(2)}`).join("\n");
  }
  if ("rows" in trend && trend.rows.length > 0) {
    s += "\n\n### Monthly Spending Trend:\n" + trend.rows.map((r) => `- ${r[0]}: $${Number(r[1]).toFixed(2)}`).join("\n");
  }
  s += "\n\n**INSTRUCTION**: Use the data above to answer the user immediately. Do not run these queries again. If charts are needed, call 'generate_standard_chart' now.";
  return s;
}
async function generateLocalSummary(deps) {
  if (financeCache && Date.now() - financeCache.ts < CACHE_TTL_MS) {
    console.log("[router] Finance cache hit (<1ms)");
    return financeCache.summary;
  }
  const summary = await buildSummary(deps);
  financeCache = { summary, ts: Date.now() };
  return summary;
}
async function generateChart(type, months, deps) {
  const reportDir = `${deps.vaultPath}/Finance/reports`;
  if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true });
  const filename = `${type}_${Date.now()}.png`;
  const chartPath = `${reportDir}/${filename}`;
  let script = "";
  if (type === "monthly_cashflow") {
    script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
inc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips GROUP BY 1", conn)
exp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount < 0 GROUP BY 1", conn)
df = pd.merge(inc, exp, on='m', how='outer', suffixes=('_i', '_e')).fillna(0).sort_values('m').tail(${months})
plt.figure(figsize=(10, 6))
x = np.arange(len(df))
plt.bar(x-0.2, df['v_i'], 0.4, label='Income', color='green')
plt.bar(x+0.2, df['v_e'], 0.4, label='Spending', color='red')
plt.xticks(x, df['m'], rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('${chartPath}')`;
  } else if (type === "spending_by_category") {
    script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
df = pd.read_sql_query("SELECT COALESCE(cp.name, c.name) as n, SUM(ABS(t.amount)) as v FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer=0 AND t.amount < 0 AND t.date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 8", conn)
plt.figure(figsize=(10, 6))
plt.pie(df['v'], labels=df['n'], autopct='%1.1f%%')
plt.title('Spending by Category (Last ${months} Months)')
plt.tight_layout()
plt.savefig('${chartPath}')`;
  } else if (type === "monthly_income") {
    script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
inc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips WHERE pay_date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 1", conn)
plt.figure(figsize=(10, 6))
plt.bar(range(len(inc)), inc['v'], color='#22c55e')
plt.xticks(range(len(inc)), inc['m'].tolist(), rotation=45)
plt.title('Income')
plt.tight_layout()
plt.savefig('${chartPath}')`;
  } else if (type === "monthly_spending") {
    script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
exp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount<0 AND date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 1", conn)
plt.figure(figsize=(10, 6))
plt.bar(range(len(exp)), exp['v'], color='#6366f1')
plt.xticks(range(len(exp)), exp['m'].tolist(), rotation=45)
plt.title('Spending')
plt.tight_layout()
plt.savefig('${chartPath}')`;
  } else if (type === "top_merchants") {
    script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
df = pd.read_sql_query("SELECT description as n, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount<0 AND date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 10", conn)
plt.figure(figsize=(10, 6))
plt.barh(range(len(df)), df['v'])
plt.yticks(range(len(df)), df['n'].tolist())
plt.title('Top Merchants (Last ${months} Months)')
plt.tight_layout()
plt.savefig('${chartPath}')`;
  } else if (type === "income_by_source") {
    script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
df = pd.read_sql_query("SELECT employer as n, SUM(net_pay) as v FROM payslips WHERE pay_date >= date('now', '-${months} months') GROUP BY employer ORDER BY v DESC", conn)
plt.figure(figsize=(10, 6))
plt.pie(df['v'], labels=df['n'], autopct='%1.1f%%')
plt.title('Income by Source (Last ${months} Months)')
plt.tight_layout()
plt.savefig('${chartPath}')`;
  } else {
    return null;
  }
  const tmpScript = `/tmp/gen_chart_${type}_${Date.now()}.py`;
  try {
    deps.fs.writeFileSync(tmpScript, script);
    await deps.execFile(deps.pythonBin, [tmpScript], {
      cwd: deps.vaultPath,
      env: { ...process.env, MPLBACKEND: "Agg" }
    });
    if (deps.fs.existsSync(chartPath)) {
      const b64 = deps.fs.readFileSync(chartPath, "base64");
      return `data:image/png;base64,${b64}`;
    }
    return null;
  } catch (err) {
    console.error(`[generateChart] Failed to generate ${type}:`, err);
    return null;
  } finally {
    if (deps.fs.existsSync(tmpScript)) deps.fs.unlinkSync(tmpScript);
  }
}
async function handleChat(messages, eventSender, deps) {
  const localContext = await localIntentRouter(messages, deps);
  let augmentedMessages;
  if (localContext) {
    const lastUserIdx = messages.reduceRight((found, m, i) => found === -1 && m.role === "user" ? i : found, -1);
    if (lastUserIdx >= 0) {
      augmentedMessages = [
        ...messages.slice(0, lastUserIdx),
        { role: "assistant", content: localContext },
        messages[lastUserIdx]
      ];
    } else {
      augmentedMessages = [...messages, { role: "assistant", content: localContext }];
    }
  } else {
    augmentedMessages = [...messages];
  }
  const history = augmentedMessages.slice(-10);
  const dynamicSystemPrompt = CATEGORY_CONTEXT ? `${SYSTEM_PROMPT}

Valid spending categories: ${CATEGORY_CONTEXT}` : SYSTEM_PROMPT;
  const apiMessages = [
    { role: "system", content: dynamicSystemPrompt },
    ...history.map((m) => ({ role: m.role, content: m.content }))
  ];
  let continueLoop = true;
  const allCharts = [];
  const MAX_TOOL_ROUNDS = 15;
  let rounds = 0;
  const sessionDir = `${deps.vaultPath}/Finance/reports/debug/sessions`;
  if (!deps.fs.existsSync(sessionDir)) deps.fs.mkdirSync(sessionDir, { recursive: true });
  const sessionTimestamp = (/* @__PURE__ */ new Date()).toISOString().replace("T", "_").replace(/:/g, "-").substring(0, 19);
  const sessionFile = `${sessionDir}/${sessionTimestamp}.json`;
  const sessionLog = { session: (/* @__PURE__ */ new Date()).toISOString(), rounds: [] };
  deps.fs.writeFileSync(sessionFile, JSON.stringify(sessionLog, null, 2));
  const timings = [];
  const t0 = Date.now();
  const elapsed = () => Date.now() - t0;
  const timed = async (label, fn) => {
    const start = Date.now();
    const result = await fn();
    const ms = Date.now() - start;
    timings.push({ label, ms });
    console.log(`[timing] ${label}: ${ms}ms`);
    return result;
  };
  while (continueLoop && rounds++ < MAX_TOOL_ROUNDS) {
    const requestSnapshot = { model: "anthropic/claude-3.7-sonnet", messages: [...apiMessages], tools: TOOLS };
    const apiStart = Date.now();
    const stream = await deps.openai.chat.completions.create({
      model: "anthropic/claude-3.7-sonnet",
      messages: apiMessages,
      tools: TOOLS,
      max_tokens: 4096,
      stream: true,
      stream_options: { include_usage: true }
    });
    let streamContent = "";
    let streamFinishReason = null;
    const streamToolCallMap = {};
    let usage;
    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta;
      if (chunk.choices[0]?.finish_reason) streamFinishReason = chunk.choices[0].finish_reason;
      if (delta?.content) {
        streamContent += delta.content;
        eventSender.send("chat:stream-token", { token: delta.content });
      }
      if (delta?.tool_calls) {
        for (const tc of delta.tool_calls) {
          if (!streamToolCallMap[tc.index]) {
            streamToolCallMap[tc.index] = { id: "", type: "function", function: { name: "", arguments: "" } };
          }
          if (tc.id) streamToolCallMap[tc.index].id = tc.id;
          if (tc.function?.name) streamToolCallMap[tc.index].function.name += tc.function.name;
          if (tc.function?.arguments) streamToolCallMap[tc.index].function.arguments += tc.function.arguments;
        }
      }
      if (chunk.usage) usage = chunk.usage;
    }
    const apiMs = Date.now() - apiStart;
    const toolCallsList = Object.entries(streamToolCallMap).sort(([a], [b]) => Number(a) - Number(b)).map(([, tc]) => tc);
    let msgContent = streamContent;
    if (toolCallsList.length > 0 && streamContent) {
      console.log(`[debug] Stripping conversational filler: ${streamContent.substring(0, 50)}...`);
      msgContent = "";
    }
    const msg = {
      role: "assistant",
      content: msgContent || null,
      ...toolCallsList.length > 0 ? {
        tool_calls: toolCallsList.map((tc) => ({ id: tc.id || `tc_${Math.random()}`, type: "function", function: tc.function }))
      } : {}
    };
    apiMessages.push(msg);
    timings.push({ label: `API call #${rounds} [${streamFinishReason}]`, ms: apiMs });
    console.log(`[timing] API call #${rounds}: ${apiMs}ms`);
    try {
      sessionLog.rounds.push({
        round: rounds,
        timestamp: (/* @__PURE__ */ new Date()).toISOString(),
        request: requestSnapshot,
        response: {
          content: streamContent,
          tool_calls: toolCallsList,
          finish_reason: streamFinishReason,
          usage
        },
        elapsed_ms: apiMs
      });
      deps.fs.writeFileSync(sessionFile, JSON.stringify(sessionLog, null, 2));
    } catch (e) {
      console.warn(`[debug] Failed to write session log: ${e}`);
    }
    const trace = `round ${rounds}: ${streamFinishReason}, ${toolCallsList.length} tool call(s), elapsed ${elapsed()}ms`;
    console.log(`[chat] ${trace}`);
    if (streamFinishReason === "tool_calls" && toolCallsList.length > 0) {
      const toolResults = await Promise.all(toolCallsList.map(async (toolCall) => {
        let args;
        try {
          let rawArgs = toolCall.function.arguments.trim();
          if (rawArgs.startsWith("```")) {
            rawArgs = rawArgs.replace(/^```[a-z]*\n/, "").replace(/\n```$/, "");
          }
          args = JSON.parse(rawArgs);
        } catch {
          await timed(`Error parsing tool args: ${toolCall.function.name}`, () => Promise.resolve(""));
          return { role: "tool", tool_call_id: toolCall.id, content: JSON.stringify({ error: "Failed to parse tool arguments" }) };
        }
        let result;
        if (toolCall.function.name === "execute_batch_sql") {
          const queries = args.queries;
          const batchResults = await Promise.all(queries.map(async (sql) => {
            const shortSql = sql.replace(/\s+/g, " ").substring(0, 50);
            const dbResult = await timed(`SQL: ${shortSql}…`, () => queryDB(sql, deps));
            eventSender.send("chat:tool-result", { tool: "execute_sql", sql, result: dbResult });
            return dbResult;
          }));
          result = JSON.stringify(batchResults);
          if (result.length > 8e3) {
            result = result.substring(0, 8e3) + "... [TRUNCATED - USE LIMITS]";
          }
        } else if (toolCall.function.name === "generate_standard_chart") {
          const type = args.type;
          const months = Number(args.months || 6);
          const filename = `${type}_${Date.now()}.png`;
          const reportDir = `${deps.vaultPath}/Finance/reports`;
          if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true });
          const chartPath = `${reportDir}/${filename}`;
          let script = "";
          if (type === "monthly_cashflow") {
            script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
inc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips GROUP BY 1", conn)
exp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount < 0 GROUP BY 1", conn)
df = pd.merge(inc, exp, on='m', how='outer', suffixes=('_i', '_e')).fillna(0).sort_values('m').tail(${months})
plt.figure(figsize=(10, 6))
x = np.arange(len(df))
plt.bar(x-0.2, df['v_i'], 0.4, label='Income', color='green')
plt.bar(x+0.2, df['v_e'], 0.4, label='Spending', color='red')
plt.xticks(x, df['m'], rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('${chartPath}')`;
          } else {
            script = `import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('${deps.vaultPath}/Finance/finance.db')
df = pd.read_sql_query("SELECT COALESCE(cp.name, c.name) as n, SUM(ABS(t.amount)) as v FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer=0 AND t.amount < 0 AND t.date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 8", conn)
plt.figure(figsize=(10, 6))
plt.pie(df['v'], labels=df['n'], autopct='%1.1f%%')
plt.title('Spending by Category (Last ${months} Months)')
plt.tight_layout()
plt.savefig('${chartPath}')`;
          }
          const tmpScript = `/tmp/std_chart_${Date.now()}.py`;
          try {
            deps.fs.writeFileSync(tmpScript, script);
            await timed(
              `std_chart: ${type}`,
              () => deps.execFile(deps.pythonBin, [tmpScript], {
                cwd: deps.vaultPath,
                env: { ...process.env, MPLBACKEND: "Agg" }
              })
            );
            if (deps.fs.existsSync(chartPath)) {
              const b64 = deps.fs.readFileSync(chartPath, "base64");
              allCharts.push({ path: chartPath, data: `data:image/png;base64,${b64}`, type, months });
              result = JSON.stringify({ success: true, path: chartPath });
            } else {
              result = JSON.stringify({ success: false, error: "File not generated" });
            }
          } catch (err) {
            result = JSON.stringify({ error: String(err) });
          } finally {
            if (deps.fs.existsSync(tmpScript)) deps.fs.unlinkSync(tmpScript);
          }
        } else if (toolCall.function.name === "execute_sql") {
          const shortSql = args.sql.replace(/\s+/g, " ").substring(0, 50);
          const dbResult = await timed(`SQL: ${shortSql}…`, () => queryDB(args.sql, deps));
          result = JSON.stringify(dbResult);
          if (result.length > 4e3) {
            result = result.substring(0, 4e3) + "... [TRUNCATED - USE LIMIT OR AGGREGATION]";
          }
          eventSender.send("chat:tool-result", { tool: "execute_sql", sql: args.sql, result: dbResult });
        } else if (toolCall.function.name === "run_finance_command") {
          result = await timed(`cmd: ${args.command}`, () => runFinanceCommand(args.command, [], deps));
          if (result.length > 15e3) {
            result = result.substring(0, 15e3) + "... [TRUNCATED]";
          }
          eventSender.send("chat:tool-result", { tool: "run_finance_command", command: args.command, result });
        } else if (toolCall.function.name === "generate_chart") {
          const reportDir = `${deps.vaultPath}/Finance/reports`;
          if (!deps.fs.existsSync(reportDir)) deps.fs.mkdirSync(reportDir, { recursive: true });
          const tmpScript = `/tmp/chart_${Date.now()}_${Math.random().toString(36).substring(7)}.py`;
          try {
            deps.fs.writeFileSync(tmpScript, args.script);
            const { stdout, stderr } = await timed(
              `chart: ${args.filename}`,
              () => deps.execFile(deps.pythonBin, [tmpScript], {
                cwd: deps.vaultPath,
                timeout: 3e4,
                env: { ...process.env, MPLBACKEND: "Agg" }
              })
            );
            const chartPath = `${reportDir}/${args.filename}`;
            if (deps.fs.existsSync(chartPath)) {
              const b64 = deps.fs.readFileSync(chartPath, "base64");
              allCharts.push({ path: chartPath, data: `data:image/png;base64,${b64}` });
              result = JSON.stringify({ success: true, path: chartPath });
            } else {
              result = JSON.stringify({ success: false, stdout, stderr });
            }
          } catch (err) {
            result = JSON.stringify({ error: String(err) });
          } finally {
            if (deps.fs.existsSync(tmpScript)) deps.fs.unlinkSync(tmpScript);
          }
        } else {
          await timed(`Unknown tool: ${toolCall.function.name}`, () => Promise.resolve(""));
          result = JSON.stringify({ error: "Unknown tool" });
        }
        return { role: "tool", tool_call_id: toolCall.id, content: result };
      }));
      apiMessages.push(...toolResults);
    } else {
      continueLoop = false;
      const totalMs = elapsed();
      const timingLine = buildTimingLine(timings, totalMs);
      console.log(`[timing] total: ${totalMs}ms — ${timingLine}`);
      const text = (streamContent || "") + "\n\n" + timingLine;
      return { text, charts: allCharts.length > 0 ? allCharts : void 0 };
    }
  }
  return { text: "(max tool rounds reached without final response)" };
}
function buildTimingLine(timings, totalMs) {
  const fmt = (ms) => ms >= 1e3 ? `${(ms / 1e3).toFixed(1)}s` : `${ms}ms`;
  const parts = timings.map((t) => `${t.label} **${fmt(t.ms)}**`);
  return `\`⏱ ${fmt(totalMs)} total\` — ${parts.join(" · ")}`;
}
function createWindow() {
  const win = new electron.BrowserWindow({
    width: 1100,
    height: 760,
    show: false,
    titleBarStyle: "hiddenInset",
    backgroundColor: "#0f0f0f",
    webPreferences: {
      preload: path.join(__dirname, "../preload/preload.js"),
      sandbox: false
    }
  });
  win.on("ready-to-show", () => win.show());
  win.webContents.setWindowOpenHandler(({ url }) => {
    electron.shell.openExternal(url);
    return { action: "deny" };
  });
  if (is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    win.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    win.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
}
electron.app.whenReady().then(async () => {
  initConfig();
  const startupDeps = makeDeps();
  initCategoryContext(startupDeps).catch((e) => console.warn("[startup] initCategoryContext failed:", e));
  initFinanceCache(startupDeps).catch((e) => console.warn("[startup] initFinanceCache failed:", e));
  migratePendingYamlToSQLite(startupDeps).catch((e) => console.warn("[startup] migratePendingYamlToSQLite failed:", e));
  electronApp.setAppUserModelId("com.finance.demo");
  electron.app.on("browser-window-created", (_, window) => {
    optimizer.watchWindowShortcuts(window);
  });
  electron.ipcMain.handle("chat:send", async (event, messages) => {
    try {
      return await handleChat(messages, event.sender, makeDeps());
    } catch (err) {
      const status = err?.status ?? err?.statusCode;
      let message;
      if (status === 401) {
        message = "API key expired or invalid — please update your OpenRouter API key in .env and restart the app.";
      } else if (status === 403) {
        message = "Access denied — your API key does not have permission for this model.";
      } else if (status === 429) {
        message = "Rate limit exceeded — please wait a moment and try again.";
      } else if (status === 402) {
        message = "Insufficient credits — please top up your OpenRouter account.";
      } else {
        message = `Error: ${String(err)}`;
      }
      return { text: message };
    }
  });
  electron.ipcMain.handle("db:query", async (_event, sql) => {
    return await queryDB(sql, makeDeps());
  });
  electron.ipcMain.handle("db:execute", async (_event, sql) => {
    try {
      const output = await runFinanceCommand("execute", [sql], makeDeps());
      const parsed = JSON.parse(output);
      return parsed;
    } catch (err) {
      return { error: String(err) };
    }
  });
  electron.ipcMain.handle("finance:command", async (_event, command) => {
    return runFinanceCommand(command, [], makeDeps());
  });
  electron.ipcMain.handle("finance:generate-chart", async (_event, type, months) => {
    return generateChart(type, months, makeDeps());
  });
  electron.ipcMain.handle("finance:recent-topics", async () => {
    try {
      const sessionDir = `${VAULT_PATH}/Finance/reports/debug/sessions`;
      const files = fs.readdirSync(sessionDir).filter((f) => f.endsWith(".json")).sort().slice(-5).reverse();
      const topics = [];
      for (const file of files) {
        try {
          const raw = require("fs").readFileSync(path.join(sessionDir, file), "utf-8");
          const session = JSON.parse(raw);
          const rounds = session.rounds || [];
          for (const round of rounds) {
            const messages = round?.request?.messages || [];
            const userMsgs = messages.filter((m) => m.role === "user");
            if (userMsgs.length > 0) {
              const last = userMsgs[userMsgs.length - 1];
              const text = typeof last.content === "string" ? last.content : last.content?.[0]?.text ?? "";
              const trimmed = text.trim().slice(0, 120);
              if (trimmed && !topics.includes(trimmed)) {
                topics.push(trimmed);
              }
            }
          }
        } catch (_) {
        }
        if (topics.length >= 3) break;
      }
      return topics;
    } catch (_) {
      return [];
    }
  });
  electron.ipcMain.handle("finance:parse-receipt", async (_event, text) => {
    try {
      const client = openrouterClient;
      if (!client) return {};
      const response = await client.chat.completions.create({
        model: "anthropic/claude-3-haiku",
        max_tokens: 256,
        messages: [
          {
            role: "user",
            content: `Extract transaction details from this receipt text. Return JSON only, no explanation:
{"date":"YYYY-MM-DD","amount":0.00,"description":"merchant name","notes":""}

Receipt text:
${text}`
          }
        ]
      });
      const content = response.choices[0]?.message?.content ?? "";
      const match = content.match(/\{[\s\S]*\}/);
      if (match) return JSON.parse(match[0]);
      return {};
    } catch (err) {
      console.error("[parse-receipt] error:", err);
      return {};
    }
  });
  createWindow();
  electron.app.on("activate", () => {
    if (electron.BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") electron.app.quit();
});
