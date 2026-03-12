#!/bin/bash
cd "$(dirname "$0")"
export VAULT_ROOT="/Users/ychen2/Obsidian"

# Use existing ANTHROPIC_API_KEY from environment, or prompt
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Set ANTHROPIC_API_KEY first:"
    echo "  export ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
fi

# Optional: override model (default: claude-sonnet-4-20250514)
# export CLAUDE_MODEL=claude-opus-4-20250514

exec ../../Scripts/venv/bin/chainlit run app.py -w --port 8000
