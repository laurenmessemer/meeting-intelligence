"""Summarization tool - LLM-powered, stateless."""
import json
from typing import Dict, Any, List, Optional
from app.llm.client import chat
from app.llm.prompts import MEETING_SUMMARY_SYSTEM, MEETING_SUMMARY_USER


def summarize_meeting(transcript: Optional[str], meeting_metadata: Dict[str, Any], 
                     memory_context: str = "") -> Dict[str, Any]:
    """
    Summarize a meeting using LLM.
    
    Args:
        transcript: Meeting transcript text (can be None)
        meeting_metadata: Dict with date, attendees, client_name, etc.
        memory_context: Relevant memory entries as formatted string
    
    Returns:
        {
            "summary": str,
            "decisions": List[str],
            "action_items": List[Dict] with text, owner, deadline
        }
    """
    # Format attendees
    attendees = meeting_metadata.get('attendees', [])
    attendees_str = ", ".join(attendees) if attendees else "Unknown"
    
    # Format transcript or indicate missing
    transcript_text = transcript if transcript else "[Transcript not available - summary based on calendar metadata only]"
    
    # Build prompt
    prompt = MEETING_SUMMARY_USER.format(
        meeting_date=meeting_metadata.get('date', 'Unknown'),
        attendees=attendees_str,
        client_name=meeting_metadata.get('client_name', 'Unknown'),
        memory_context=memory_context or "No previous context available.",
        transcript=transcript_text
    )
    
    # Call LLM
    response_text = chat(
        prompt=prompt,
        system_prompt=MEETING_SUMMARY_SYSTEM,
        temperature=0.7,
        response_format={"response_mime_type": "application/json"}
    )
    
    # Parse JSON response
    try:
        result = json.loads(response_text)
        return {
            "summary": result.get("summary", ""),
            "decisions": result.get("decisions", []),
            "action_items": result.get("action_items", [])
        }
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "summary": response_text,
            "decisions": [],
            "action_items": []
        }
