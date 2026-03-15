#!/bin/bash
cd "$(dirname "$0")"
export VAULT_ROOT="/Users/ychen2/Obsidian"

# Optional: override model (default: sonnet)
# export CLAUDE_MODEL=opus

exec ../../Scripts/venv/bin/python3 app.py
