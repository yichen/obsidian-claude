#!/bin/bash

# This script checks the environment before starting the personal-finance-llm demo app.
# It should be run from the project root: /Users/yichen/Obsidian/Projects/2_personal-finance-llm

PROJECT_ROOT="/Users/yichen/Obsidian/Projects/2_personal-finance-llm"
DEMO_APP_DIR="$PROJECT_ROOT/demo-app"
PYTHON_BIN="/Users/yichen/Obsidian/Scripts/venv/bin/python3"
FINANCE_SCRIPT="/Users/yichen/Obsidian/.claude/scripts/finance_db.py"

echo "🔍 Checking environment..."

# 1. Check if we are in the right place
if [ ! -d "$DEMO_APP_DIR" ]; then
  echo "❌ Error: Cannot find 'demo-app' directory."
  echo "   Make sure you are running this from $PROJECT_ROOT"
  exit 1
fi

# 2. Check Python environment
if [ ! -f "$PYTHON_BIN" ]; then
  echo "❌ Error: Python binary not found at $PYTHON_BIN"
  echo "   Please ensure your virtual environment is set up."
  exit 1
fi

# 3. Check Finance script
if [ ! -f "$FINANCE_SCRIPT" ]; then
  echo "❌ Error: Finance script not found at $FINANCE_SCRIPT"
  exit 1
fi

# 4. Check if demo-app has node_modules
if [ ! -d "$DEMO_APP_DIR/node_modules" ]; then
  echo "⚠️ Warning: 'node_modules' not found in demo-app. Running 'npm install'..."
  cd "$DEMO_APP_DIR" && npm install
  cd "$PROJECT_ROOT"
fi

echo "✅ Environment looks good. Starting app..."
cd "$DEMO_APP_DIR" && npm run dev
