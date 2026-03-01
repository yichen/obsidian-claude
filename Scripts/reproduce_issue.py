import os
import datetime
from datetime import datetime as dt
import shutil
import sys

# Add Scripts to path
sys.path.append('/Users/chen.y/Obsidian/Scripts')
import update_events

# Mock data
TEST_EVENTS_FILE = "test_events.md"
update_events.EVENTS_FILE = TEST_EVENTS_FILE
update_events.TODAY = dt(2025, 11, 24).date()
update_events.CURRENT_YEAR = 2025

def create_test_file():
    content = """
> Last Updated: 2025-11-24 00:00:00

## Nov 24, Monday

*   **[Manual] My Manual Event**
    *   **Time:** 10:00 AM
    *   **Loc:** Somewhere
    *   **Link:** https://manual.com/event

## Nov 25, Tuesday

*   **[FB] Existing Scraped Event**
    *   **Time:** 11:00 AM
    *   **Link:** https://fb.com/event1

## Flexible / Upcoming / Date Unknown

*   **[Manual] Flexible Manual Event**
    *   **Link:** https://manual.com/flex
"""
    with open(TEST_EVENTS_FILE, 'w') as f:
        f.write(content)

def mock_fetch_latin():
    return []

def mock_fetch_fb():
    return [
        (dt(2025, 11, 25).date(), "*   **[FB] New Scraped Event**\n    *   **Time:** 12:00 PM\n    *   **Link:** https://fb.com/event2\n")
    ]

# Monkey patch
update_events.fetch_latin_dance_events = mock_fetch_latin
update_events.fetch_facebook_events = mock_fetch_fb

def run_test():
    create_test_file()
    print("Initial file created.")
    
    print("Running update...")
    update_events.update_events_file()
    
    print("\nChecking results...")
    with open(TEST_EVENTS_FILE, 'r') as f:
        content = f.read()
        
    print(content)
    
    failures = []
    if "[Manual] My Manual Event" not in content:
        failures.append("Manual dated event was lost!")
    if "[Manual] Flexible Manual Event" not in content:
        failures.append("Manual flexible event was lost!")
    if "[FB] New Scraped Event" not in content:
        failures.append("New scraped event was not added!")
        
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"- {f}")
    else:
        print("\nSUCCESS: All events present.")

    # Cleanup
    if os.path.exists(TEST_EVENTS_FILE):
        os.remove(TEST_EVENTS_FILE)

if __name__ == "__main__":
    run_test()
