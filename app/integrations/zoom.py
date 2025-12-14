"""Zoom integration - extract meeting ID and fetch transcript."""
import re
from typing import Optional
from app.integrations.calendar import get_calendar_service
from app.config import Config

# Note: Zoom OAuth configuration available via Config.ZOOM_ACCOUNT_ID, 
# Config.ZOOM_CLIENT_ID, Config.ZOOM_CLIENT_SECRET
# Legacy fallback: Config.ZOOM_API_KEY, Config.ZOOM_API_SECRET


def extract_zoom_meeting_id(calendar_event: dict) -> Optional[str]:
    """
    Extract Zoom meeting ID from calendar event.
    
    Looks for Zoom meeting links in:
    - hangoutLink
    - description
    - location
    
    Returns:
        Zoom meeting ID (11-digit number) or None
    """
    # Zoom meeting IDs are typically 11 digits
    zoom_id_pattern = r'zoom\.us/j/(\d{11})'
    
    # Check hangoutLink
    hangout_link = calendar_event.get('hangoutLink', '')
    if hangout_link:
        match = re.search(zoom_id_pattern, hangout_link)
        if match:
            return match.group(1)
    
    # Check description
    description = calendar_event.get('description', '')
    if description:
        match = re.search(zoom_id_pattern, description)
        if match:
            return match.group(1)
    
    # Check location
    location = calendar_event.get('location', '')
    if location:
        match = re.search(zoom_id_pattern, location)
        if match:
            return match.group(1)
    
    return None


def fetch_zoom_transcript(zoom_meeting_id: str) -> Optional[str]:
    """
    Fetch Zoom meeting transcript.
    
    Note: This is a stub implementation. Real implementation would use Zoom API
    to fetch transcripts. For now, returns None to indicate transcript unavailable.
    
    Args:
        zoom_meeting_id: 11-digit Zoom meeting ID
    
    Returns:
        Transcript text or None if unavailable
    """
    # TODO: Implement actual Zoom API call
    # This would require:
    # 1. Zoom OAuth authentication
    # 2. API call to get meeting recordings/transcripts
    # 3. Parse and return transcript text
    
    # For now, return None to indicate transcript is not available
    # The orchestrator will handle this gracefully
    return None
