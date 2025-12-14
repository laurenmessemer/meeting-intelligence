"""Summarization tool - LLM-powered, stateless."""
import json
from typing import Dict, Any, List, Optional
from app.llm.client import chat
from app.llm.prompts import MEETING_SUMMARY_SYSTEM, MEETING_SUMMARY_USER


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Safely extract JSON from LLM output.
    Handles raw JSON and JSON wrapped in markdown fences.
    """
    text = text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first and last fence lines
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    return json.loads(text)


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
        result = _extract_json(response_text)
        return {
            "summary": result.get("summary", ""),
            "decisions": result.get("decisions", []),
            "action_items": result.get("action_items", [])
        }
    except Exception as e:
        print(f"DIAGNOSTIC: Failed to parse summary JSON: {e}")
        return {
            "summary": response_text.strip(),
            "decisions": [],
            "action_items": []
        }

