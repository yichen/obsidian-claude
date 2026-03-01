---
name: ninja-quest-calendar
description: "Query Ninja Quest Adventures calendar using Claude Code. Use when user asks about ninja quest schedules, open gym times, or when the next session is at specific locations (Issaquah, Northgate). Handles time-based queries like 'next Friday' or 'this weekend' by navigating the dynamic calendar."
metadata:
  {
    "openclaw": { "emoji": "🥷", "requires": { "anyBins": ["claude"] } },
  }
---

# Ninja Quest Calendar (Claude Code)

Use **Claude Code** to query the Ninja Quest Adventures calendar for open gym sessions, camps, and classes. Claude Code uses the browser tool directly for navigation and parsing.

## ⚠️ Browser Tool Required!

This skill requires Claude Code to have access to the browser tool for:
- Starting the browser
- Navigating to calendar URLs
- Taking snapshots
- Clicking navigation buttons

## Quick Start

```bash
# Simple query - tomorrow's schedule at Issaquah
claude "Check ninja quest calendar for tomorrow at Issaquah and show me all open gym sessions. Don't forget to remind me to bring albuterol for Laurence."

# Weekend schedule
claude "What open gym sessions are available this weekend at Issaquah? Include the albuterol reminder."

# Next weekend
claude "Find all open gym sessions for next weekend at Issaquah. Remember to remind me about albuterol."
```

## URLs

**Primary (Issaquah-only):** https://www.ninjaquestadventures.com/calendar/issaquah-calendar
**All locations:** https://www.ninjaquestadventures.com/calendar

## Workflow

### Step 1: Parse Query

Extract **day** and **location** from user's question:
- **Day:** tomorrow, today, weekend, next-weekend, Sunday, Monday, etc.
- **Location:** issaquah (default), northgate, all

### Step 2: Start Browser & Navigate

```javascript
browser tool: action="start", profile="openclaw"
browser tool: action="open", profile="openclaw", targetUrl="https://www.ninjaquestadventures.com/calendar/issaquah-calendar"
```

### Step 3: Extract Iframe URL

The calendar loads in an iframe. Extract it:

```javascript
browser tool: action="evaluate", profile="openclaw", fn="() => { const iframe = document.querySelector('main iframe'); return iframe ? iframe.getAttribute('src') : null; }"
```

### Step 4: Navigate to Iframe

```javascript
browser tool: action="open", profile="openclaw", targetUrl="<extracted_iframe_url>"
```

### Step 5: Navigate Forward (if needed)

For future dates (next-weekend, next-week):

```javascript
// Click forward arrow using JavaScript
browser tool: action="evaluate", profile="openclaw", fn="() => { const buttons = document.querySelectorAll('button'); for (let btn of buttons) { if (btn.textContent.includes('›')) { btn.click(); return true; } } return false; }"

// Wait for content to load, then take snapshot
browser tool: action="snapshot", profile="openclaw", format="ai"
```

### Step 6: Scroll & Capture

```javascript
browser tool: action="press", profile="openclaw", key="End"
// Wait for content to load
browser tool: action="snapshot", profile="openclaw", format="ai"
```

### Step 7: Parse & Filter

Extract Open Gym sessions from the snapshot:
- Look for rows containing "Open Gym" and "Issaquah"
- Filter by the target day column (Monday=1, Sunday=7)
- Extract time, activity name, and time range

### Step 8: Present Results

Format output clearly with:
- Week date range
- Day labels (Saturday, Sunday)
- Session times and names
- **Albuterol reminder for Laurence**

### Step 9: Cleanup

```javascript
browser tool: action="close", profile="openclaw"
```

## Common Queries

**"Tomorrow at Issaquah"**
```bash
claude "Show me open gym sessions for tomorrow at Issaquah. Remind me to bring albuterol for Laurence."
```

**"This weekend"**
```bash
claude "What open gym sessions are available this weekend at Issaquah? Don't forget the albuterol reminder."
```

**"Next weekend"**
```bash
claude "Find all open gym sessions for next weekend at Issaquah. Include albuterol reminder for Laurence."
```

**"Sunday"**
```bash
claude "Check ninja quest calendar for Sunday at Issaquah and show open gym times. Remind about albuterol."
```

## Output Format

```
📅 Open Gym - Tomorrow (Sunday) at Issaquah 24 Hr Fitness
Week: Feb 22 2026 - Feb 22 2026

• 4:30 PM - 5:25 PM: Open Gym - Ages (5-14)
• 5:30 PM - 6:25 PM: Open Gym - Ages (5-14)

Found 2 session(s)

🧴 Don't forget to bring albuterol for Laurence!
```

## Column Mapping

The calendar is a table with:
- **Column 1:** Time
- **Column 2-8:** Monday through Sunday

When parsing, count cells to identify the target day:
- Monday = column 2
- Tuesday = column 3
- Wednesday = column 4
- Thursday = column 5
- Friday = column 6
- Saturday = column 7
- Sunday = column 8

## Important Reminders for Laurence

Always remind Yi to bring albuterol (asthma inhaler) when presenting Ninja Quest sessions for Laurence.

## Tips

- Use AI snapshot format (`format="ai"`) for best parsing
- Scroll to bottom (`key="End"`) to capture all sessions
- Click forward arrow using JavaScript for reliable navigation
- Close browser tab after extracting results
- Albuterol reminder should be in every response