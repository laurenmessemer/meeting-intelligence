from typing import Optional, List, Any, Dict
import json
import logging

from app.llm.client import chat as gemini_chat
from app.runtime.mode import is_demo_mode

logger = logging.getLogger(__name__)

LLM_CONFIDENCE_THRESHOLD = 0.85


def resolve_client_name(
    *,
    explicit_client: Optional[str],
    meeting,
    calendar_event: Dict[str, Any],
    known_clients: Optional[List[str]] = None,
) -> Optional[str]:


    """
    Canonical client-name resolver.

    Resolution order:
    1) Existing meeting memory (authoritative)
    2) Explicit user-provided client
    3) Deterministic calendar parsing
    4) LLM-assisted constrained resolution

    Returns:
        Canonical client_name or None
    """

    if is_demo_mode():
    # If no explicit client and no meeting memory, default safely
        if not explicit_client and not (meeting and meeting.client_name):
            return "Good Health"

    # -------------------------------------------------
    # 1) Existing meeting always wins
    # -------------------------------------------------
    if meeting and meeting.client_name:
        return meeting.client_name.strip()

    # -------------------------------------------------
    # 2) Explicit user input
    # -------------------------------------------------
    if explicit_client:

        return explicit_client.strip()

    summary = (calendar_event or {}).get("summary", "")
    attendees = (calendar_event or {}).get("attendees", [])

    # -------------------------------------------------
    # 3) Deterministic fallback (very conservative)
    # -------------------------------------------------
    deterministic = _deterministic_client_from_summary(summary)
    if deterministic:
        return deterministic

    # -------------------------------------------------
    # 4) LLM-assisted resolution (only if constrained)
    # -------------------------------------------------
    if known_clients:
        llm_result = _llm_resolve_client(
            summary=summary,
            attendees=attendees,
            known_clients=known_clients,
        )

        if (
            llm_result.get("client")
            and llm_result.get("confidence", 0.0) >= LLM_CONFIDENCE_THRESHOLD
        ):
            return llm_result["client"]

    return None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _deterministic_client_from_summary(summary: str) -> Optional[str]:
    """
    Very conservative string cleanup.
    ONLY returns if result is clean and short.
    """
    if not summary:
        return None

    lowered = summary.lower()

    blacklist = [
        "meeting",
        "call",
        "sync",
        "review",
        "crm",
        "college list",
        ":",
        "-",
    ]

    for phrase in blacklist:
        lowered = lowered.replace(phrase, "")

    cleaned = " ".join(lowered.split()).title()

    # Safety: avoid returning long phrases
    if len(cleaned.split()) <= 3:
        return cleaned

    return None


def _llm_resolve_client(
    *,
    summary: str,
    attendees: List[Any],
    known_clients: List[str],
) -> Dict[str, Any]:
    """
    LLM-assisted client resolution.
    Must choose from known_clients or return null.
    """

    system_prompt = (
        "You are a strict client name resolution assistant.\n"
        "You MUST choose a client from the provided list.\n"
        "You MUST NOT invent or guess new companies.\n"
        "If no clear match exists, return null.\n"
        "Return JSON only."
    )

    payload = {
        "calendar_summary": summary,
        "attendees": attendees,
        "known_clients": known_clients,
        "output_schema": {
            "client": "string or null",
            "confidence": "number between 0 and 1",
            "reasoning": "string",
        },
    }

    try:
        raw = gemini_chat(
            prompt=json.dumps(payload),
            system_prompt=system_prompt,
            temperature=0.0,
        )
        parsed = json.loads(raw)
        return parsed
    except Exception as e:
        return {"client": None, "confidence": 0.0}
