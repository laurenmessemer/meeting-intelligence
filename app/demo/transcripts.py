from pathlib import Path

BASE_PATH = Path(__file__).parent / "data"


def load_demo_transcript(calendar_event: dict) -> str:
    filename = calendar_event.get("transcript_file")

    if not filename:
        raise ValueError(
            f"Demo calendar event '{calendar_event.get('id')}' "
            "is missing 'transcript_file'"
        )

    transcript_path = BASE_PATH / filename

    if not transcript_path.exists():
        raise FileNotFoundError(
            f"Missing demo transcript file: {transcript_path}"
        )

    return transcript_path.read_text(encoding="utf-8")
