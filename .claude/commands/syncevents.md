---
description: Sync events by scraping Facebook and Latin dance schedule
---

Synchronize events from Facebook groups and Latin dance websites by running the event sync script.

**Process:**
1. Run the Python script at `Scripts/update_events.py` using the system Python 3
2. The script will:
   - Fetch Latin dance events from golatindance.com
   - Scrape Facebook events from hiking/singles groups (if session is valid)
   - Merge new events into `events.md` in the root folder
   - Add driving times and Google Maps links from Sammamish home
   - Skip duplicates and past events automatically
3. Report how many new events were added

**Command to execute:**
Run `python3 Scripts/update_events.py` from the Obsidian root directory.

**Note:** The script uses relative paths so it works across all synced computers.
