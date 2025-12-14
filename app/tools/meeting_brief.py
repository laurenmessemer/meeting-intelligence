"""Meeting brief generation tool - LLM-powered."""

from typing import List
from app.llm.client import chat
from app.llm.prompts import MEETING_BRIEF_SYSTEM, MEETING_BRIEF_USER


def generate_meeting_brief(
    client_name: str,
    meeting_title: str,
    meeting_date: str,
    attendees: List[str],
    memory_context: str = "",
) -> str:
    """
    Generate a concise prep brief for an upcoming meeting.
    """

    prompt = MEETING_BRIEF_USER.format(
        client_name=client_name,
        meeting_title=meeting_title,
        meeting_date=meeting_date,
        attendees=", ".join(attendees) if attendees else "Unknown",
        memory_context=memory_context,
    )

    return chat(
        prompt=prompt,
        system_prompt=MEETING_BRIEF_SYSTEM,
        temperature=0.4,
    )
