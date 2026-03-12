"""Finance Chat — Native desktop app routing queries through Claude Code CLI.

Uses pywebview for a native macOS window with embedded WebKit.
Claude Code CLI (`claude -p`) handles AI + tool execution using your existing subscription.
"""

import json
import os
import re
import subprocess

import webview

VAULT_ROOT = os.environ.get("VAULT_ROOT", "/Users/ychen2/Obsidian")
PYTHON = os.path.join(VAULT_ROOT, "Scripts/venv/bin/python3")
FINANCE_SCRIPT = os.path.join(VAULT_ROOT, ".claude/scripts/finance_db.py")
REPORTS_DIR = os.path.join(VAULT_ROOT, "Finance/reports")


def run_command(command: str, args: str = "") -> str:
    """Run finance_db.py command and return output."""
    cmd = [PYTHON, FINANCE_SCRIPT, command]
    if args:
        cmd.extend(args.split())
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=VAULT_ROOT)
        output = result.stdout.strip()
        if result.returncode != 0:
            output += f"\nSTDERR: {result.stderr.strip()}" if result.stderr else ""
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 60 seconds"
    except Exception as e:
        return f"ERROR: {e}"


def build_system_prompt() -> str:
    """Build a system prompt that tells Claude Code how to use finance_db.py."""
    parts = [
        "You are a personal finance analyst. Answer questions about spending, income, and financial data.",
        "",
        "## Tools Available",
        f"Run finance commands: `{PYTHON} {FINANCE_SCRIPT} <command> [args]`",
        "",
        "Key commands:",
        "- `dashboard` — overview of all data sources",
        "- `query \"<sql>\"` — run SQL against Finance/finance.db",
        "- `status` — import status",
        "- `validate` — check balances",
        "- `match-pending` — match pending transactions",
        "- `categorize` — apply categorization rules",
        "- `uncategorized` — show uncategorized transactions",
        "",
        "Key tables: transactions, categories, accounts, payslips, payslip_line_items, "
        "amazon_orders, fidelity_cma_transactions, becu_checking_transactions, becu_heloc_statements",
        "",
        "## Query Rules",
        "- Filter spending with `is_transfer=0` and use `ABS(amount)` for display",
        "- Present results as clean markdown tables with $ amounts rounded to 2 decimal places",
        "- For charts: use matplotlib, save to Finance/reports/<name>.png",
        f"  Run chart scripts with: `{PYTHON} <script.py>`",
        "",
        "## Files",
        f"- Pending transactions: {VAULT_ROOT}/Finance/pending-transactions.yaml",
        f"- Database: {VAULT_ROOT}/Finance/finance.db",
        f"- Reports dir: {VAULT_ROOT}/Finance/reports/",
    ]

    # Append schema reference if available
    finance_claude = os.path.join(VAULT_ROOT, "Finance/CLAUDE.md")
    if os.path.exists(finance_claude):
        with open(finance_claude) as f:
            parts.append("\n## Schema Reference\n" + f.read())

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# HTML/CSS/JS chat UI
# ---------------------------------------------------------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  :root {
    --bg: #1e1e2e;
    --surface: #313244;
    --text: #cdd6f4;
    --text-dim: #a6adc8;
    --accent: #89b4fa;
    --user-bg: #45475a;
    --tool-bg: #1e1e2e;
    --border: #585b70;
    --input-bg: #313244;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg: #eff1f5;
      --surface: #ccd0da;
      --text: #4c4f69;
      --text-dim: #6c6f85;
      --accent: #1e66f5;
      --user-bg: #bcc0cc;
      --tool-bg: #e6e9ef;
      --border: #9ca0b0;
      --input-bg: #ccd0da;
    }
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .msg {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 12px;
    line-height: 1.5;
    font-size: 14px;
    word-wrap: break-word;
  }
  .msg.user {
    align-self: flex-end;
    background: var(--user-bg);
    border-bottom-right-radius: 4px;
  }
  .msg.assistant {
    align-self: flex-start;
    background: var(--surface);
    border-bottom-left-radius: 4px;
  }
  .msg.assistant table {
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 13px;
    width: 100%;
  }
  .msg.assistant th, .msg.assistant td {
    border: 1px solid var(--border);
    padding: 4px 8px;
    text-align: left;
  }
  .msg.assistant th {
    background: var(--tool-bg);
  }
  .msg.assistant code {
    background: var(--tool-bg);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 13px;
  }
  .msg.assistant pre {
    background: var(--tool-bg);
    padding: 8px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 6px 0;
  }
  .msg.assistant pre code {
    padding: 0;
    background: none;
  }
  .msg.assistant img {
    max-width: 100%;
    border-radius: 6px;
    margin: 6px 0;
  }
  .thinking {
    align-self: flex-start;
    color: var(--text-dim);
    font-style: italic;
    font-size: 13px;
    padding: 6px 14px;
  }
  .thinking .dot { animation: blink 1.4s infinite; }
  .thinking .dot:nth-child(2) { animation-delay: 0.2s; }
  .thinking .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes blink { 0%,80%,100%{opacity:0} 40%{opacity:1} }
  #input-area {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    background: var(--bg);
  }
  #user-input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--input-bg);
    color: var(--text);
    font-size: 14px;
    font-family: inherit;
    resize: none;
    outline: none;
    min-height: 40px;
    max-height: 120px;
  }
  #user-input:focus { border-color: var(--accent); }
  #send-btn {
    padding: 8px 18px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    font-weight: 600;
    align-self: flex-end;
  }
  #send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
<div id="messages"></div>
<div id="input-area">
  <textarea id="user-input" placeholder="Ask about your finances..." rows="1"></textarea>
  <button id="send-btn" onclick="sendMessage()">Send</button>
</div>
<script>
const msgContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
let busy = false;

userInput.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

userInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function scrollToBottom() {
  msgContainer.scrollTop = msgContainer.scrollHeight;
}

function addMessage(role, html) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML = html;
  msgContainer.appendChild(div);
  scrollToBottom();
  return div;
}

function addThinking() {
  const div = document.createElement('div');
  div.className = 'thinking';
  div.id = 'thinking-indicator';
  div.innerHTML = 'Thinking<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
  msgContainer.appendChild(div);
  scrollToBottom();
  return div;
}

function removeThinking() {
  const el = document.getElementById('thinking-indicator');
  if (el) el.remove();
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

function renderMarkdown(text) {
  try {
    return marked.parse(text);
  } catch (e) {
    return escapeHtml(text);
  }
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || busy) return;

  busy = true;
  sendBtn.disabled = true;
  userInput.value = '';
  userInput.style.height = 'auto';

  addMessage('user', escapeHtml(text));
  addThinking();

  try {
    const result = await window.pywebview.api.send_message(text);
    removeThinking();
    if (result.error) {
      addMessage('assistant', '<em>Error: ' + escapeHtml(result.error) + '</em>');
    } else {
      let html = renderMarkdown(result.text || '');
      if (result.images) {
        for (const img of result.images) {
          html += '<img src="file://' + img + '">';
        }
      }
      addMessage('assistant', html);
    }
  } catch (e) {
    removeThinking();
    addMessage('assistant', '<em>Error: ' + escapeHtml(String(e)) + '</em>');
  }

  busy = false;
  sendBtn.disabled = false;
  userInput.focus();
}

// Load initial dashboard on startup
window.addEventListener('pywebviewready', async function() {
  try {
    const status = await window.pywebview.api.get_initial_status();
    if (status) {
      addMessage('assistant', renderMarkdown(status));
    }
  } catch (e) {
    addMessage('assistant', '<em>Failed to load: ' + escapeHtml(String(e)) + '</em>');
  }
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# pywebview API class — routes queries through Claude Code CLI
# ---------------------------------------------------------------------------

class Api:
    def __init__(self):
        self.system_prompt = build_system_prompt()
        self.conversation: list[tuple[str, str]] = []  # (role, text) pairs for context

    def get_initial_status(self):
        """Called on window load — run dashboard and return formatted status."""
        dashboard = run_command("dashboard")
        return f"**Finance Chat ready.** Ask me anything about your spending, income, or financial data.\n\n<details><summary>Dashboard</summary>\n\n```\n{dashboard}\n```\n</details>"

    def send_message(self, user_text: str):
        """Route user question through `claude -p` CLI."""
        self.conversation.append(("user", user_text))

        # Build the full prompt with conversation history for multi-turn context
        prompt_parts = []
        if len(self.conversation) > 1:
            prompt_parts.append("Previous conversation:")
            for role, text in self.conversation[:-1]:
                label = "User" if role == "user" else "Assistant"
                # Truncate long assistant responses in history to save tokens
                display = text[:2000] + "..." if len(text) > 2000 else text
                prompt_parts.append(f"{label}: {display}")
            prompt_parts.append("")

        prompt_parts.append(user_text)
        full_prompt = "\n".join(prompt_parts)

        try:
            result = subprocess.run(
                [
                    "claude", "-p",
                    "--system-prompt", self.system_prompt,
                    "--allowed-tools", "Bash(Scripts/venv/bin/python3*),Bash(cat*),Read",
                    "--no-session-persistence",
                    "--model", os.environ.get("CLAUDE_MODEL", "sonnet"),
                ],
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=VAULT_ROOT,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"claude exited with code {result.returncode}"
                return {"error": error_msg, "images": []}

            response = result.stdout.strip()

        except subprocess.TimeoutExpired:
            return {"error": "Request timed out after 120 seconds.", "images": []}
        except FileNotFoundError:
            return {"error": "Claude Code CLI not found. Make sure 'claude' is in your PATH.", "images": []}
        except Exception as e:
            return {"error": str(e), "images": []}

        self.conversation.append(("assistant", response))

        # Detect chart images in response
        images = []
        for match in re.finditer(r'(Finance/reports/[\w.-]+\.png)', response):
            img_path = os.path.join(VAULT_ROOT, match.group(1))
            if os.path.exists(img_path):
                images.append(img_path)

        return {"text": response, "images": images}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    api = Api()
    window = webview.create_window(
        "Finance Advisor",
        html=HTML,
        js_api=api,
        width=900,
        height=700,
        min_size=(600, 400),
    )
    webview.start()
