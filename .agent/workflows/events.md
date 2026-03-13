---
description: Trigger event scraping and update events.md
---
# Workflow: /events

1. Open a terminal in the `Scripts` directory of your Obsidian vault:
   ```
   cd /Users/yichen/Obsidian/Scripts
   ```
2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```
3. Run the event scraper to refresh `events.md` with locations, driving info, and Google Maps links:
   ```
   python3 update_events.py
   ```
4. (Optional) Commit the updated `events.md` to version control:
   ```
   git add /Users/yichen/Obsidian/Dating/events.md
   git commit -m "Update events"
   ```

You can invoke this workflow manually by typing the slash command `/events` in your preferred interface that supports custom workflows.
