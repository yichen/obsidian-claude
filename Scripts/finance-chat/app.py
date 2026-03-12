"""Finance Chat — Chainlit app wrapping finance_db.py with Claude tool_use."""

import json
import os
import subprocess
import tempfile

import anthropic
import chainlit as cl

VAULT_ROOT = os.environ.get("VAULT_ROOT", "/Users/ychen2/Obsidian")
PYTHON = os.path.join(VAULT_ROOT, "Scripts/venv/bin/python3")
FINANCE_SCRIPT = os.path.join(VAULT_ROOT, ".claude/scripts/finance_db.py")
REPORTS_DIR = os.path.join(VAULT_ROOT, "Finance/reports")

# Load system prompt from SKILL.md + Finance/CLAUDE.md
def load_system_prompt() -> str:
    parts = ["You are a personal finance analyst with access to tools for querying a SQLite finance database.\n"]

    skill_path = os.path.join(VAULT_ROOT, ".claude/skills/finance/SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path) as f:
            # Skip YAML frontmatter
            content = f.read()
            if content.startswith("---"):
                content = content.split("---", 2)[2]
            parts.append(content.strip())

    finance_claude = os.path.join(VAULT_ROOT, "Finance/CLAUDE.md")
    if os.path.exists(finance_claude):
        with open(finance_claude) as f:
            parts.append("\n\n## Additional Schema Reference\n\n" + f.read())

    parts.append("""
## Tool Usage Notes
- Use run_finance_command for high-level commands (dashboard, status, validate, etc.)
- Use run_sql_query for custom SQL queries against the database
- Use read_file to read YAML/markdown files from the vault (e.g., pending-transactions.yaml)
- Use generate_chart to create matplotlib visualizations — they'll be shown inline
- Always filter spending queries with is_transfer=0 and use ABS(amount) for display
- Present results as clean markdown tables with rounded amounts
""")
    return "\n\n".join(parts)


TOOLS = [
    {
        "name": "run_finance_command",
        "description": "Run a finance_db.py CLI command. Available commands: dashboard, status, validate, preflight, categorize, uncategorized, import, import-payslips, import-tax, import-fidelity, import-sofi, import-becu, import-amazon, import-wellsfargo-car, match-pending, rebuild, backup-rules, restore-rules, query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command name (e.g., 'dashboard', 'status', 'validate')"},
                "args": {"type": "string", "description": "Additional arguments (optional)", "default": ""},
            },
            "required": ["command"],
        },
    },
    {
        "name": "run_sql_query",
        "description": "Execute a SQL query against the finance SQLite database. Use for custom queries not covered by built-in commands. The database has tables: transactions, categories, accounts, payslips, payslip_line_items, amazon_orders, tax_documents, tax_line_items, fidelity_accounts, fidelity_cma_transactions, sofi_loan_statements, becu_checking_statements, becu_checking_transactions, becu_heloc_statements, wellsfargo_car_statements.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL query to execute"},
            },
            "required": ["sql"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from the Obsidian vault. Path is relative to vault root. Useful for reading pending-transactions.yaml, payslip YAMLs, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to vault root (e.g., 'Finance/pending-transactions.yaml')"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "generate_chart",
        "description": "Generate a matplotlib chart. The code should query Finance/finance.db directly and save the figure to Finance/reports/<name>.png. Return the filename used.",
        "input_schema": {
            "type": "object",
            "properties": {
                "python_code": {"type": "string", "description": "Complete Python script using matplotlib. Must save figure with plt.savefig()."},
                "filename": {"type": "string", "description": "Output filename (e.g., 'monthly-spending-2025.png')"},
            },
            "required": ["python_code", "filename"],
        },
    },
]


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


def execute_tool(name: str, input_data: dict) -> tuple[str, str | None]:
    """Execute a tool call. Returns (text_result, optional_image_path)."""
    if name == "run_finance_command":
        return run_command(input_data["command"], input_data.get("args", "")), None

    elif name == "run_sql_query":
        return run_command("query", f'"{input_data["sql"]}"'), None

    elif name == "read_file":
        path = os.path.join(VAULT_ROOT, input_data["path"])
        try:
            with open(path) as f:
                return f.read(), None
        except Exception as e:
            return f"ERROR reading {path}: {e}", None

    elif name == "generate_chart":
        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = input_data["filename"]
        output_path = os.path.join(REPORTS_DIR, filename)

        # Inject the save path into the code
        code = input_data["python_code"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [PYTHON, tmp_path], capture_output=True, text=True, timeout=30, cwd=VAULT_ROOT
            )
            if result.returncode != 0:
                return f"ERROR generating chart:\n{result.stderr}", None
            if os.path.exists(output_path):
                return f"Chart saved to {output_path}", output_path
            return f"Chart script ran but file not found at {output_path}\nstdout: {result.stdout}\nstderr: {result.stderr}", None
        except Exception as e:
            return f"ERROR: {e}", None
        finally:
            os.unlink(tmp_path)

    return f"Unknown tool: {name}", None


@cl.on_chat_start
async def on_start():
    """Initialize conversation with system prompt and dashboard context."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        await cl.Message(content="**Set ANTHROPIC_API_KEY environment variable before starting.**").send()
        return

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = load_system_prompt()

    # Prime with dashboard
    dashboard_output = run_command("dashboard")

    # Read pending transactions
    pending_path = os.path.join(VAULT_ROOT, "Finance/pending-transactions.yaml")
    pending_content = ""
    if os.path.exists(pending_path):
        with open(pending_path) as f:
            pending_content = f.read()

    priming = f"## Current Dashboard\n```json\n{dashboard_output}\n```"
    if pending_content:
        priming += f"\n\n## Pending Transactions\n```yaml\n{pending_content}\n```"

    cl.user_session.set("client", client)
    cl.user_session.set("system_prompt", system_prompt + "\n\n" + priming)
    cl.user_session.set("history", [])
    cl.user_session.set("model", os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"))

    await cl.Message(content="Finance Chat ready. Ask me anything about your spending, income, or financial data.").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages with Claude tool_use loop."""
    client: anthropic.Anthropic = cl.user_session.get("client")
    if not client:
        await cl.Message(content="No API key configured. Set ANTHROPIC_API_KEY and restart.").send()
        return

    system_prompt = cl.user_session.get("system_prompt")
    history: list = cl.user_session.get("history")
    model = cl.user_session.get("model")

    history.append({"role": "user", "content": message.content})

    # Tool use loop
    images_to_attach = []
    msg = cl.Message(content="")
    await msg.send()

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=history,
        )

        # Check if there are tool calls
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if not tool_uses:
            # Final text response
            final_text = "\n".join(b.text for b in text_blocks)
            history.append({"role": "assistant", "content": response.content})
            msg.content = final_text

            # Attach any chart images
            for img_path in images_to_attach:
                img_element = cl.Image(name=os.path.basename(img_path), path=img_path, display="inline")
                msg.elements.append(img_element)

            await msg.update()
            break

        # Execute tool calls
        history.append({"role": "assistant", "content": response.content})
        tool_results = []

        for tool_use in tool_uses:
            # Show tool use in a step
            async with cl.Step(name=tool_use.name, type="tool") as step:
                step.input = json.dumps(tool_use.input, indent=2)
                result_text, image_path = execute_tool(tool_use.name, tool_use.input)

                # Truncate very long results
                if len(result_text) > 15000:
                    result_text = result_text[:15000] + "\n... (truncated)"

                step.output = result_text
                if image_path:
                    images_to_attach.append(image_path)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result_text,
            })

        history.append({"role": "user", "content": tool_results})

        # Stream partial text if any
        if text_blocks:
            partial = "\n".join(b.text for b in text_blocks)
            msg.content = partial + "\n\n*Running tools...*"
            await msg.update()

    cl.user_session.set("history", history)
