"""Workflow definitions - data only, no logic."""

MEETING_SUMMARY_WORKFLOW = {
    "name": "summarize_meeting",
    "steps": [
        "resolve_meeting",
        "summarize_meeting"
    ],
    "produces": [
        "summary",
        "decisions",
        "action_items"
    ]
}
