#!/bin/bash
# Ninja Quest Calendar Script
# Usage: ./scripts/ninja-quest-calendar.sh [day] [location]
#   day: "tomorrow", "today", "weekend", "next-weekend", or day name
#   location: "issaquah" (default) or "northgate"

set -e

# Configuration
ISSAQUAH_URL="https://www.ninjaquestadventures.com/calendar/issaquah-calendar"
ALL_URL="https://www.ninjaquestadventures.com/calendar"
DEFAULT_LOCATION="issaquah"

# Parse arguments
DAY_QUERY="${1:-tomorrow}"
LOCATION="${2:-$DEFAULT_LOCATION}"

# Normalize location
case "$LOCATION" in
  issaquah|isaq|iss)
    LOCATION="issaquah"
    URL="$ISSAQUAH_URL"
    ;;
  northgate|north|ng)
    LOCATION="northgate"
    URL="$ALL_URL"
    ;;
  all|*)
    LOCATION="all"
    URL="$ALL_URL"
    ;;
esac

# Get current day of week (0=Sunday, 1=Monday, etc.)
CURRENT_DAY=$(date +%u)
CURRENT_DAY_NAME=$(date +%A)

# Check for multi-day queries
MULTI_DAY=false
SATURDAY_COL=""
SUNDAY_COL=""

# Map day query to target day(s)
TARGET_DAY=""
TARGET_DAY_NAME=""
case "$DAY_QUERY" in
  tomorrow|tmrw|tom)
    TARGET_DAY=$(( (CURRENT_DAY % 7) + 1 ))
    TARGET_DAY_NAME=$(date -v+1d +%A 2>/dev/null || date -d "tomorrow" +%A)
    ;;
  today|tdy)
    TARGET_DAY=$CURRENT_DAY
    TARGET_DAY_NAME=$CURRENT_DAY_NAME
    ;;
  weekend|this-weekend)
    MULTI_DAY=true
    SATURDAY_COL=6
    SUNDAY_COL=7
    TARGET_DAY_NAME="This Weekend (Saturday + Sunday)"
    ;;
  next-weekend)
    MULTI_DAY=true
    SATURDAY_COL=6
    SUNDAY_COL=7
    TARGET_DAY_NAME="Next Weekend (Saturday + Sunday)"
    ;;
  sunday|sun)
    TARGET_DAY=0
    TARGET_DAY_NAME="Sunday"
    ;;
  monday|mon)
    TARGET_DAY=1
    TARGET_DAY_NAME="Monday"
    ;;
  tuesday|tue)
    TARGET_DAY=2
    TARGET_DAY_NAME="Tuesday"
    ;;
  wednesday|wed)
    TARGET_DAY=3
    TARGET_DAY_NAME="Wednesday"
    ;;
  thursday|thu)
    TARGET_DAY=4
    TARGET_DAY_NAME="Thursday"
    ;;
  friday|fri)
    TARGET_DAY=5
    TARGET_DAY_NAME="Friday"
    ;;
  saturday|sat)
    TARGET_DAY=6
    TARGET_DAY_NAME="Saturday"
    ;;
  *)
    TARGET_DAY=$CURRENT_DAY
    TARGET_DAY_NAME="$DAY_QUERY"
    ;;
esac

# Convert 0=Sunday to 7 for column position (Monday=1, ..., Sunday=7)
if [ "$MULTI_DAY" = false ]; then
  COLUMN_POS=$((TARGET_DAY == 0 ? 7 : TARGET_DAY))
else
  COLUMN_POS=0  # Not used for multi-day
fi

echo "🥷 Ninja Quest Calendar - Location: $LOCATION"
echo "Target day: $TARGET_DAY_NAME"
echo ""

# Step 1: Start browser
echo "Starting browser..."
openclaw browser start --browser-profile openclaw --expect-final > /dev/null 2>&1 || true

# Step 2: Open calendar URL
echo "Opening calendar..."
openclaw browser open "$URL" --browser-profile openclaw --expect-final --json | jq -r '.tabs[0].targetId' > /tmp/nq_tab_id.txt
TAB_ID=$(cat /tmp/nq_tab_id.txt)

# Wait for page load
sleep 2

# Step 3: Extract iframe URL
echo "Extracting iframe URL..."
IFRAME_URL=$(openclaw browser evaluate --browser-profile openclaw --fn '() => { const iframe = document.querySelector("main iframe"); return iframe ? iframe.getAttribute("src") : null; }' --json | jq -r '.result')

if [ "$IFRAME_URL" = "null" ] || [ -z "$IFRAME_URL" ]; then
  echo "❌ Failed to extract iframe URL"
  exit 1
fi

echo "Iframe URL: $IFRAME_URL"

# Step 4: Navigate directly to iframe URL
echo "Navigating to iframe..."
openclaw browser open "$IFRAME_URL" --browser-profile openclaw --expect-final --json | jq -r '.tabs[0].targetId' > /tmp/nq_tab_id.txt
TAB_ID=$(cat /tmp/nq_tab_id.txt)

# Wait for content load
sleep 3

# Step 5: Check if we need to navigate to future dates
NAVIGATE_FORWARD=false
WEEKS_AHEAD=0

# Calculate target date and weeks to navigate
case "$DAY_QUERY" in
  next-weekend|next-week)
    NAVIGATE_FORWARD=true
    WEEKS_AHEAD=1
    ;;
  next-weekend-week|weekend-after-next)
    NAVIGATE_FORWARD=true
    WEEKS_AHEAD=2
    ;;
esac

if [ "$NAVIGATE_FORWARD" = true ]; then
  echo "Navigating $WEEKS_AHEAD week(s) ahead..."

  # Click forward button using JavaScript for reliability
  for i in $(seq 1 $WEEKS_AHEAD); do
    echo "  - Clicking forward ($i/$WEEKS_AHEAD)..."
    openclaw browser evaluate --browser-profile openclaw --fn '() => { const buttons = document.querySelectorAll("button"); for (let btn of buttons) { if (btn.textContent.includes("›")) { btn.click(); return true; } } return false; }' --expect-final > /dev/null 2>&1
    sleep 2
  done

  # Scroll to load all sessions for the target week
  for j in {1..5}; do
    openclaw browser press --browser-profile openclaw PageDown --expect-final > /dev/null 2>&1
    sleep 1
  done
  openclaw browser press --browser-profile openclaw End --expect-final > /dev/null 2>&1
  sleep 2

  # Take snapshot of the target week
  echo "Capturing calendar..."
  SNAPSHOT=$(openclaw browser snapshot --browser-profile openclaw --format ai --json --limit 2000 --expect-final)
  echo "$SNAPSHOT" > /tmp/nq_snapshot.json
  echo "$SNAPSHOT" | jq -r '.snapshot' > /tmp/nq_snapshot_text.txt
else
  # Scroll to load all sessions (for current week)
  echo "Loading all sessions..."
  for i in {1..5}; do
    openclaw browser press --browser-profile openclaw PageDown --expect-final > /dev/null 2>&1
    sleep 1
  done
  openclaw browser press --browser-profile openclaw End --expect-final > /dev/null 2>&1
  sleep 2

  # Take snapshot
  echo "Capturing calendar..."
  SNAPSHOT=$(openclaw browser snapshot --browser-profile openclaw --format ai --json --limit 2000 --expect-final)

  # Save snapshot for debugging
  echo "$SNAPSHOT" > /tmp/nq_snapshot.json
  echo "$SNAPSHOT" | jq -r '.snapshot' > /tmp/nq_snapshot_text.txt
fi

# Step 7: Parse sessions for target day
echo ""
echo "📅 Results:"
echo "================================"
echo ""

# Extract week range
WEEK_RANGE=$(echo "$SNAPSHOT" | jq -r '.snapshot' 2>/dev/null | grep -oE 'Feb [0-9]{2} 2026 - Feb [0-9]{2} 2026' | head -1)
echo "📅 Open Gym - $TARGET_DAY_NAME at Issaquah 24 Hr Fitness"
echo "Week: $WEEK_RANGE"
echo ""

# Use Python for reliable column extraction
SESSIONS=$(python3 -c "
import re
import sys

multi_day = '$MULTI_DAY' == 'true'
saturday_col = int('$SATURDAY_COL') + 1 if multi_day else 0
sunday_col = int('$SUNDAY_COL') + 1 if multi_day else int('$COLUMN_POS') + 1

with open('/tmp/nq_snapshot_text.txt', 'r') as f:
    content = f.read()

# Find all rows and extract the target column cell(s)
lines = content.split('\n')
in_row = False
cell_count = 0

for i, line in enumerate(lines):
    if 'row \"' in line and ('Open Gym' in line or '12:00 PM' in line or '02:00 PM' in line or '03:00 PM' in line or '04:30 PM' in line):
        in_row = True
        cell_count = 0
        continue

    if in_row:
        if '- cell' in line:
            cell_count += 1
            # Check if this cell matches any of our target columns
            target_cols = [sunday_col] if not multi_day else [saturday_col, sunday_col]
            if cell_count in target_cols:
                # Extract cell content if it exists
                match = re.search(r'- cell \"([^\"]+)\"', line)
                if match:
                    cell_content = match.group(1)
                    if 'Open Gym' in cell_content and 'Issaquah' in cell_content:
                        # Add day label for multi-day
                        if multi_day:
                            day_label = 'Saturday' if cell_count == saturday_col else 'Sunday'
                            print(f'{day_label}: {cell_content}')
                        else:
                            print(cell_content)
        elif cell_count >= (max(target_cols) if multi_day else sunday_col):
            in_row = False
" 2>/dev/null)

if [ -z "$SESSIONS" ]; then
  echo "No Open Gym sessions found for $TARGET_DAY_NAME at Issaquah"
else
  echo "$SESSIONS" | sort | uniq | while read -r line; do
    echo "• $line"
  done
  echo ""
  echo "Found $(echo "$SESSIONS" | sort | uniq | wc -l) session(s)"
fi

echo ""
echo "================================"
echo "🧴 Don't forget to bring albuterol for Laurence!"
echo ""

# Step 8: Close browser tab
echo "Closing browser tab..."
openclaw browser close --browser-profile openclaw --expect-final > /dev/null 2>&1 || true
echo ""