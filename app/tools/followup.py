"""Follow-up email generation tool - LLM-powered."""
from typing import Dict, Any, List
from app.llm.client import chat
from app.llm.prompts import FOLLOWUP_EMAIL_SYSTEM, FOLLOWUP_EMAIL_USER


def generate_followup_email(summary: str, decisions: List[str], action_items: List[Dict[str, Any]],
                           client_name: str, meeting_date: str, memory_context: str = "") -> str:
    """
    Generate polished follow-up email text.
    
    Args:
        summary: Meeting summary
        decisions: List of decisions
        action_items: List of action item dicts
        client_name: Client name
        meeting_date: Meeting date string
        memory_context: Relevant memory context
    
    Returns:
        Email body text
    """
    # Format decisions
    decisions_str = "\n".join(f"- {d}" for d in decisions) if decisions else "None"
    
    # Format action items
    action_items_str = "\n".join(
        f"- {item.get('text', '')} (Owner: {item.get('owner', 'TBD')}, Due: {item.get('deadline', 'TBD')})"
        for item in action_items
    ) if action_items else "None"
    
    prompt = FOLLOWUP_EMAIL_USER.format(
        summary=summary,
        decisions=decisions_str,
        action_items=action_items_str,
        client_name=client_name,
        meeting_date=meeting_date
    )
    
    email_text = chat(
        prompt=prompt,
        system_prompt=FOLLOWUP_EMAIL_SYSTEM,
        temperature=0.7
    )
    
    return email_text
