---
name: ninja-quest-calendar-claude-code
description: "Query Ninja Quest Adventures calendar using Claude Code only (no OpenClaw dependencies). Use when user asks about ninja quest schedules, open gym times, or when the next session is at specific locations (Issaquah, Northgate). Handles time-based queries like 'next Friday' or 'this weekend'."
metadata:
  {
    "openclaw": { "emoji": "🥷", "requires": { "anyBins": ["claude"] } },
  }
---

# Ninja Quest Calendar (Claude Code - Standalone)

Use **Claude Code only** (no OpenClaw) to query the Ninja Quest Adventures calendar. This version uses Puppeteer for browser automation.

## Quick Start

```bash
# Simple query - tomorrow's schedule at Issaquah
claude "Check ninja quest calendar for tomorrow at Issaquah and show me all open gym sessions. Don't forget to remind me to bring albuterol for Laurence."

# Weekend schedule
claude "What open gym sessions are available this weekend at Issaquah? Include the albuterol reminder."

# Next weekend
claude "Find all open gym sessions for next weekend at Issaquah. Remember to remind me about albuterol."
```

## Prerequisites

Install Puppeteer:
```bash
npm install puppeteer
```

Or use globally:
```bash
npm install -g puppeteer
```

## Workflow

### Step 1: Parse Query

Extract **day** and **location** from user's question:
- **Day:** tomorrow, today, weekend, next-weekend, Sunday, Monday, etc.
- **Location:** issaquah (default), northgate, all

### Step 2: Create Node.js Script

Write a Node.js script using Puppeteer that:

```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  // Navigate to calendar
  await page.goto('https://www.ninjaquestadventures.com/calendar/issaquah-calendar');

  // Extract iframe URL
  const iframeUrl = await page.evaluate(() => {
    const iframe = document.querySelector('main iframe');
    return iframe ? iframe.getAttribute('src') : null;
  });

  // Navigate to iframe
  await page.goto(iframeUrl);

  // Click forward if needed (for next-weekend, etc.)
  if (needsFutureWeek) {
    await page.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      for (let btn of buttons) {
        if (btn.textContent.includes('›')) {
          btn.click();
          break;
        }
      }
    });
    await page.waitForTimeout(2000);
  }

  // Scroll to bottom
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);

  // Get HTML content
  const html = await page.content();

  // Parse calendar data
  const sessions = await page.evaluate(() => {
    const rows = document.querySelectorAll('table tr');
    const results = [];
    
    rows.forEach(row => {
      const text = row.textContent;
      if (text.includes('Open Gym') && text.includes('Issaquah')) {
        results.push(text);
      }
    });
    
    return results;
  });

  await browser.close();
  console.log(JSON.stringify(sessions, null, 2));
})();
```

### Step 3: Parse Results

Filter sessions by target day:
- Look for day name in the row context
- Extract time and session details
- Match against the requested day

### Step 4: Present Results

Format output clearly with:
- Week date range
- Day labels (Saturday, Sunday)
- Session times and names
- **Albuterol reminder for Laurence**

## Example Implementation

```javascript
// ninja-quest-calendar.js
const puppeteer = require('puppeteer');

const getNinjaQuestSchedule = async (day, location = 'issaquah') => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  try {
    // Navigate to calendar
    await page.goto('https://www.ninjaquestadventures.com/calendar/issaquah-calendar');
    await page.waitForSelector('main iframe', { timeout: 10000 });

    // Extract iframe URL
    const iframeUrl = await page.evaluate(() => {
      const iframe = document.querySelector('main iframe');
      return iframe ? iframe.getAttribute('src') : null;
    });

    if (!iframeUrl) {
      throw new Error('Could not extract iframe URL');
    }

    // Navigate to iframe
    await page.goto(iframeUrl);
    await page.waitForSelector('table', { timeout: 10000 });

    // Click forward for future weeks
    const weeksAhead = calculateWeeksAhead(day);
    for (let i = 0; i < weeksAhead; i++) {
      await page.evaluate(() => {
        const buttons = document.querySelectorAll('button');
        for (let btn of buttons) {
          if (btn.textContent.includes('›')) {
            btn.click();
            return true;
          }
        }
      });
      await page.waitForTimeout(2000);
    }

    // Scroll to load all content
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);

    // Extract sessions
    const sessions = await page.evaluate((targetDay) => {
      const dayMap = {
        'sunday': 7,
        'monday': 1,
        'tuesday': 2,
        'wednesday': 3,
        'thursday': 4,
        'friday': 5,
        'saturday': 6
      };

      const rows = document.querySelectorAll('table tbody tr');
      const results = [];
      
      rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const targetCol = dayMap[targetDay] || dayMap['sunday'];
        
        if (cells.length > targetCol) {
          const cell = cells[targetCol - 1]; // -1 for 0-indexed
          const text = cell.textContent.trim();
          
          if (text.includes('Open Gym') && text.includes('Issaquah')) {
            results.push(text);
          }
        }
      });
      
      return results;
    }, day);

    await browser.close();
    return sessions;

  } catch (error) {
    await browser.close();
    throw error;
  }
};

// Helper function
const calculateWeeksAhead = (day) => {
  if (day === 'next-weekend') return 1;
  if (day === 'weekend-after-next') return 2;
  return 0;
};

// Main execution
const day = process.argv[2] || 'tomorrow';
const location = process.argv[3] || 'issaquah';

getNinjaQuestSchedule(day, location)
  .then(sessions => {
    console.log('📅 Results:');
    console.log('================================');
    sessions.forEach(session => {
      console.log(`• ${session}`);
    });
    console.log('');
    console.log(`Found ${sessions.length} session(s)`);
    console.log('');
    console.log('🧴 Don\'t forget to bring albuterol for Laurence!');
  })
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
```

## Usage

Run the script:
```bash
node ninja-quest-calendar.js tomorrow issaquah
node ninja-quest-calendar.js next-weekend issaquah
node ninja-quest-calendar.js weekend issaquah
```

## Output Format

```
📅 Results:
================================
• Open Gym - Ages (5-14) Issaquah 24 Hr Fitness 4:30 PM - 5:25 PM
• Open Gym - Ages (5-14) Issaquah 24 Hr Fitness 5:30 PM - 6:25 PM

Found 2 session(s)

🧴 Don't forget to bring albuterol for Laurence!
```

## Important Reminders for Laurence

Always remind Yi to bring albuterol (asthma inhaler) when presenting Ninja Quest sessions for Laurence.

## Tips

- Use `headless: 'new'` for better Puppeteer performance
- Add `--no-sandbox` flag if running in restricted environments
- Increase timeout for slower network connections
- Parse sessions carefully - filter by location text
- Always include albuterol reminder in output