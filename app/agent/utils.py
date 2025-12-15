from typing import Optional


def resolve_client_name(
    explicit_client: Optional[str],
    meeting,
    calendar_event: dict,
) -> Optional[str]:
    """
    Resolve client name deterministically.
    Returns None if confidence is insufficient.
    """

    # 1. Explicitly provided by user intent
    if explicit_client:
        return explicit_client.strip()

    # 2. Existing meeting memory (authoritative)
    if meeting and getattr(meeting, "client_name", None):
        return meeting.client_name.strip()

    # 3. Very conservative heuristic (OPTIONAL, whitelist-only)
    summary = (calendar_event.get("summary") or "").lower()

    KNOWN_CLIENT_KEYWORDS = {
        "mtca": "MTCA",
        "good health": "Good Health",
        "for good": "For Good",
    }

    for keyword, client in KNOWN_CLIENT_KEYWORDS.items():
        if keyword in summary:
            return client

    # 4. No confident client
    return None
