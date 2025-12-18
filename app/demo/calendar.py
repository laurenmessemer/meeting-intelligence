from pathlib import Path
from datetime import datetime, timezone
import json
from typing import List, Optional, Dict

_DATA_DIR = Path(__file__).resolve().parent / "data"
_EVENTS_FILE = _DATA_DIR / "calendar_events.json"

def load_demo_events() -> List[dict]:
    return json.loads(_EVENTS_FILE.read_text(encoding="utf-8"))

def get_most_recent_demo_meeting() -> Optional[dict]:
        now = datetime.now(timezone.utc)
        events = load_demo_events()

        past_events = []

        for e in events:
            start_dt = datetime.fromisoformat(
                e["start"].replace("Z", "+00:00")
            )

            if start_dt <= now:
                past_events.append((start_dt, e))

        if not past_events:
            return None

        # 🔑 SORT BY DATE DESCENDING
        past_events.sort(key=lambda x: x[0], reverse=True)

        return past_events[0][1]

def get_demo_meetings_for_client(client_name: str) -> List[dict]:
    return [
        e for e in load_demo_events()
        if e["client_name"].lower() == client_name.lower()
    ]


def get_demo_meeting_by_client_and_date(
    client_name: str,
    target_date
    ) -> Optional[Dict]:
    for e in load_demo_events():
        if (
            e["client_name"].lower() == client_name.lower()
            and e["start"][:10] == target_date.isoformat()
        ):
            return e
    return None

def get_next_upcoming_demo_meeting(
    client_name: Optional[str] = None
) -> Optional[Dict]:
    now = datetime.now(timezone.utc)

    events = load_demo_events()

    if client_name:
        events = [
            e for e in events
            if e.get("client_name", "").lower() == client_name.lower()
        ]

    future_events = []

    for e in events:
        try:
            start_dt = datetime.fromisoformat(
                e["start"].replace("Z", "+00:00")
            ).astimezone(timezone.utc)
        except Exception:
            continue

        if start_dt > now:
            future_events.append((start_dt, e))

    if not future_events:
        return None

    # 🔑 Earliest upcoming meeting
    future_events.sort(key=lambda x: x[0])
    return future_events[0][1]
