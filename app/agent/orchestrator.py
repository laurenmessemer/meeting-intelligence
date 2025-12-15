"""Agent orchestrator - coordinates all operations, owns control flow."""

from typing import Dict, Any
from datetime import datetime, date
from dateutil import parser

from app.agent.intents import recognize_intent
from app.agent.workflows import MEETING_SUMMARY_WORKFLOW
from app.agent.commitments import create_commitments_from_action_items

from app.memory.repo import MemoryRepo
from app.memory.schemas import MeetingCreate, MeetingUpdate, MemoryEntryCreate

from app.integrations.calendar import (
    get_most_recent_meeting_by_client,
    get_meeting_by_client_and_date,
    get_next_upcoming_meeting_from_calendar,
    get_most_recent_meeting,
)

from app.integrations.zoom import extract_zoom_meeting_id, fetch_zoom_transcript

from app.tools.summarize import summarize_meeting
from app.tools.followup import generate_followup_email
from app.tools.meeting_brief import generate_meeting_brief

from app.integrations.hubspot import HubSpotIntegrationError


import logging

logger = logging.getLogger(__name__)

ENABLE_HUBSPOT = False

class Orchestrator:
    """Coordinates agent operations - no SQL, HTTP, or LLM prompts here."""

    def __init__(self, memory_repo: MemoryRepo):
        self.memory_repo = memory_repo

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _parse_target_date(self, date_str: str) -> date:
        """
        Parse ISO or natural-language dates into a date object.
        If no year is specified and the date is in the past,
        assume the next future occurrence.
        """
        parsed = parser.parse(date_str, default=datetime.utcnow())
        parsed_date = parsed.date()

        today = datetime.utcnow().date()
        year_specified = "20" in date_str

        if not year_specified and parsed_date < today:
            parsed_date = date(parsed_date.year + 1, parsed_date.month, parsed_date.day)

        return parsed_date

    # -------------------------------------------------
    # Public entry point
    # -------------------------------------------------

    def process_message(self, user_message: str) -> Dict[str, Any]:
        intent_result = recognize_intent(user_message)
        intent = intent_result.get("intent")
        entities = intent_result.get("entities", {})

        workflow = None

        if intent == "summarize_meeting":
            workflow = MEETING_SUMMARY_WORKFLOW["name"]
            response = self._execute_meeting_summary_workflow(entities)

        elif intent == "generate_followup":
            workflow = "generate_followup"
            response = self._execute_followup_workflow()

        elif intent == "meeting_brief":
            workflow = "meeting_brief"
            response = self._execute_meeting_brief_workflow(entities)

        else:
            response = {
                "message": (
                    "I can help you with:\n"
                    "- Summarizing past meetings\n"
                    "- Generating follow-up emails\n"
                    "- Briefing you on upcoming meetings\n\n"
                    "Try:\n"
                    "- 'Summarize my last meeting'\n"
                    "- 'Brief me on my next meeting'\n"
                    "- 'Brief me on my meeting with MTCA'"
                ),
                "metadata": {"intent": intent},
            }

        self.memory_repo.create_interaction(
            user_message=user_message,
            intent=intent,
            workflow=workflow,
            response=response.get("message", ""),
            metadata=response.get("metadata", {}),
        )

        return response

    # -------------------------------------------------
    # Meeting Summary Workflow
    # -------------------------------------------------

    def _execute_meeting_summary_workflow(
        self, entities: Dict[str, Any]
    ) -> Dict[str, Any]:

        client_name = entities.get("client_name")
        date_str = entities.get("date")
        calendar_event = None

        # CASE 1: No client, no date → most recent meeting overall
        if not client_name and not date_str:
            calendar_event = get_most_recent_meeting()

        # CASE 2: Client + date → strict date resolution
        elif client_name and date_str:
            try:
                target_date = self._parse_target_date(date_str)
                calendar_event = get_meeting_by_client_and_date(
                    client_name=client_name,
                    target_date=target_date,
                )
                if not calendar_event:
                    return {
                        "message": f"I couldn't find a meeting with {client_name} on {date_str}.",
                        "metadata": {
                            "error": "meeting_not_found_for_date",
                            "client_name": client_name,
                            "date": date_str,
                        },
                    }
            except Exception as e:
                return {
                    "message": (
                        f"I couldn't resolve the meeting date you requested "
                        f"({date_str}). Please try rephrasing."
                    ),
                    "metadata": {
                        "error": "date_resolution_failed",
                        "exception": str(e),
                    },
                }

        # CASE 3: Client only → most recent meeting for that client
        elif client_name:
            calendar_event = get_most_recent_meeting_by_client(client_name)

        # CASE 4: Date only → ambiguous
        elif date_str:
            return {
                "message": (
                    "I need the client name to summarize a meeting for a specific date. "
                    "Please try again and include the client."
                ),
                "metadata": {
                    "error": "missing_client_name",
                    "date": date_str,
                },
            }

        if not calendar_event:
            return {
                "message": "I couldn’t find any meetings matching your request.",
                "metadata": {"error": "meeting_not_found"},
            }

        if not client_name:
            client_name = calendar_event.get("summary", "Unknown Client")

        # -------------------------------------------------
        # Memory + Transcript Resolution
        # -------------------------------------------------

        existing_meeting = self.memory_repo.get_meeting_by_calendar_id(
            calendar_event["id"]
        )

        start_str = calendar_event.get("start")
        try:
            meeting_date = (
                datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                if start_str
                else datetime.utcnow()
            )
        except Exception:
            meeting_date = datetime.utcnow()

        zoom_meeting_id = extract_zoom_meeting_id(calendar_event)
        transcript = (
            fetch_zoom_transcript(zoom_meeting_id, expected_date=meeting_date)
            if zoom_meeting_id
            else None
        )

        if not existing_meeting:
            meeting = self.memory_repo.create_meeting(
                MeetingCreate(
                    client_name=client_name,
                    meeting_date=meeting_date,
                    calendar_event_id=calendar_event["id"],
                    zoom_meeting_id=zoom_meeting_id,
                    transcript=transcript,
                )
            )
        else:
            meeting = existing_meeting

        # -------------------------------------------------
        # Summarization
        # -------------------------------------------------

        memory_entries = self.memory_repo.get_memory_for_client(client_name)
        memory_context = "\n".join(
            f"{entry.key}: {entry.value}" for entry in memory_entries[:5]
        )

        summary_result = summarize_meeting(
            transcript=transcript or meeting.transcript,
            meeting_metadata={
                "date": calendar_event.get("start"),
                "attendees": calendar_event.get("attendees", []),
                "client_name": client_name,
            },
            memory_context=memory_context,
        )

        self.memory_repo.update_meeting(
            meeting.id,
            MeetingUpdate(
                summary=summary_result["summary"],
                decisions=summary_result["decisions"],
                action_items=summary_result["action_items"],
            ),
        )

        if summary_result.get("summary"):
            self.memory_repo.create_memory_entry(
                MemoryEntryCreate(
                    meeting_id=meeting.id,
                    key="meeting_summary",
                    value=summary_result["summary"][:500],
                    metadata={"client": client_name},
                )
            )

        commitments = []
        hubspot_errors = []

        if summary_result.get("action_items"):
            try:
                commitments = create_commitments_from_action_items(
                    summary_result["action_items"],
                    meeting.id,
                    self.memory_repo,
                )
            except HubSpotIntegrationError as e:
                logger.warning("HubSpot integration failed during commitment creation", exc_info=e)
                hubspot_errors.append(str(e))

        # -------------------------------------------------
        # Optional HubSpot Integration (non-blocking)
        # -------------------------------------------------

        if ENABLE_HUBSPOT:
            try:
                create_hubspot_task(
                    meeting_id=meeting.id,
                    client_name=client_name,
                    action_items=summary_result.get("action_items", []),
                )
            except Exception as e:
                logger.warning(f"HubSpot task creation failed (ignored): {e}")


        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        response_message = f"""**Meeting Summary for {client_name}**

        {summary_result['summary']}

        **Decisions:**
        {chr(10).join(f"- {d}" for d in summary_result.get('decisions', [])) or "None"}

        **Action Items:**
        {chr(10).join(f"- {item.get('text', '')}" for item in summary_result.get('action_items', [])) or "None"}
        """

        self.memory_repo.set_active_meeting(meeting.id)


        return {
            "message": response_message,
            "metadata": {
                "meeting_id": meeting.id,
                "client_name": client_name,
                "commitments_created": len(commitments),
                "hubspot_status": "failed" if hubspot_errors else "success",
            },
        }



    # -------------------------------------------------
    # Follow-up Workflow
    # -------------------------------------------------

    def _execute_followup_workflow(self) -> Dict[str, Any]:
        meeting = self.memory_repo.get_active_meeting()

        if not meeting:
            meeting = self.memory_repo.get_most_recent_meeting()


        if not meeting:
            return {
                "message": "I don’t have any meetings on record yet.",
                "metadata": {"error": "no_meetings"},
            }

        if not meeting.summary:
            return {
                "message": (
                    "I don’t have a summarized meeting to generate a follow-up from yet. "
                    "Please summarize a meeting first."
                ),
                "metadata": {"error": "meeting_not_summarized"},
            }

        followup_text = generate_followup_email(
            summary=meeting.summary,
            decisions=meeting.decisions or [],
            action_items=meeting.action_items or [],
            client_name=meeting.client_name,
            meeting_date=meeting.meeting_date.date().isoformat(),
            memory_context="",
        )

        return {
            "message": followup_text,
            "metadata": {
                "meeting_id": meeting.id,
                "client_name": meeting.client_name,
            },
        }

    # -------------------------------------------------
    # Meeting Brief Workflow
    # -------------------------------------------------

    def _execute_meeting_brief_workflow(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        client_name = entities.get("client_name")

        calendar_event = get_next_upcoming_meeting_from_calendar(client_name)

        if not calendar_event:
            return {
                "message": (
                    "I couldn’t find any upcoming meetings"
                    f"{f' with {client_name}' if client_name else ''}."
                ),
                "metadata": {"error": "no_upcoming_meeting"},
            }

        memory_entries = (
            self.memory_repo.get_memory_for_client(client_name)
            if client_name
            else []
        )

        memory_context = "\n".join(
            f"- {entry.value}" for entry in memory_entries[:5]
        )

        brief_text = generate_meeting_brief(
            client_name=client_name,
            meeting_title=calendar_event.get("summary", "Upcoming Meeting"),
            meeting_date=calendar_event.get("start"),
            attendees=calendar_event.get("attendees", []),
            memory_context=memory_context,
        )

        return {
            "message": brief_text,
            "metadata": {
                "calendar_event_id": calendar_event.get("id"),
                "client_name": client_name,
            },
        }
