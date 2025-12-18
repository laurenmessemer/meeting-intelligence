from typing import Optional
from app.runtime.mode import is_demo_mode
from app.demo.fixtures import demo_memory_seed
from app.memory.schemas import MemoryEntryCreate, MeetingCreate

def seed_demo_data(memory_repo) -> None:
    """
    Idempotent demo seeding.
    Only seeds if demo mode and DB has no meetings.
    """
    if not is_demo_mode():
        return

    # 1) If any meeting exists, don't seed
    # seed.py

from app.demo.fixtures import demo_calendar_events, demo_zoom_transcript_for
from app.memory.schemas import MeetingCreate, MeetingUpdate

def seed_demo_data(memory_repo) -> None:
    if not is_demo_mode():
        return

    events = demo_calendar_events()

    for event in events:
        existing = memory_repo.get_meeting_by_calendar_id(event["id"])
        if existing:
            continue

        transcript = demo_zoom_transcript_for(event["id"])

        meeting = memory_repo.create_meeting(
            MeetingCreate(
                client_name=event["summary"].split("–")[0].strip(),
                meeting_date=datetime.fromisoformat(event["start"]),
                calendar_event_id=event["id"],
                zoom_meeting_id=f"zoom_{event['id']}",
                transcript=transcript,
            )
        )

        # Optional: seed per-meeting memory here if you want


    # 2) Create a demo meeting record (minimal)
    # NOTE: meeting_date should be parseable; use UTC now or a fixed date
    meeting = memory_repo.create_meeting(
        MeetingCreate(
            client_name="Good Health",
            meeting_date=memory_repo.utcnow() if hasattr(memory_repo, "utcnow") else None,
            calendar_event_id="demo_event_001",
            zoom_meeting_id="demo_zoom_001",
            transcript=None,  # transcript will come from demo zoom integration
        )
    )

    # 3) Seed memory entries (minimal)
    seed = demo_memory_seed()
    for key, value in seed.items():
        memory_repo.create_memory_entry(
            MemoryEntryCreate(
                meeting_id=meeting.id,
                key=key,
                value=str(value)[:2000],
                metadata={"demo": True},
            )
        )
