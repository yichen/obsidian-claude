import json
from playwright.sync_api import sync_playwright
import os

SESSION_FILE = '/Users/yichen/Obsidian/Scripts/fb_session.json'

def run():
    print("Launching browser for Facebook login...")
    print("1. The browser will open.")
    print("2. Please log in to Facebook manually.")
    print("3. Navigate to a group page to ensure you are fully logged in.")
    print("4. Close the browser window when you are done.")
    
    with sync_playwright() as p:
        # Launch headful browser so user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://www.facebook.com")
        
        # Wait for the user to close the browser (browser context close)
        # We loop and check if browser is still connected or page is closed
        try:
            print("Waiting for you to close the browser...")
            page.wait_for_event("close", timeout=0) # Wait indefinitely until page closes
        except Exception as e:
            pass # Page closed

        # Save storage state (cookies, local storage)
        context.storage_state(path=SESSION_FILE)
        print(f"Session saved to {SESSION_FILE}")
        browser.close()

if __name__ == "__main__":
    run()
