"""Zoom integration - extract meeting ID and fetch transcript."""
import re
from typing import Optional
from app.integrations.calendar import get_calendar_service
from app.config import Config
import requests
import base64
from datetime import datetime, timedelta
from urllib.parse import quote
from app.runtime.mode import is_demo_mode
from app.demo.transcripts import load_demo_transcript


class ZoomClient:
    def __init__(self):
        self.account_id = Config.ZOOM_ACCOUNT_ID
        self.client_id = Config.ZOOM_CLIENT_ID
        self.client_secret = Config.ZOOM_CLIENT_SECRET
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        url = (
            "https://zoom.us/oauth/token"
            f"?grant_type=account_credentials&account_id={self.account_id}"
        )

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        resp = requests.post(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}


def resolve_meeting_uuid(
    zoom_meeting_id: str,
    expected_date: Optional[datetime] = None
) -> Optional[str]:
    """
    Resolve Zoom meeting UUID from meeting ID.
    Uses /past_meetings/{meeting_id}/instances
    """
    client = ZoomClient()

    url = f"https://api.zoom.us/v2/past_meetings/{zoom_meeting_id}/instances"
    resp = requests.get(url, headers=client._headers(), timeout=30)

    if resp.status_code != 200:
        return None

    meetings = resp.json().get("meetings", [])
    if not meetings:
        return None

    if expected_date:
        def score(m):
            dt = datetime.fromisoformat(m["start_time"].replace("Z", "+00:00"))
            return abs((dt - expected_date).total_seconds())

        meetings.sort(key=score)
    else:
        meetings.sort(key=lambda m: m["start_time"], reverse=True)

    return meetings[0]["uuid"]


def fetch_transcript_by_uuid(meeting_uuid: str) -> Optional[str]:
    """
    Fetch transcript text for a Zoom meeting UUID.
    """
    client = ZoomClient()

    encoded_uuid = quote(meeting_uuid, safe="")
    urls = [
        f"https://api.zoom.us/v2/meetings/{encoded_uuid}/recordings",
        f"https://api.zoom.us/v2/meetings/{meeting_uuid}/recordings",
    ]

    recordings = None
    for url in urls:
        resp = requests.get(url, headers=client._headers(), timeout=30)
        if resp.status_code == 200:
            recordings = resp.json()
            break

    if not recordings:
        return None

    files = recordings.get("recording_files", [])

    transcript_file = None
    for f in files:
        if (
            f.get("file_type") == "TRANSCRIPT"
            or f.get("recording_type") == "AUDIO_TRANSCRIPT"
            or f.get("file_extension", "").lower() == "vtt"
            or f.get("file_name", "").lower().endswith(".vtt")
        ):
            transcript_file = f
            break

    if not transcript_file:
        return None

    download_url = transcript_file.get("download_url")
    if not download_url:
        return None

    resp = requests.get(
        download_url,
        headers=client._headers(),
        timeout=120,
        allow_redirects=True,
    )

    if resp.status_code != 200:
        return None

    return _parse_vtt(resp.text)


def _parse_vtt(vtt_text: str) -> str:
    lines = []
    for line in vtt_text.splitlines():
        line = line.strip()
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("NOTE")
            or "-->" in line
        ):
            continue
        lines.append(line)

    return "\n".join(lines)

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


def fetch_zoom_transcript(
    zoom_meeting_id: str,
    expected_date: Optional[datetime] = None
) -> Optional[str]:

    if is_demo_mode():
        return demo_zoom_transcript()

    uuid = resolve_meeting_uuid(zoom_meeting_id, expected_date)
    if not uuid:
        return None
    return fetch_transcript_by_uuid(uuid)

