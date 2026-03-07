# /salsa — Find Latin Dance Events Near You

## Overview
Query the local Latin dance events registry and return filtered, formatted results with drive times from home (Sammamish).

## Input
$ARGUMENTS

## Data Source
Read the event registry at `/Users/ychen2/Obsidian/Life/salsa/events-registry.yaml`. This contains all known recurring Latin dance events in the Seattle area with pre-geocoded lat/lon coordinates.

## Subcommands

### Default (no arguments or day/time/location query)
Show all active events for the **next 7 days**, grouped by day, sorted by start_time within each day.

### `refresh`
1. WebFetch `https://golatindance.com/events/category/seattle/` — extract all events with name, day, time, venue, address
2. Compare against the registry:
   - **Matched**: Update `last_confirmed` date
   - **New** (on website but not in registry): Report to user, suggest adding
   - **Missing** (in registry but not on website): Flag as possibly cancelled/paused
3. Write updated YAML back to the registry file

### `add`
Interactive: ask user for event details (name, day, time, venue, address, style). Geocode the address via Nominatim (`https://nominatim.openstreetmap.org/search?q=ADDRESS&format=json&limit=1`). Add to registry YAML.

## Filtering Logic

Parse natural language from $ARGUMENTS. Apply filters with AND logic:

### Day Filter
- "today", "tonight" → current day of week
- "tomorrow" → next day
- "this Saturday", "next Monday" → specific day
- "this weekend" → Friday + Saturday + Sunday
- "next week" → Monday through Sunday of the following week
- No day specified → next 7 days

### Time Filter
- "before 9pm" → start_time < 21:00
- "after 8pm" → start_time >= 20:00
- "early evening" → start_time < 20:00
- "late night" → start_time >= 22:00

### Location Filter
Use Haversine distance formula: `d = 2R * arcsin(sqrt(sin²((lat2-lat1)/2) + cos(lat1)*cos(lat2)*sin²((lon2-lon1)/2)))` where R = 3959 miles.

- **"near X"** → compute distance from X to each event, show events within 20 miles sorted by proximity
- **"between A and B"** → compute midpoint of A and B, sort events by distance from midpoint
- **"in Seattle"** → filter where address contains "Seattle" (string match)

Use the `reference_locations` block in the YAML for city coordinates. If a location isn't in the reference list, try to geocode it via Nominatim WebFetch.

### Style Filter
- "salsa" → filter events where style array includes "salsa"
- "bachata" → filter events where style array includes "bachata"
- "zouk", "kizomba" → same pattern

### Frequency Filter
- By default, show ALL events regardless of frequency
- For non-weekly events (monthly, bimonthly), add a note about the schedule in the output
- If the user asks about a specific date, check if a monthly/bimonthly event actually occurs on that date

## Drive Time

For each event in the results, fetch drive time from home using OSRM:
```
https://router.project-osrm.org/route/v1/driving/{home_lon},{home_lat};{event_lon},{event_lat}?overview=false
```

Extract `routes[0].duration` (seconds) → convert to minutes. Extract `routes[0].distance` (meters) → convert to miles.

**Important**: Make OSRM calls sequentially (1 at a time) to respect rate limits. Only fetch drive times for events in the final filtered result set (not all 19 events).

## Output Format

Group events by day. Within each day, sort by start_time. Use a markdown table:

```markdown
### Saturday, Mar 8

| Time | Event | Venue | City | Drive | Style | Cost |
|------|-------|-------|------|-------|-------|------|
| 7:00-9:00 PM | [Live Salsa Saturdays](https://maps.google.com/?q=47.6615,-122.3323) | Sea Monster Lounge | Seattle | 28 min | salsa | - |
| 8:30 PM-1:30 AM | [AVS Vinyl Salsa Night](https://maps.google.com/?q=47.6150,-122.3198) | Reverie Ballroom | Seattle | 25 min | salsa | - |
```

- **Event name** links to Google Maps at the venue's lat/lon
- **Drive** column shows drive time in minutes from home
- **Cost** shows entry fee or `-` if unknown/free
- For non-weekly events, append frequency note after the event name (e.g., "2nd Thu only")

## Notes
- Today's date for day-of-week calculations: use the current date from context
- All times are in Pacific Time
- Events with `status: paused` or `status: cancelled` are excluded unless user specifically asks
- If no events match the filters, say so and suggest broadening the search
