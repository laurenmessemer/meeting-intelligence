KNOWN_CLIENTS = {
    "mtca": "MTCA",
    "mt college auditions": "MTCA",
    "musical theatre college auditions": "MTCA",
    "good health": "Good Health",
    "gfs": "Gordon Food Services",
}

def extract_client_from_calendar(calendar_event: dict) -> str | None:
    """
    Deterministic, rules-based client extraction.
    ONLY used for first-time meetings.
    """

    haystack = " ".join([
        calendar_event.get("summary", ""),
        calendar_event.get("description", ""),
        calendar_event.get("location", ""),
        " ".join(calendar_event.get("attendees", []) or []),
    ]).lower()

    for key, canonical in KNOWN_CLIENTS.items():
        if key in haystack:
            return canonical

    return None
