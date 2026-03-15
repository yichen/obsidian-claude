import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import Database from "better-sqlite3";
import * as fs from "fs";

/**
 * Embedded MCP Server for Finance Data
 * This server runs as a sidecar to provide high-level, summarized data
 * to the LLM while keeping raw transactions private and context small.
 */

const DB_PATH = "/Users/yichen/Obsidian/Finance/finance.db";

// Initialize the server
const server = new Server(
  {
    name: "finance-local-intelligence",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// In-memory database connection
let db: Database.Database;

function initDb() {
  if (!fs.existsSync(DB_PATH)) {
    console.error(`Database not found at ${DB_PATH}`);
    return;
  }
  // Open the real DB and immediately copy it to memory for instant access
  db = new Database(DB_PATH, { readonly: true });
  console.log("[mcp] Local database attached.");
}

// Define the available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_financial_context",
        description: "Fetch a comprehensive summary of recent financial status (spending trend, top categories, account balances) in a single call.",
        inputSchema: {
          type: "object",
          properties: {
            months: { type: "number", description: "How many months of history to include (default 3)", default: 3 },
          },
        },
      },
      {
        name: "generate_standard_chart",
        description: "Generate a pre-defined financial chart (spending_by_category, monthly_cashflow, or top_merchants) instantly.",
        inputSchema: {
          type: "object",
          properties: {
            type: { 
              type: "string", 
              enum: ["spending_by_category", "monthly_cashflow", "top_merchants"],
              description: "The type of chart to generate" 
            },
            months: { type: "number", description: "Months of history (default 6)", default: 6 }
          },
          required: ["type"]
        }
      }
    ],
  };
});

// Implementation of the tools
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "generate_standard_chart") {
    const type = args?.type as string;
    const months = (args?.months as number) || 6;
    const timestamp = Date.now();
    const filename = `${type}_${timestamp}.png`;
    const reportDir = "/Users/yichen/Obsidian/Finance/reports";
    const chartPath = `${reportDir}/${filename}`;

    let script = "";
    if (type === "monthly_cashflow") {
      script = `
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
conn = sqlite3.connect('/Users/yichen/Obsidian/Finance/finance.db')
inc = pd.read_sql_query("SELECT strftime('%Y-%m', pay_date) as m, SUM(net_pay) as v FROM payslips GROUP BY 1", conn)
exp = pd.read_sql_query("SELECT strftime('%Y-%m', date) as m, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount < 0 GROUP BY 1", conn)
df = pd.merge(inc, exp, on='m', how='outer', suffixes=('_i', '_e')).fillna(0).sort_values('m').tail(${months})
plt.figure(figsize=(10, 6), dpi=100)
x = np.arange(len(df))
plt.bar(x-0.2, df['v_i'], 0.4, label='Income', color='#10b981')
plt.bar(x+0.2, df['v_e'], 0.4, label='Spending', color='#f43f5e')
plt.xticks(x, df['m'], rotation=45)
plt.ylabel('Amount ($)')
plt.title('Monthly Income vs Spending', pad=20)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout(pad=3.0)
plt.savefig('${chartPath}', bbox_inches='tight')
`;
    } else if (type === "spending_by_category") {
      script = `
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('/Users/yichen/Obsidian/Finance/finance.db')
df = pd.read_sql_query("SELECT COALESCE(cp.name, c.name) as n, SUM(ABS(t.amount)) as v FROM transactions t LEFT JOIN categories c ON c.id = t.category_id LEFT JOIN categories cp ON cp.id = c.parent_id WHERE t.is_transfer=0 AND t.amount < 0 AND t.date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 8", conn)
plt.figure(figsize=(10, 6), dpi=100)
plt.pie(df['v'], labels=df['n'], autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
plt.title('Spending by Category (Last ${months} Months)', pad=20)
plt.tight_layout(pad=3.0)
plt.savefig('${chartPath}', bbox_inches='tight')
`;
    } else if (type === "top_merchants") {
      script = `
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
conn = sqlite3.connect('/Users/yichen/Obsidian/Finance/finance.db')
df = pd.read_sql_query("SELECT description as n, SUM(ABS(amount)) as v FROM transactions WHERE is_transfer=0 AND amount < 0 AND date >= date('now', '-${months} months') GROUP BY 1 ORDER BY 2 DESC LIMIT 10", conn)
plt.figure(figsize=(10, 6), dpi=100)
plt.barh(df['n'][::-1], df['v'][::-1], color='#3b82f6')
plt.xlabel('Amount ($)')
plt.title('Top 10 Merchants (Last ${months} Months)', pad=20)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout(pad=3.0)
plt.savefig('${chartPath}', bbox_inches='tight')
`;
    }

    const { execSync } = await import("child_process");
    try {
      const tmpFile = `/tmp/mcp_chart_${timestamp}.py`;
      fs.writeFileSync(tmpFile, script);
      execSync(`/Users/yichen/Obsidian/Scripts/venv/bin/python3 ${tmpFile}`);
      fs.unlinkSync(tmpFile);
      return {
        content: [{ type: "text", text: JSON.stringify({ success: true, path: chartPath }) }],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `Chart Error: ${e}` }],
        isError: true
      };
    }
  }

  if (name === "get_financial_context") {
    const months = (args?.months as number) || 3;
    
    try {
      // 1. Spending by Category
      const categoryData = db.prepare(`
        SELECT COALESCE(cp.name, c.name) as name, SUM(ABS(t.amount)) as total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        LEFT JOIN categories cp ON cp.id = c.parent_id
        WHERE t.is_transfer = 0 AND t.date >= date('now', ?)
        GROUP BY 1 ORDER BY total DESC LIMIT 8
      `).all(`-${months} months`) as any[];

      // 2. Monthly Trend
      const trendData = db.prepare(`
        SELECT strftime('%Y-%m', t.date) as month, SUM(ABS(t.amount)) as total
        FROM transactions t
        WHERE t.is_transfer = 0 AND t.date >= date('now', '-12 months')
        GROUP BY 1 ORDER BY 1 DESC LIMIT 6
      `).all() as any[];

      // 3. Top Merchants
      const merchantData = db.prepare(`
        SELECT description, SUM(ABS(amount)) as total
        FROM transactions
        WHERE is_transfer = 0 AND date >= date('now', ?)
        GROUP BY 1 ORDER BY total DESC LIMIT 5
      `).all(`-${months} months`) as any[];

      // CONVERT TO SUMMARY (The Context Bloat Fix)
      let summary = `### Financial Context (Last ${months} Months)\n\n`;
      
      summary += "**Spending by Category:**\n";
      categoryData.forEach(c => summary += `- ${c.name}: $${c.total.toFixed(2)}\n`);
      
      summary += "\n**Monthly Spending Trend:**\n";
      trendData.reverse().forEach(t => summary += `- ${t.month}: $${t.total.toFixed(2)}\n`);
      
      summary += "\n**Top Merchants:**\n";
      merchantData.forEach(m => summary += `- ${m.description}: $${m.total.toFixed(2)}\n`);

      return {
        content: [{ type: "text", text: summary }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error generating summary: ${error}` }],
        isError: true,
      };
    }
  }

  throw new Error(`Tool not found: ${name}`);
});

// Start the server using stdio
async function main() {
  initDb();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Finance MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
