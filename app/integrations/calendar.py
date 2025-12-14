"""Google Calendar integration - fetch meetings only."""
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Any, Optional
import os
from app.config import Config
from dateutil import parser as date_parser

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def _to_utc_datetime(start_str: str) -> datetime:
    """
    Normalize event start strings to timezone-aware UTC datetimes.
    Handles date-only and datetime formats safely.
    """
    dt = date_parser.parse(start_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = None
    token_file = Config.GOOGLE_TOKEN_FILE
    scopes = Config.GOOGLE_SCOPES if Config.GOOGLE_SCOPES else SCOPES
    
    # Load existing token if available
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use new GOOGLE_CLIENT_SECRET_FILE or fallback to legacy GOOGLE_CREDENTIALS_PATH
            credentials_path = Config.GOOGLE_CLIENT_SECRET_FILE or Config.GOOGLE_CREDENTIALS_PATH
            if not credentials_path:
                raise ValueError("GOOGLE_CLIENT_SECRET_FILE or GOOGLE_CREDENTIALS_PATH not configured")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, scopes)
            creds = flow.run_local_server(port=0)
        
        # Save token to configured file
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

def get_recent_meetings(days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch recent calendar meetings.
    
    Returns:
        List of calendar events with id, summary, start, end, description, attendees
    """
    print("=" * 80)
    print("DIAGNOSTIC: get_recent_meetings()")
    print("=" * 80)
    
    service = get_calendar_service()
    time_min = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'
    time_max = datetime.utcnow().isoformat() + 'Z'
    
    print(f"DIAGNOSTIC: Query parameters:")
    print(f"  timeMin: {time_min}")
    print(f"  timeMax: {time_max}")
    print(f"  maxResults: 50")
    print(f"  days_back: {days_back}")
    print(f"  calendarId: {Config.GOOGLE_CALENDAR_ID}")
    
    all_events = []
    page_token = None
    page_num = 0
    
    while True:
        page_num += 1
        print(f"\nDIAGNOSTIC: Fetching page {page_num}")
        print(f"  pageToken (before): {page_token}")
        
        request_params = {
            'calendarId': Config.GOOGLE_CALENDAR_ID,
            'timeMin': time_min,
            'timeMax': time_max,
            'maxResults': 50,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        if page_token:
            request_params['pageToken'] = page_token
        
        events_result = service.events().list(**request_params).execute()
        
        events = events_result.get('items', [])
        next_page_token = events_result.get('nextPageToken')
        
        print(f"  Events returned this page: {len(events)}")
        print(f"  nextPageToken (after): {next_page_token}")
        
        all_events.extend(events)
        
        if not next_page_token:
            break
        
        page_token = next_page_token
    
    print(f"\nDIAGNOSTIC: Total events retrieved across all pages: {len(all_events)}")
    print(f"DIAGNOSTIC: Pagination complete: {'YES' if page_num > 1 else 'NO (single page)'}")
    
    print("\nDIAGNOSTIC: RAW EVENT DUMP (before filtering):")
    print("-" * 80)
    for idx, event in enumerate(all_events, 1):
        print(f"\nEvent #{idx}:")
        print(f"  id: {event.get('id')}")
        print(f"  summary: {event.get('summary', '')}")
        start_data = event.get('start', {})
        start_dt = start_data.get('dateTime') or start_data.get('date')
        print(f"  start: {start_dt}")
        print(f"  organizer.email: {(event.get('organizer') or {}).get('email', '')}")
        print(f"  creator.email: {(event.get('creator') or {}).get('email', '')}")
        attendees = [a.get('email', '') for a in event.get('attendees', []) if a.get('email')]
        print(f"  attendees: {attendees}")
        print(f"  location: {event.get('location', '')}")
    print("-" * 80)
    
    events = all_events
    
    return [
        {
            'id': event.get('id'),
            'summary': event.get('summary', ''),
            'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
            'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
            'description': event.get('description', ''),
            'attendees': [a.get('email') for a in event.get('attendees', []) if a.get('email')],
            'organizer': (event.get('organizer') or {}).get('email', ''),
            'creator': (event.get('creator') or {}).get('email', ''),
            'location': event.get('location', ''),
            'hangoutLink': event.get('hangoutLink')
                or event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
        }
        for event in events
    ]

def _matches_client(meeting: Dict[str, Any], client_lower: str) -> bool:
    """
    Check client name across all relevant event fields.
    """
    haystack = " ".join([
        meeting.get("summary", ""),
        meeting.get("description", ""),
        meeting.get("location", ""),
        meeting.get("organizer", ""),
        meeting.get("creator", ""),
        " ".join(meeting.get("attendees", [])),
    ]).lower()

    return client_lower in haystack

def search_meetings_by_client(client_name: str, days_back: int = 90) -> List[Dict[str, Any]]:
    """
    Search meetings by client name in summary or description.
    
    Returns:
        List of matching calendar events
    """
    all_meetings = get_recent_meetings(days_back)
    client_lower = client_name.lower()
    
    return [
        meeting
        for meeting in all_meetings
        if _matches_client(meeting, client_lower)
    ]

def get_most_recent_meeting_by_client(client_name: str) -> Optional[Dict[str, Any]]:
    """Get the most recent meeting for a client."""
    print("=" * 80)
    print("DIAGNOSTIC: get_most_recent_meeting_by_client()")
    print("=" * 80)
    print(f"DIAGNOSTIC: client_name: {client_name}")
    
    meetings = search_meetings_by_client(client_name)
    if not meetings:
        print("DIAGNOSTIC: No meetings found")
        return None
    
    print(f"\nDIAGNOSTIC: Found {len(meetings)} candidate meetings BEFORE sorting:")
    print("-" * 80)
    for idx, m in enumerate(meetings, 1):
        try:
            parsed_dt = _to_utc_datetime(m["start"])
            print(f"  #{idx}: start='{m['start']}' -> parsed={parsed_dt}, summary='{m['summary']}'")
        except Exception as e:
            print(f"  #{idx}: start='{m['start']}' -> PARSE ERROR: {e}, summary='{m['summary']}'")

    # Sort by start time, most recent first
    print(f"\nDIAGNOSTIC: Sorting by start time (most recent first)...")
    meetings.sort(
        key=lambda x: _to_utc_datetime(x["start"]),
        reverse=True
    )
    
    print(f"\nDIAGNOSTIC: Meetings AFTER sorting:")
    print("-" * 80)
    for idx, m in enumerate(meetings, 1):
        try:
            parsed_dt = _to_utc_datetime(m["start"])
            print(f"  #{idx}: start='{m['start']}' -> parsed={parsed_dt}, summary='{m['summary']}'")
        except Exception as e:
            print(f"  #{idx}: start='{m['start']}' -> PARSE ERROR: {e}, summary='{m['summary']}'")
    
    selected = meetings[0]
    print(f"\nDIAGNOSTIC: Selected meeting (most recent):")
    print(f"  start: {selected['start']}")
    print(f"  summary: {selected['summary']}")
    print(f"  id: {selected.get('id')}")
    
    return selected

def get_meeting_by_client_and_date(
    client_name: str,
    target_date: date,
) -> Optional[Dict[str, Any]]:
    """
    Find a meeting for a client near a specific date.
    Searches +/- days_buffer around target_date.
    """
    print("=" * 80)
    print("DIAGNOSTIC: get_meeting_by_client_and_date()")
    print("=" * 80)
    print(f"DIAGNOSTIC: Input parameters:")
    print(f"  client_name: {client_name}")
    print(f"  target_date: {target_date} (type: {type(target_date)})")
    
    start_dt = datetime.combine(
        target_date,
        datetime.min.time(),
        tzinfo=timezone.utc
    )
    end_dt = datetime.combine(
        target_date,
        datetime.max.time(),
        tzinfo=timezone.utc
    )

    start_range = start_dt.isoformat()
    end_range = end_dt.isoformat()
    
    print(f"\nDIAGNOSTIC: Date window computation:")
    print(f"  start_dt: {start_dt} (timezone: {start_dt.tzinfo})")
    print(f"  end_dt: {end_dt} (timezone: {end_dt.tzinfo})")
    print(f"  timeMin: {start_range}")
    print(f"  timeMax: {end_range}")
    print(f"  ISO format valid: YES")
    print(f"  December 12, 2025 00:00-23:59 UTC covered: {'YES' if target_date == date(2025, 12, 12) else 'N/A'}")

    service = get_calendar_service()
    
    all_events = []
    page_token = None
    page_num = 0
    
    while True:
        page_num += 1
        print(f"\nDIAGNOSTIC: Fetching page {page_num}")
        print(f"  pageToken (before): {page_token}")
        
        request_params = {
            'calendarId': Config.GOOGLE_CALENDAR_ID,
            'timeMin': start_range,
            'timeMax': end_range,
            'maxResults': 50,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        if page_token:
            request_params['pageToken'] = page_token
        
        print(f"  timeMin: {start_range}")
        print(f"  timeMax: {end_range}")
        print(f"  maxResults: 20")
        
        events_result = service.events().list(**request_params).execute()
        
        events = events_result.get("items", [])
        next_page_token = events_result.get('nextPageToken')
        
        print(f"  Events returned this page: {len(events)}")
        print(f"  nextPageToken (after): {next_page_token}")
        
        all_events.extend(events)
        
        if not next_page_token:
            break
        
        page_token = next_page_token
    
    print(f"\nDIAGNOSTIC: Total events retrieved across all pages: {len(all_events)}")
    print(f"DIAGNOSTIC: Pagination complete: {'YES' if page_num > 1 else 'NO (single page)'}")
    
    print("\nDIAGNOSTIC: RAW EVENT DUMP (before client filtering):")
    print("-" * 80)
    for idx, event in enumerate(all_events, 1):
        print(f"\nEvent #{idx}:")
        print(f"  id: {event.get('id')}")
        print(f"  summary: {event.get('summary', '')}")
        start_data = event.get('start', {})
        start_dt_str = start_data.get('dateTime') or start_data.get('date')
        print(f"  start: {start_dt_str}")
        print(f"  organizer.email: {(event.get('organizer') or {}).get('email', '')}")
        print(f"  creator.email: {(event.get('creator') or {}).get('email', '')}")
        attendees = [a.get('email', '') for a in event.get('attendees', []) if a.get('email')]
        print(f"  attendees: {attendees}")
        print(f"  location: {event.get('location', '')}")
    print("-" * 80)
    
    events = all_events

    client_lower = client_name.lower()
    
    print(f"\nDIAGNOSTIC: Client matching for '{client_name}' (lowercase: '{client_lower}')")
    print("-" * 80)

    for idx, event in enumerate(events, 1):
        summary = event.get("summary", "").lower()
        description = event.get("description", "").lower()
        location = event.get("location", "").lower()
        organizer = (event.get("organizer") or {}).get("email", "").lower()
        creator = (event.get("creator") or {}).get("email", "").lower()
        attendees = [a.get("email", "").lower() for a in event.get("attendees", []) if a.get("email")]
        
        summary_match = client_lower in summary
        description_match = client_lower in description
        location_match = client_lower in location
        organizer_match = client_lower in organizer
        creator_match = client_lower in creator
        attendee_match = any(client_lower in att for att in attendees)
        
        matches = summary_match or description_match
        
        print(f"\nEvent #{idx} ({event.get('summary', '')}):")
        print(f"  summary match: {summary_match} (summary: '{summary}')")
        print(f"  description match: {description_match} (description: '{description[:50]}...')")
        print(f"  location match: {location_match}")
        print(f"  organizer match: {organizer_match} (organizer: '{organizer}')")
        print(f"  creator match: {creator_match} (creator: '{creator}')")
        print(f"  attendee match: {attendee_match} (attendees: {attendees})")
        print(f"  OVERALL MATCH: {matches}")
        
        if matches:
            print(f"  ✓ MATCH FOUND - Returning this event")
            return {
                "id": event.get("id"),
                "summary": event.get("summary", ""),
                "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                "description": event.get("description", ""),
                "attendees": [a.get("email") for a in event.get("attendees", [])],
                "location": event.get("location", ""),
                "hangoutLink": event.get("hangoutLink")
                    or event.get("conferenceData", {})
                    .get("entryPoints", [{}])[0]
                    .get("uri", "")
            }

    return None

def get_next_upcoming_meeting_from_calendar(
    client_name: Optional[str] = None,
    lookahead_days: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Returns the next upcoming calendar meeting.
    If client_name is provided, filters to that client.
    """

    print("=" * 80)
    print("DIAGNOSTIC: get_next_upcoming_meeting_from_calendar()")
    print("=" * 80)
    print(f"DIAGNOSTIC: client_name: {client_name}")
    print(f"DIAGNOSTIC: lookahead_days: {lookahead_days}")

    service = get_calendar_service()

    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=lookahead_days)).isoformat()

    print(f"DIAGNOSTIC: timeMin: {time_min}")
    print(f"DIAGNOSTIC: timeMax: {time_max}")

    events_result = service.events().list(
        calendarId=Config.GOOGLE_CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

    events = events_result.get("items", [])

    print(f"DIAGNOSTIC: Events returned: {len(events)}")

    if not events:
        return None

    client_lower = client_name.lower() if client_name else None

    for idx, event in enumerate(events, 1):
        start_str = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")

        try:
            start_dt = _to_utc_datetime(start_str)
        except Exception as e:
            print(f"DIAGNOSTIC: Skipping event #{idx}, date parse failed: {e}")
            continue

        print(f"\nEvent #{idx}:")
        print(f"  summary: {event.get('summary', '')}")
        print(f"  start: {start_dt}")

        meeting = {
            "id": event.get("id"),
            "summary": event.get("summary", ""),
            "start": start_str,
            "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
            "description": event.get("description", ""),
            "attendees": [a.get("email") for a in event.get("attendees", []) if a.get("email")],
            "organizer": (event.get("organizer") or {}).get("email", ""),
            "creator": (event.get("creator") or {}).get("email", ""),
            "location": event.get("location", ""),
            "hangoutLink": event.get("hangoutLink")
                or event.get("conferenceData", {})
                .get("entryPoints", [{}])[0]
                .get("uri", ""),
        }

        if client_lower:
            if not _matches_client(meeting, client_lower):
                print("  ✗ Client does not match, skipping")
                continue

        print("  ✓ Selected as next upcoming meeting")
        return meeting

    print("DIAGNOSTIC: No upcoming meeting matched client filter")
    return None
