"""Agent orchestrator - coordinates all operations, owns control flow."""

from typing import Dict, Any, Optional
from datetime import datetime, date
from dateutil import parser
import uuid
import re 

from app.agent.intents import recognize_intent
from app.agent.workflows import MEETING_SUMMARY_WORKFLOW

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
from app.agent.client_resolution import resolve_client_name

from app.runtime.mode import is_demo_mode
from app.demo.fixtures import demo_zoom_transcript


from app.integrations.hubspot import (
    HubSpotIntegrationError,
    get_company_by_name,
    get_or_create_company_id
)

import logging

logger = logging.getLogger(__name__)

ENABLE_HUBSPOT = True

class Orchestrator:

    def log_trace(self, message: str):
        logger.info(f"[TRACE {self.trace_id}] {message}")

    """Coordinates agent operations - no SQL, HTTP, or LLM prompts here."""

    def __init__(self, memory_repo: MemoryRepo):
        self.memory_repo = memory_repo

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _parse_target_date(self, date_str: str) -> date:
        """
        Parse natural-language dates into a concrete date.
        If no year is specified, resolve to the most recent
        occurrence on or before today.
        """
        today = datetime.utcnow().date()

        # First: detect explicit year using regex (not substring)
        year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
        year_specified = bool(year_match)

        # Parse without forcing a year
        parsed = parser.parse(date_str, fuzzy=True)
        parsed_date = parsed.date()

        # Only trust year if user explicitly typed a 4-digit year
        explicit_year = re.search(r"\b(19|20)\d{2}\b", date_str)

        if not explicit_year:
            candidate = date(today.year, parsed_date.month, parsed_date.day)
            if candidate > today:
                candidate = date(today.year - 1, parsed_date.month, parsed_date.day)
            return candidate

        if year_specified:
            return parsed_date

        # No year → assume current year first
        candidate = date(today.year, parsed_date.month, parsed_date.day)

        # If that date is in the future, roll back one year
        if candidate > today:
            candidate = date(today.year - 1, parsed_date.month, parsed_date.day)

        return candidate


    def _has_actionable_date(self, date_text: Optional[str]) -> bool:
        if not date_text:
            return False

        date_text = date_text.strip().lower()

        NON_DATE_KEYWORDS = {
            "last",
            "recent",
            "recently",
            "latest",
            "most recent",
            "last meeting",
            "previous",
            "previous meeting",
        }

        for phrase in NON_DATE_KEYWORDS:
            if phrase in date_text:
                return False

        return True


    # -------------------------------------------------
    # Public entry point
    # -------------------------------------------------

    def process_message(
    self,
    user_message: str,
    intent_override: Optional[str] = None,
    entities_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
        if intent_override:
            intent = intent_override
            entities = entities_override or {}
            logger.info(f"[INTENT OVERRIDE] intent={intent} entities={entities}")
        else:
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
        
        elif intent == "approve_hubspot_tasks":
            response = self._execute_hubspot_approval_workflow(entities)

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

        trace_id = str(uuid.uuid4())[:8]

        client_name = entities.get("client_name")
        raw_date_text = entities.get("date_text")
        date_str = raw_date_text if self._has_actionable_date(raw_date_text) else None

        calendar_event = None
        existing_meeting = None 

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


        # -------------------------------------------------
        # Load existing meeting early (if it exists)
        # -------------------------------------------------

        if is_demo_mode():
            client_name = "MTCA"

        existing_meeting = self.memory_repo.get_meeting_by_calendar_id(
            calendar_event["id"]
        )

        if existing_meeting:
            logger.info(
                f"[TRACE {trace_id}] Existing meeting found | "
                f"meeting_id={existing_meeting.id} | "
                f"client_name='{existing_meeting.client_name}'"
            )
        else:
            logger.info(f"[TRACE {trace_id}] No existing meeting found")



        # -------------------------------------------------
        # Client Resolution (authoritative)
        # Priority: DB meeting -> explicit user -> deterministic -> LLM -> ask user
        # -------------------------------------------------

        # 1) DB meeting wins (canonical if it exists)
        if existing_meeting and existing_meeting.client_name:
            client_name = existing_meeting.client_name

        # 2) Explicit user client next (if provided)
        if not client_name and entities.get("client_name"):
            client_name = entities.get("client_name")

        # 3) Deterministic resolver (your existing function)
        if not client_name:
            known_clients = self.memory_repo.get_distinct_client_names()

            client_name = resolve_client_name(
                explicit_client=entities.get("client_name"),
                meeting=existing_meeting,
                calendar_event=calendar_event,
                known_clients=known_clients,
            )

        # 4) LLM resolver only if still unresolved
        # llm_meta = None
        # if not client_name:
        #     known_clients = self.memory_repo.get_distinct_client_names()

        #     # IMPORTANT: you must wire in your actual LLM call here
        #     # Replace `your_llm_chat_fn` with your existing LLM chat callable.
        #     llm_result = llm_resolve_client_name(
        #         calendar_summary=calendar_event.get("summary", ""),
        #         attendees=calendar_event.get("attendees", []),
        #         known_clients=known_clients,
        #         llm_chat_fn=your_llm_chat_fn,
        #     )

            # llm_meta = llm_result

            # # Gate on confidence
            # if llm_result.get("proposed_client") and llm_result.get("confidence", 0.0) >= 0.85:
            #     client_name = llm_result["proposed_client"]

        # 5) If still not resolved, ask user
        if not client_name:
            return {
                "message": (
                    "I couldn’t confidently determine the client for this meeting. "
                    "Which client/company was this with?"
                ),
                "metadata": {
                    "error": "client_not_resolved",
                    "calendar_summary": calendar_event.get("summary"),
                    "llm_client_resolution": None,
                },
            }


        # -------------------------------------------------
        # Memory + Transcript Resolution
        # -------------------------------------------------


        start_str = calendar_event.get("start")
        try:
            meeting_date = (
                datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                if start_str
                else datetime.utcnow()
            )
        except Exception:
            meeting_date = datetime.utcnow()

        if is_demo_mode():
            transcript = demo_zoom_transcript()
            zoom_meeting_id = "demo_zoom_001"
        else:
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
        # HubSpot Company Resolution (safe: meeting exists)
        # -------------------------------------------------

        if ENABLE_HUBSPOT and not meeting.hubspot_company_id:
            try:
                from app.integrations.hubspot import normalize_company_name

                normalized_company = normalize_company_name(client_name)

                meeting.hubspot_company_id = get_or_create_company_id(normalized_company)
                self.memory_repo.session.commit()

            except HubSpotIntegrationError as e:
                logger.warning(
                    f"Failed to resolve HubSpot company for {client_name}",
                    exc_info=e,
                )

        # -------------------------------------------------
        # Summarization
        # -------------------------------------------------

        memory_entries = self.memory_repo.get_memory_for_client(client_name)
        memory_context = "\n".join(
            f"{entry.key}: {entry.value}" for entry in memory_entries[:5]
        )

        # -------------------------------------------------
        # Pre-summary attendee context (SAFE, NON-INFERRED)
        # -------------------------------------------------


        summary_result = summarize_meeting(
            transcript=transcript or meeting.transcript,
            meeting_metadata={
                "date": meeting.meeting_date.isoformat(),
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

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        meeting_date_str = meeting.meeting_date.strftime("%B %d, %Y")

        response_message = f"""**Meeting Summary**
        **Client:** {client_name}
        **Date:** {meeting_date_str}
        **Attendees:** {chr(10).join(f"{attendee}" for attendee in calendar_event.get('attendees', []))}

        {summary_result['summary']}


        **Decisions:**
        {chr(10).join(f"- {d}" for d in summary_result.get('decisions', [])) or "None"}

        **Action Items:**
        {chr(10).join(f"- {item.get('text', '')}" for item in summary_result.get('action_items', [])) or "None"}
        """

        self.memory_repo.set_active_meeting(meeting.id)


        proposed_tasks = [
            {
                "text": item.get("text"),
                "owner": item.get("owner"),
                "deadline": item.get("deadline"),
            }
            for item in summary_result.get("action_items", [])
        ]

        return {
            "message": response_message,
            "metadata": {
                "meeting_id": meeting.id,
                "client_name": client_name,
                "proposed_hubspot_tasks": proposed_tasks,
                "requires_hubspot_approval": bool(proposed_tasks),
                "calendar_event_summary": calendar_event.get("summary"),
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

    def create_selected_hubspot_tasks(*, tasks, meeting_id, memory_repo):
        created = []
        failed = []

        for task in tasks:
            try:
                # existing HubSpot task creation logic
                created.append(task)
            except Exception as e:
                failed.append({"task": task, "error": str(e)})

        return {
            "created": created,
            "failed": failed,
        }


    def _execute_hubspot_approval_workflow(self, entities):
        meeting = self.memory_repo.get_active_meeting()

        if not meeting:
            return {
                "message": "There is no active meeting to approve tasks for.",
                "metadata": {"error": "no_active_meeting"},
            }

        approved_indexes = entities.get("approved_task_indexes")

        # 🔒 HARD REQUIREMENT: explicit approval
        if not approved_indexes:
            return {
                "message": "No tasks were selected for approval.",
                "metadata": {"error": "no_tasks_selected"},
            }

        if not meeting.action_items:
            return {
                "message": "There are no pending tasks to approve.",
                "metadata": {"status": "no_pending_tasks"},
            }

        # 🧠 Filter to ONLY approved tasks
        approved_tasks = [
            task
            for idx, task in enumerate(meeting.action_items)
            if idx in approved_indexes
        ]

        if not approved_tasks:
            return {
                "message": "Selected tasks do not match pending tasks.",
                "metadata": {"error": "task_mismatch"},
            }

        from app.tools.hubspot_tasks import create_selected_hubspot_tasks

        result = create_selected_hubspot_tasks(
            tasks=approved_tasks,
            meeting_id=meeting.id,
            memory_repo=self.memory_repo,
        )

        # 🔥 Remove only approved tasks from meeting
        remaining_tasks = [
            task
            for idx, task in enumerate(meeting.action_items)
            if idx not in approved_indexes
        ]

        self.memory_repo.update_meeting(
            meeting.id,
            MeetingUpdate(action_items=remaining_tasks),
        )

        return {
            "message": f"Added {len(result.get('created', []))} tasks to HubSpot.",
            "metadata": result,
        }

