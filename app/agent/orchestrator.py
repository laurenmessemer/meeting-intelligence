"""Agent orchestrator - coordinates all operations, owns control flow."""
from typing import Dict, Any, Optional
from datetime import datetime
from app.agent.intents import recognize_intent
from app.agent.workflows import MEETING_SUMMARY_WORKFLOW
from app.agent.commitments import create_commitments_from_action_items
from app.memory.repo import MemoryRepo
from app.integrations.calendar import get_most_recent_meeting_by_client
from app.integrations.zoom import extract_zoom_meeting_id, fetch_zoom_transcript
from app.tools.summarize import summarize_meeting
from app.memory.schemas import MeetingCreate, MeetingUpdate


class Orchestrator:
    """Coordinates agent operations - no SQL, HTTP, or LLM prompts here."""
    
    def __init__(self, memory_repo: MemoryRepo):
        self.memory_repo = memory_repo
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Main entry point - processes user message through full workflow.
        
        Returns:
            Response dict with message and metadata
        """
        # Step 1: Recognize intent
        intent_result = recognize_intent(user_message)
        intent = intent_result.get("intent")
        entities = intent_result.get("entities", {})
        
        # Step 2: Select workflow
        workflow = None
        if intent == "summarize_meeting":
            workflow = MEETING_SUMMARY_WORKFLOW
            response = self._execute_meeting_summary_workflow(user_message, entities)
        else:
            # Unknown intent - return default response
            response = {
                "message": "I can help you summarize meetings. Try asking: 'Summarize my last meeting with [client name]'",
                "metadata": {"intent": intent}
            }
        
        # Step 3: Save interaction
        self.memory_repo.create_interaction(
            user_message=user_message,
            intent=intent,
            workflow=workflow.get("name") if workflow else None,
            response=response.get("message", ""),
            metadata=response.get("metadata", {})
        )
        
        return response
    
    def _execute_meeting_summary_workflow(self, user_message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the meeting summary workflow.
        
        Steps:
        1. Resolve meeting (find calendar event)
        2. Extract transcript if available
        3. Retrieve memory context
        4. Summarize meeting
        5. Create commitments (HubSpot tasks)
        6. Save memory
        """
        # Step 1: Resolve meeting
        client_name = entities.get("client_name")
        if not client_name:
            return {
                "message": "I couldn't identify which client meeting you're referring to. Please specify the client name.",
                "metadata": {"error": "missing_client_name"}
            }
        
        # Find most recent meeting for client
        calendar_event = get_most_recent_meeting_by_client(client_name)
        if not calendar_event:
            return {
                "message": f"I couldn't find any recent meetings with {client_name}. Please check your calendar.",
                "metadata": {"error": "meeting_not_found", "client_name": client_name}
            }
        
        # Check if meeting already exists in memory
        existing_meeting = self.memory_repo.get_meeting_by_calendar_id(calendar_event["id"])
        
        # Step 2: Extract transcript
        zoom_meeting_id = extract_zoom_meeting_id(calendar_event)
        transcript = None
        if zoom_meeting_id:
            transcript = fetch_zoom_transcript(zoom_meeting_id)
        
        # Step 3: Create or update meeting record
        if not existing_meeting:
            # Parse meeting date (handle both datetime and date-only formats)
            start_str = calendar_event["start"]
            try:
                if "T" in start_str:
                    # Datetime format
                    meeting_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    # Date-only format
                    meeting_date = datetime.fromisoformat(start_str)
            except ValueError:
                # Fallback to current time if parsing fails
                meeting_date = datetime.utcnow()
            
            meeting = self.memory_repo.create_meeting(MeetingCreate(
                client_name=client_name,
                meeting_date=meeting_date,
                calendar_event_id=calendar_event["id"],
                zoom_meeting_id=zoom_meeting_id,
                transcript=transcript
            ))
        else:
            meeting = existing_meeting
            # Update transcript if we got one and it's missing
            if transcript and not meeting.transcript:
                # Note: This would require adding update_transcript method to repo
                # For now, we'll proceed with existing transcript or new one
                pass
        
        # Step 4: Retrieve memory context
        memory_entries = self.memory_repo.get_memory_for_client(client_name)
        memory_context = "\n".join([
            f"{entry.key}: {entry.value}" for entry in memory_entries[:5]  # Last 5 entries
        ])
        
        # Step 5: Summarize meeting
        meeting_metadata = {
            "date": calendar_event.get("start", ""),
            "attendees": calendar_event.get("attendees", []),
            "client_name": client_name
        }
        
        summary_result = summarize_meeting(
            transcript=transcript or meeting.transcript,
            meeting_metadata=meeting_metadata,
            memory_context=memory_context
        )
        
        # Step 6: Update meeting with summary
        self.memory_repo.update_meeting(meeting.id, MeetingUpdate(
            summary=summary_result["summary"],
            decisions=summary_result["decisions"],
            action_items=summary_result["action_items"]
        ))
        
        # Step 7: Create commitments (HubSpot tasks)
        action_items = summary_result.get("action_items", [])
        commitments = []
        if action_items:
            commitments = create_commitments_from_action_items(
                action_items=action_items,
                meeting_id=meeting.id,
                memory_repo=self.memory_repo
            )
        
        # Step 8: Save memory entries (client preferences, etc.)
        # Extract any preferences from summary and save
        if summary_result.get("summary"):
            from app.memory.schemas import MemoryEntryCreate
            self.memory_repo.create_memory_entry(MemoryEntryCreate(
                meeting_id=meeting.id,
                key="meeting_summary",
                value=summary_result["summary"][:500],  # Truncate for storage
                metadata={"client": client_name}
            ))
        
        # Step 9: Format response
        commitments_count = len(commitments)
        response_message = f"""**Meeting Summary for {client_name}**

{summary_result['summary']}

**Decisions:**
{chr(10).join(f"- {d}" for d in summary_result.get('decisions', [])) if summary_result.get('decisions') else "None"}

**Action Items:**
{chr(10).join(f"- {item.get('text', '')}" for item in action_items) if action_items else "None"}

{f'{commitments_count} task(s) created in HubSpot.' if commitments_count > 0 else ''}
"""
        
        return {
            "message": response_message,
            "metadata": {
                "meeting_id": meeting.id,
                "client_name": client_name,
                "commitments_created": commitments_count,
                "has_transcript": bool(transcript or meeting.transcript)
            }
        }
