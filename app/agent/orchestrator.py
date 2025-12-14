"""Agent orchestrator - coordinates all operations, owns control flow."""

from typing import Dict, Any
from datetime import datetime, date
from dateutil import parser
from app.agent.intents import recognize_intent
from app.agent.workflows import MEETING_SUMMARY_WORKFLOW
from app.agent.commitments import create_commitments_from_action_items
from app.memory.repo import MemoryRepo
from app.integrations.calendar import (
    get_most_recent_meeting_by_client,
    get_meeting_by_client_and_date,
)
from app.integrations.zoom import extract_zoom_meeting_id, fetch_zoom_transcript
from app.tools.summarize import summarize_meeting
from app.memory.schemas import MeetingCreate, MeetingUpdate


class Orchestrator:
    """Coordinates agent operations - no SQL, HTTP, or LLM prompts here."""

    def __init__(self, memory_repo: MemoryRepo):
        self.memory_repo = memory_repo

    # ----------------------------
    # Helpers
    # ----------------------------

    def _parse_target_date(self, date_str: str) -> date:
        """
        Parse ISO or natural-language dates into a date object.
        If no year is specified, bias toward the next future occurrence.
        """
        print(f"DIAGNOSTIC: _parse_target_date() input: {repr(date_str)}")
        parsed = parser.parse(date_str, default=datetime.utcnow())
        parsed_date = parsed.date()
        print(f"DIAGNOSTIC: dateutil.parser result: {parsed} -> date: {parsed_date}")

        today = datetime.utcnow().date()
        print(f"DIAGNOSTIC: Today's date: {today}")

        # If user did NOT specify a year and the date is in the past,
        # assume they mean the next occurrence (next year)
        year_in_string = "20" in date_str
        print(f"DIAGNOSTIC: Year in string ('20' found): {year_in_string}")
        print(f"DIAGNOSTIC: Parsed date < today: {parsed_date < today}")
        
        if not year_in_string and parsed_date < today:
            original_date = parsed_date
            parsed_date = date(parsed_date.year + 1, parsed_date.month, parsed_date.day)
            print(f"DIAGNOSTIC: Adjusted year (no year in string + past date): {original_date} -> {parsed_date}")
        else:
            print(f"DIAGNOSTIC: No year adjustment needed")

        print(f"DIAGNOSTIC: Final parsed date: {parsed_date}")
        return parsed_date


    # ----------------------------
    # Public entry point
    # ----------------------------

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Main entry point - processes user message through full workflow.
        """
        intent_result = recognize_intent(user_message)
        intent = intent_result.get("intent")
        entities = intent_result.get("entities", {})

        workflow = None

        if intent == "summarize_meeting":
            workflow = MEETING_SUMMARY_WORKFLOW
            response = self._execute_meeting_summary_workflow(entities)
        else:
            response = {
                "message": (
                    "I can help you summarize meetings. "
                    "Try asking: 'Summarize my last meeting with [client name]'"
                ),
                "metadata": {"intent": intent},
            }

        self.memory_repo.create_interaction(
            user_message=user_message,
            intent=intent,
            workflow=workflow.get("name") if workflow else None,
            response=response.get("message", ""),
            metadata=response.get("metadata", {}),
        )

        return response

    # ----------------------------
    # Workflow execution
    # ----------------------------

    def _execute_meeting_summary_workflow(
        self, entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the meeting summary workflow.
        """

        # Step 1: Resolve meeting
        client_name = entities.get("client_name")
        if not client_name:
            return {
                "message": (
                    "I couldn't identify which client meeting you're referring to. "
                    "Please specify the client name."
                ),
                "metadata": {"error": "missing_client_name"},
            }

        date_str = entities.get("date")
        calendar_event = None
        
        print("=" * 80)
        print("DIAGNOSTIC: Orchestrator date resolution")
        print("=" * 80)
        print(f"DIAGNOSTIC: Raw entities: {entities}")
        print(f"DIAGNOSTIC: date_str from entities: {repr(date_str)}")
        print(f"DIAGNOSTIC: date_str is truthy: {bool(date_str)}")

        # --- DATE-AWARE RESOLUTION ---
        if date_str:
            print(f"\nDIAGNOSTIC: Entering date-aware resolution branch")
            try:
                print(f"DIAGNOSTIC: Parsing date_str: {repr(date_str)}")
                target_date = self._parse_target_date(date_str)
                print(f"DIAGNOSTIC: Parsed target_date: {target_date} (type: {type(target_date)})")
                print(f"DIAGNOSTIC: target_date.year: {target_date.year}")
                print(f"DIAGNOSTIC: Calling get_meeting_by_client_and_date()...")
                calendar_event = get_meeting_by_client_and_date(
                    client_name=client_name,
                    target_date=target_date,
                )
                print(f"DIAGNOSTIC: get_meeting_by_client_and_date() returned: {calendar_event is not None}")
                if calendar_event:
                    print(f"DIAGNOSTIC: Found event: {calendar_event.get('summary')} on {calendar_event.get('start')}")
            except Exception as e:
                print(f"DIAGNOSTIC: Exception during date parsing/lookup: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "message": (
                        f"I couldn't resolve the meeting date you requested "
                        f"({date_str}). Please try rephrasing."
                    ),
                    "metadata": {
                        "error": "date_resolution_failed",
                        "client_name": client_name,
                        "date": date_str,
                        "exception": str(e),
                    },
                }


            # If user explicitly asked for a date, do NOT silently fall back
            if not calendar_event:
                print(f"DIAGNOSTIC: No calendar_event found for date {date_str}, returning error")
                return {
                    "message": (
                        f"I couldn't find a meeting with {client_name} on {date_str}."
                    ),
                    "metadata": {
                        "error": "meeting_not_found_for_date",
                        "client_name": client_name,
                        "date": date_str,
                    },
                }
        else:
            print(f"DIAGNOSTIC: date_str is falsy, skipping date-aware branch")

        # --- MOST RECENT FALLBACK ---
        if not calendar_event:
            print(f"\nDIAGNOSTIC: calendar_event is None, entering fallback to get_most_recent_meeting_by_client()")
            print(f"DIAGNOSTIC: Fallback reason: {'date_str was falsy' if not date_str else 'date lookup returned None'}")
            calendar_event = get_most_recent_meeting_by_client(client_name)
            if calendar_event:
                print(f"DIAGNOSTIC: Fallback returned event: {calendar_event.get('summary')} on {calendar_event.get('start')}")
            else:
                print(f"DIAGNOSTIC: Fallback returned None")

        if not calendar_event:
            return {
                "message": (
                    f"I couldn't find any recent meetings with {client_name}. "
                    "Please check your calendar."
                ),
                "metadata": {
                    "error": "meeting_not_found",
                    "client_name": client_name,
                },
            }

        # Step 2: Check memory
        existing_meeting = self.memory_repo.get_meeting_by_calendar_id(
            calendar_event["id"]
        )

        # Step 3: Extract transcript
        zoom_meeting_id = extract_zoom_meeting_id(calendar_event)
        transcript = fetch_zoom_transcript(zoom_meeting_id) if zoom_meeting_id else None

        # Step 4: Create or reuse meeting record
        if not existing_meeting:
            start_str = calendar_event.get("start")

            try:
                if start_str and "T" in start_str:
                    meeting_date = datetime.fromisoformat(
                        start_str.replace("Z", "+00:00")
                    )
                elif start_str:
                    meeting_date = datetime.fromisoformat(start_str)
                else:
                    meeting_date = datetime.utcnow()
            except Exception:
                meeting_date = datetime.utcnow()

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

        # Step 5: Retrieve memory context
        memory_entries = self.memory_repo.get_memory_for_client(client_name)
        memory_context = "\n".join(
            f"{entry.key}: {entry.value}" for entry in memory_entries[:5]
        )

        # Step 6: Summarize
        meeting_metadata = {
            "date": calendar_event.get("start"),
            "attendees": calendar_event.get("attendees", []),
            "client_name": client_name,
        }

        summary_result = summarize_meeting(
            transcript=transcript or meeting.transcript,
            meeting_metadata=meeting_metadata,
            memory_context=memory_context,
        )

        # Step 7: Persist summary
        self.memory_repo.update_meeting(
            meeting.id,
            MeetingUpdate(
                summary=summary_result["summary"],
                decisions=summary_result["decisions"],
                action_items=summary_result["action_items"],
            ),
        )

        # Step 8: Commitments
        action_items = summary_result.get("action_items", [])
        commitments = []

        if action_items:
            commitments = create_commitments_from_action_items(
                action_items=action_items,
                meeting_id=meeting.id,
                memory_repo=self.memory_repo,
            )

        # Step 9: Memory entry
        if summary_result.get("summary"):
            from app.memory.schemas import MemoryEntryCreate

            self.memory_repo.create_memory_entry(
                MemoryEntryCreate(
                    meeting_id=meeting.id,
                    key="meeting_summary",
                    value=summary_result["summary"][:500],
                    metadata={"client": client_name},
                )
            )

        # Step 10: Response
        commitments_count = len(commitments)

        response_message = f"""**Meeting Summary for {client_name}**

{summary_result['summary']}

**Decisions:**
{chr(10).join(f"- {d}" for d in summary_result.get('decisions', [])) or "None"}

**Action Items:**
{chr(10).join(f"- {item.get('text', '')}" for item in action_items) or "None"}

{f"{commitments_count} task(s) created in HubSpot." if commitments_count else ""}
"""

        return {
            "message": response_message,
            "metadata": {
                "meeting_id": meeting.id,
                "client_name": client_name,
                "commitments_created": commitments_count,
                "has_transcript": bool(transcript or meeting.transcript),
            },
        }
