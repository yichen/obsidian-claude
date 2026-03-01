import os
import re
import datetime
from datetime import datetime as dt, timedelta
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from playwright.sync_api import sync_playwright

# Configuration
EVENTS_FILE = "/Users/yichen/Obsidian/Dating/events.md"
SESSION_FILE = '/Users/yichen/Obsidian/Scripts/fb_session.json'
TODAY = dt.now().date()
CURRENT_YEAR = TODAY.year

# Home Coordinates (Sammamish)
HOME_LAT = 47.5839052
HOME_LON = -121.9964883
geolocator = Nominatim(user_agent="pnw_event_updater")

# --- Helper Functions ---

def get_drive_estimates(destination):
    """
    Calculates driving time and distance from Home to Destination.
    Uses Nominatim for geocoding and OSRM for routing.
    """
    if not destination or len(destination) < 3:
        return None

    try:
        # 1. Geocode Destination
        # Add 'WA' if not present to bias towards local results
        search_query = destination if "WA" in destination else f"{destination}, WA"
        loc = geolocator.geocode(search_query)
        if not loc:
            return None
        
        # 2. Get Route from OSRM
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{HOME_LON},{HOME_LAT};{loc.longitude},{loc.latitude}?overview=false"
        
        resp = requests.get(osrm_url, timeout=5)
        data = resp.json()
        
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            duration_sec = route["duration"]
            distance_meters = route["distance"]
            
            # Convert to readable format
            hours = int(duration_sec // 3600)
            minutes = int((duration_sec % 3600) // 60)
            miles = round(distance_meters * 0.000621371, 1)
            
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            return f"{time_str} ({miles} miles)"
            
    except Exception as e:
        # print(f"Error calculating drive time for {destination}: {e}")
        pass
    
    return None

def get_google_maps_link(address, home_address="2807 257th Pl SE, Sammamish, WA 98075"):
    """
    Generates a Google Maps directions link from home to destination.
    Returns None if address is invalid.
    """
    if not address or len(address) < 3:
        return None
    
    import urllib.parse
    encoded_home = urllib.parse.quote(home_address)
    encoded_dest = urllib.parse.quote(address)
    return f"https://www.google.com/maps/dir/{encoded_home}/{encoded_dest}"

def parse_date_str(date_str):
    """
    Parses a date string like 'Nov 23, Sunday' or '## Nov 23, Sunday' or 'November 23 @ 6:00 pm' and returns a datetime.date object.
    Returns None if the string doesn't match expected patterns.
    """
    # Remove markdown header if present
    date_str = date_str.replace("##", "").strip()
    
    # Try to match full month name first (e.g., "November 23 @ 6:00 pm")
    match = re.search(r'([A-Za-z]+)\s+(\d{1,2})\s*@', date_str)
    if match:
        month_str = match.group(1)
        day_str = match.group(2)
        try:
            # Try full month name
            date_obj = dt.strptime(f"{month_str} {day_str} {CURRENT_YEAR}", "%B %d %Y").date()
            return date_obj
        except:
            pass
    
    # Try to match "Nov 23, Sunday" or "Nov 23"
    match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})', date_str)
    if match:
        month_str = match.group(1)
        day_str = match.group(2)
        try:
            date_obj = dt.strptime(f"{month_str} {day_str} {CURRENT_YEAR}", "%b %d %Y").date()
            return date_obj
        except:
            pass
    
    return None

def get_event_time(event_md):
    """
    Extracts time from event markdown string.
    Returns a datetime.time object for sorting, or 23:59 if no time found.
    """
    # Look for **Time:** field
    time_match = re.search(r'\*\*Time:\*\*\s*(.+)', event_md)
    if not time_match:
        # No time found, return end of day for sorting
        return dt.strptime("23:59", "%H:%M").time()
    
    time_str = time_match.group(1).strip()
    
    # Parse various time formats
    # "9:00 AM", "9 AM", "19:00", "November 23 @ 6:00 pm - 8:30 pm"
    
    # Try "9:00 AM" or "9 AM"
    match = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)', time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3).upper()
        
        # Convert to 24-hour format
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
            
        return dt.strptime(f"{hour}:{minute}", "%H:%M").time()
    
    # Try "November 23 @ 6:00 pm"
    match = re.search(r'@\s*(\d{1,2}):(\d{2})\s*(am|pm)', time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3).upper()
        
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
            
        return dt.strptime(f"{hour}:{minute}", "%H:%M").time()
    
    # Default to end of day if can't parse
    return dt.strptime("23:59", "%H:%M").time()

def format_header_date(date_obj):
    """Returns string like '## Nov 23, Sunday'"""
    return f"## {date_obj.strftime('%b %d, %A')}"

# --- Scrapers ---

def fetch_latin_dance_events():
    """
    Fetches events from golatindance.com using Playwright.
    Returns list of tuples: (date_obj, event_markdown_string)
    """
    url = "https://golatindance.com/events/category/seattle/list/"
    print(f"Fetching Latin Dance events from {url}...")
    
    events = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            
            # Wait for events to load
            try:
                page.wait_for_selector('.tribe-events-calendar-list__event-row', timeout=10000)
            except:
                print("Timeout waiting for Latin events selector.")
                browser.close()
                return []
                
            event_rows = page.locator('.tribe-events-calendar-list__event-row').all()
            # print(f"DEBUG: Found {len(event_rows)} Latin event rows.")
            
            for row in event_rows:
                try:
                    title_tag = row.locator('.tribe-events-calendar-list__event-title-link')
                    if title_tag.count() == 0: continue
                    title = title_tag.inner_text().strip()
                    link = title_tag.get_attribute('href')
                    
                    time_tag = row.locator('.tribe-events-calendar-list__event-datetime')
                    date_str = time_tag.inner_text().strip() if time_tag.count() > 0 else ""
                    
                    # Parse Date
                    date_obj = parse_date_str(date_str)
                    
                    # Venue
                    venue_name = ""
                    venue_addr = ""
                    if row.locator('.tribe-events-calendar-list__event-venue-title').count() > 0:
                        venue_name = row.locator('.tribe-events-calendar-list__event-venue-title').inner_text().strip()
                    if row.locator('.tribe-events-calendar-list__event-venue-address').count() > 0:
                        venue_addr = row.locator('.tribe-events-calendar-list__event-venue-address').inner_text().strip()
                    
                    # Clean address
                    parts = [p.strip() for p in venue_addr.split(',')]
                    seen = set()
                    clean_parts = []
                    for p in parts:
                        if p not in seen:
                            clean_parts.append(p)
                            seen.add(p)
                    clean_addr = ", ".join(clean_parts)
                    location_str = f"{venue_name}, {clean_addr}".strip(', ')
                    
                    # Drive Time and Google Maps Link
                    drive_time_str = ""
                    maps_link = ""
                    
                    if clean_addr:
                        drive_time = get_drive_estimates(clean_addr)
                        if drive_time:
                            drive_time_str = f"    *   **Drive:** {drive_time}\n"
                        
                        maps_url = get_google_maps_link(clean_addr)
                        if maps_url:
                            maps_link = f"    *   **Directions:** [Google Maps]({maps_url})\n"

                    event_md = f"*   **[Latin] {title}**\n    *   **Time:** {date_str}\n    *   **Loc:** {location_str}\n{drive_time_str}{maps_link}    *   **Link:** {link}\n"
                    
                    events.append((date_obj, event_md))
                    
                except Exception as e:
                    print(f"Error parsing latin event row: {e}")
                    continue
            
            browser.close()
                
    except Exception as e:
        print(f"Error fetching Latin events with Playwright: {e}")
        
    return events

def fetch_facebook_events():
    """
    Scrapes FB events. 
    Returns list of tuples: (date_obj, event_markdown_string) and a flag indicating session issues.
    """
    session_issue = False

    if not os.path.exists(SESSION_FILE):
        print("No FB session found.")
        session_issue = True
        return [], session_issue

    FACEBOOK_GROUP_URLS = [
        # "https://www.facebook.com/groups/seattlehiking/", # Unmaintained
        "https://www.facebook.com/groups/2137924416462354/events", # Single Hikers of PNW
        "https://www.facebook.com/groups/40plussinglehikerspnw/events",
        "https://www.facebook.com/groups/326664065609590/events", # PNW Singles Camping
    ]

    events = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=SESSION_FILE)
            page = context.new_page()
            
            # Validate session on first URL
            try:
                page.goto(FACEBOOK_GROUP_URLS[0], timeout=15000)
                if "login" in page.url:
                    print("FB Session expired.")
                    browser.close()
                    return [], True
            except:
                pass

            for group_url in FACEBOOK_GROUP_URLS:
                events_url = group_url if "events" in group_url else f"{group_url.rstrip('/')}/events"
                print(f"Scraping FB: {events_url}")
                
                try:
                    page.goto(events_url, timeout=20000)
                    page.wait_for_load_state("domcontentloaded")
                    
                    # Get Group Name
                    title = page.title()
                    group_name = re.sub(r'\(\d+\)\s*', '', title).split('|')[0].replace("Events", "").replace("Facebook", "").strip()
                    if len(group_name) > 60: group_name = "FB Group"

                    # Find all event cards
                    # This is tricky as FB structure changes. We look for links with /events/ in them
                    # and try to find date context.
                    
                    # Strategy: Get all links, check if they look like event links
                    links = page.locator('a[href*="/events/"]').all()
                    
                    seen_urls = set()
                    
                    for link in links:
                        href = link.get_attribute('href')
                        text = link.inner_text().strip()
                        
                        if not href or "/events/" not in href: continue
                        
                        clean_url = "https://www.facebook.com" + href.split('?')[0] if href.startswith('/') else href.split('?')[0]
                        if clean_url in seen_urls or clean_url.endswith("/events"): continue
                        
                        # Try to get date/title from grandparent text
                        # This handles cases where the link is just a wrapper and date is in a sibling/parent
                        try:
                            grandparent_text = link.locator('xpath=../..').inner_text()
                        except:
                            grandparent_text = ""
                            
                        date_obj = None
                        event_title = text
                        event_time = None
                        
                        # Parse Grandparent Text
                        # Format often: "Sat, Nov 15\nEvent Title\n..." or "Today at 9 AM\nEvent Title\n..."
                        lines = grandparent_text.split('\n')
                        if len(lines) > 0:
                            possible_date = lines[0].strip()
                            # Check for date patterns
                            try:
                                upper_date = possible_date.upper()
                                
                                # Extract time if present (e.g., "Today at 9 AM", "Wed, Nov 26 at 12 PM")
                                time_match = re.search(r'at\s+(\d{1,2}(?::\d{2})?\s*(?:AM|PM))', possible_date, re.IGNORECASE)
                                if time_match:
                                    event_time = time_match.group(1).strip()
                                
                                if "TODAY" in upper_date:
                                    date_obj = TODAY
                                elif "TOMORROW" in upper_date:
                                    date_obj = TODAY + timedelta(days=1)
                                else:
                                    # Try "Sat, Nov 15" or "Wed, Nov 26 at 12 PM"
                                    # Remove day name if present
                                    # Regex to match "Mon, Sep 22" or "Sep 22"
                                    match = re.search(r'([A-Za-z]{3}),\s+([A-Za-z]{3})\s+(\d+)', possible_date)
                                    if match:
                                        # matched "Sat, Nov 15"
                                        month_str = match.group(2)
                                        day_str = match.group(3)
                                        date_obj = dt.strptime(f"{month_str} {day_str} {CURRENT_YEAR}", "%b %d %Y").date()
                                    else:
                                         # Try just "Nov 15"
                                        match = re.search(r'([A-Za-z]{3})\s+(\d+)', possible_date)
                                        if match:
                                            month_str = match.group(1)
                                            day_str = match.group(2)
                                            date_obj = dt.strptime(f"{month_str} {day_str} {CURRENT_YEAR}", "%b %d %Y").date()
                                
                                # If we found a date, the title is likely the next line
                                if date_obj:
                                    if len(lines) > 1:
                                        event_title = lines[1].strip()
                                    elif not event_title:
                                        event_title = "Unknown Title"
                                        
                                    # Handle year rollover (if date is Jan/Feb and we are in Nov/Dec)
                                    if date_obj.month < TODAY.month and (TODAY.month - date_obj.month) > 6:
                                        date_obj = date_obj.replace(year=CURRENT_YEAR + 1)
                                    elif date_obj.month > TODAY.month and (date_obj.month - TODAY.month) > 6:
                                        # Unlikely but possible if scraping old events? 
                                        # Actually if we scrape "Jan" in "Dec", it's next year.
                                        pass
                                        
                            except Exception as e:
                                pass

                        if not event_title: continue # Skip if we still have no title
                        
                        seen_urls.add(clean_url)

                        # Extract location by visiting the event page
                        event_location = ""
                        try:
                            # Navigate to event page to get location
                            event_page = context.new_page()
                            event_page.goto(clean_url, timeout=15000)
                            event_page.wait_for_load_state("domcontentloaded")
                            
                            # Try multiple selectors for location
                            # Facebook uses different selectors for location
                            location_selectors = [
                                'text=/.*,.*WA.*/i',  # Regex to find text with "WA" (Washington)
                                '[aria-label*="location"]',
                                '[aria-label*="Location"]',
                            ]
                            
                            for selector in location_selectors:
                                try:
                                    loc_elem = event_page.locator(selector).first
                                    if loc_elem.count() > 0:
                                        loc_text = loc_elem.inner_text().strip()
                                        # Check if it looks like an address (contains WA or Washington)
                                        if 'WA' in loc_text or 'Washington' in loc_text:
                                            event_location = loc_text
                                            break
                                except:
                                    continue
                            
                            event_page.close()
                        except Exception as e:
                            print(f"Could not extract location for {clean_url}: {e}")

                        # Calculate driving info and generate Google Maps link
                        drive_time_str = ""
                        maps_link = ""
                        location_field = ""
                        
                        if event_location:
                            location_field = f"    *   **Loc:** {event_location}\n"
                            
                            drive_time = get_drive_estimates(event_location)
                            if drive_time:
                                drive_time_str = f"    *   **Drive:** {drive_time}\n"
                            
                            maps_url = get_google_maps_link(event_location)
                            if maps_url:
                                maps_link = f"    *   **Directions:** [Google Maps]({maps_url})\n"

                        event_md = f"*   **[FB] {event_title}**\n"
                        if event_time:
                            event_md += f"    *   **Time:** {event_time}\n"
                        event_md += location_field
                        event_md += drive_time_str
                        event_md += maps_link
                        event_md += f"    *   **Facebook Group:** {group_name}\n"
                        event_md += f"    *   **Link:** {clean_url}\n"
                        
                        events.append((date_obj, event_md))

                except Exception as e:
                    print(f"Error scraping group {group_url}: {e}")
            
            browser.close()
            
    except Exception as e:
        print(f"Playwright error: {e}")

    return events, session_issue

def fetch_wta_events():
    # Placeholder for WTA - keeping it simple for now as user prioritized Latin/FB
    return []

# --- Main Logic ---

def read_existing_events():
    """
    Reads events.md and parses it into a dictionary:
    { date_obj: [list_of_lines], 'unknown': [list_of_lines], 'header': [lines], 'sources': [lines] }
    """
    if not os.path.exists(EVENTS_FILE):
        return {'header': [], 'unknown': [], 'sources': []}
        
    with open(EVENTS_FILE, 'r') as f:
        lines = f.readlines()
        
    sections = {'header': [], 'unknown': [], 'sources': []}
    current_date = None
    current_section_lines = []
    
    # Header includes everything up to the first date section
    header_done = False
    skipping_section = False
    in_sources = False

    for line in lines:
        # Detect start of auto-generated sections to skip
        if line.strip().startswith("## New Events Found"):
            skipping_section = True
            # If we were building a section, save it
            if in_sources:
                sections['sources'].extend(current_section_lines)
            elif current_date:
                if current_date not in sections: sections[current_date] = []
                sections[current_date].extend(current_section_lines)
            elif not header_done:
                sections['header'] = current_section_lines
                header_done = True
            else:
                sections['unknown'].extend(current_section_lines)
            current_section_lines = []
            current_date = None
            continue
            
        if line.strip().startswith("## "):
            # New Header - stop skipping
            skipping_section = False
            
            if parse_date_str(line):
                # New Date Section
                if in_sources:
                    sections['sources'].extend(current_section_lines)
                    in_sources = False
                elif not header_done:
                    sections['header'] = current_section_lines
                    header_done = True
                elif current_date:
                    if current_date not in sections: sections[current_date] = []
                    sections[current_date].extend(current_section_lines)
                else:
                    # Was in unknown/flexible section
                    sections['unknown'].extend(current_section_lines)
                    
                current_date = parse_date_str(line)
                current_section_lines = [] 
            else:
                # Other headers (Flexible, Sources, etc)
                
                # Save previous section
                if in_sources:
                    sections['sources'].extend(current_section_lines)
                elif not header_done:
                    sections['header'] = current_section_lines
                    header_done = True
                elif current_date:
                    if current_date not in sections: sections[current_date] = []
                    sections[current_date].extend(current_section_lines)
                    current_date = None 
                else:
                    sections['unknown'].extend(current_section_lines)
                
                current_section_lines = []
                current_date = None
                
                # Check if it's "Sources Checked"
                if "Sources Checked" in line:
                    in_sources = True
                    current_section_lines = [line]
                elif "Date Unknown" in line or "Flexible" in line:
                    in_sources = False
                    # Don't keep the header line
                else:
                    # Unknown header
                    in_sources = False
                    current_section_lines = [line]

        else:
            if not skipping_section:
                current_section_lines.append(line)
            
    # Flush last section
    if not skipping_section:
        if in_sources:
            sections['sources'].extend(current_section_lines)
        elif current_date:
            if current_date not in sections: sections[current_date] = []
            sections[current_date].extend(current_section_lines)
        elif not header_done:
            sections['header'] = current_section_lines
        else:
            sections['unknown'].extend(current_section_lines)
        
    return sections

def update_events_file():
    print("Reading existing events...")
    sections = read_existing_events()
    
    # 1. Fetch New Events
    latin_events = fetch_latin_dance_events()
    print(f"Fetched {len(latin_events)} Latin events.")
    fb_events, fb_session_issue = fetch_facebook_events()
    print(f"Fetched {len(fb_events)} FB events.")
    
    all_new_events = latin_events + fb_events
    
    print(f"Found {len(all_new_events)} total new events.")
    
    # 2. Merge into Sections
    # We need to avoid duplicates. Check links.
    existing_links = set()
    
    # Helper to scan links in lines
    def scan_links(lines):
        for line in lines:
            if "**Link:**" in line:
                try:
                    link = line.split("**Link:**")[1].strip()
                    existing_links.add(link)
                except: pass

    scan_links(sections['header'])
    scan_links(sections['unknown'])
    scan_links(sections['sources']) # Scan sources too? Maybe not needed but safe.
    for k, v in sections.items():
        if isinstance(k, datetime.date):
            scan_links(v)
                
    added_count = 0
    for date_obj, event_md in all_new_events:
        # Extract link to check dup
        link_match = re.search(r'\*\*Link:\*\* (http[^\s]+)', event_md)
        if link_match:
            link = link_match.group(1).strip()
            if link in existing_links:
                print(f"Skipping duplicate: {link}")
                continue
            existing_links.add(link)
            
        if date_obj:
            if date_obj < TODAY: 
                print(f"Skipping past event: {date_obj}")
                continue 
            if date_obj not in sections:
                sections[date_obj] = []
            sections[date_obj].append(event_md)
            print(f"Added event to {date_obj}")
            added_count += 1
        else:
            # Date unknown
            sections['unknown'].append(event_md)
            print("Added event to Unknown")
            added_count += 1
            
    print(f"Merged {added_count} unique new events.")
    
    # 3. Write Back to File
    new_lines = []
    
    # Header
    # Update timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Filter out old Last Updated
    header_lines = [l for l in sections['header'] if not l.startswith("> Last Updated:")]

    def strip_fb_warning(lines):
        warning_marker = "> [!WARNING] **Facebook Session Expired**"
        if not any(l.startswith(warning_marker) for l in lines):
            return lines

        cleaned = []
        skip = False
        code_open = False

        for line in lines:
            if line.startswith(warning_marker):
                skip = True
                code_open = False
                continue

            if skip:
                # Skip until we close the warning's fenced code block
                if line.startswith("> ```"):
                    if code_open:
                        skip = False
                        code_open = False
                    else:
                        code_open = True
                continue

            cleaned.append(line)

        # Remove leading blank lines left behind
        while cleaned and cleaned[0].strip() == "":
            cleaned.pop(0)

        return cleaned

    header_lines = strip_fb_warning(header_lines)

    if fb_session_issue:
        warning_block = [
            "> [!WARNING] **Facebook Session Expired**\n",
            "> Please run the following to refresh your session:\n",
            "> ```bash\n",
            "> source scripts/venv/bin/activate\n",
            "> python3 scripts/setup_fb_auth.py\n",
            "> python3 scripts/update_events.py\n",
            "> ```\n",
            "\n",
        ]
        header_lines = warning_block + header_lines

    new_lines.append(f"> Last Updated: {timestamp}\n\n")
    new_lines.extend(header_lines)
    
    # Sorted Date Sections
    # Filter out past dates from existing sections too
    sorted_dates = sorted([d for d in sections.keys() if isinstance(d, datetime.date) and d >= TODAY])
    
    for date_obj in sorted_dates:
        new_lines.append(f"\n{format_header_date(date_obj)}\n\n")
        
        # Parse lines into complete event blocks
        # Each event starts with "*   **" and continues until the next event or end
        raw_lines = [l for l in sections[date_obj] if l.strip()]
        event_blocks = []
        current_block = ""
        
        for line in raw_lines:
            if line.startswith("*   **"):
                # Start of new event
                if current_block:
                    event_blocks.append(current_block)
                current_block = line
            else:
                # Continuation of current event
                current_block += line
        
        # Don't forget the last block
        if current_block:
            event_blocks.append(current_block)
        
        # Sort events by time
        event_blocks.sort(key=lambda event_md: get_event_time(event_md))
        
        # Write sorted events
        for block in event_blocks:
            new_lines.append(block)
            
    # Unknown / Flexible Section
    new_lines.append("\n## Flexible / Upcoming / Date Unknown\n\n")
    for l in sections['unknown']:
        if l.strip():
            new_lines.append(l.rstrip() + "\n")
            
    # Sources Checked Section
    if sections['sources']:
        # Ensure header is there if not in lines (it should be)
        # But we logic'd it to be in lines
        for l in sections['sources']:
             new_lines.append(l)
    else:
        new_lines.append("\n## Sources Checked\n")

    with open(EVENTS_FILE, 'w') as f:
        f.writelines(new_lines)
        
    print("Events file updated successfully.")

if __name__ == "__main__":
    update_events_file()
