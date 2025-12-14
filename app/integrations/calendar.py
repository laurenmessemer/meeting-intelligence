"""Google Calendar integration - fetch meetings only."""
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from app.config import Config

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


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
    service = get_calendar_service()
    time_min = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'
    time_max = datetime.utcnow().isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId=Config.GOOGLE_CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    return [
        {
            'id': event.get('id'),
            'summary': event.get('summary', ''),
            'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
            'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
            'description': event.get('description', ''),
            'attendees': [a.get('email') for a in event.get('attendees', [])],
            'location': event.get('location', ''),
            'hangoutLink': event.get('hangoutLink') or event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
        }
        for event in events
    ]


def search_meetings_by_client(client_name: str, days_back: int = 90) -> List[Dict[str, Any]]:
    """
    Search meetings by client name in summary or description.
    
    Returns:
        List of matching calendar events
    """
    all_meetings = get_recent_meetings(days_back)
    client_lower = client_name.lower()
    
    return [
        meeting for meeting in all_meetings
        if client_lower in meeting['summary'].lower() or client_lower in meeting.get('description', '').lower()
    ]


def get_most_recent_meeting_by_client(client_name: str) -> Optional[Dict[str, Any]]:
    """Get the most recent meeting for a client."""
    meetings = search_meetings_by_client(client_name)
    if not meetings:
        return None
    
    # Sort by start time, most recent first
    meetings.sort(key=lambda x: x['start'], reverse=True)
    return meetings[0]
