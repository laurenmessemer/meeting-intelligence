"""HubSpot integration - create tasks deterministically."""
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import Config


def create_task(action_item_text: str, due_date: Optional[datetime] = None) -> Optional[str]:
    """
    Create a HubSpot task for an action item.
    
    Args:
        action_item_text: Description of the action item
        due_date: Due date (defaults to +3 business days if not provided)
    
    Returns:
        HubSpot task ID or None if creation failed
    """
    if not Config.HUBSPOT_API_KEY:
        raise ValueError("HUBSPOT_API_KEY not configured")
    
    # Default due date: +3 business days
    if not due_date:
        due_date = datetime.utcnow() + timedelta(days=3)
        # Skip weekends (simple implementation)
        while due_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            due_date += timedelta(days=1)
    
    url = "https://api.hubapi.com/crm/v3/objects/tasks"
    
    headers = {
        "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "properties": {
            "hs_task_subject": action_item_text[:100],  # HubSpot limit
            "hs_task_body": action_item_text,
            "hs_task_status": "NOT_STARTED",
            "hs_timestamp": int(due_date.timestamp() * 1000),  # HubSpot expects milliseconds
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result.get("id")
    except Exception as e:
        # Log error but don't fail the workflow
        print(f"HubSpot task creation failed: {e}")
        return None


def task_exists(task_id: str) -> bool:
    """
    Check if a HubSpot task exists (for idempotency).
    
    Args:
        task_id: HubSpot task ID
    
    Returns:
        True if task exists
    """
    if not Config.HUBSPOT_API_KEY:
        return False
    
    url = f"https://api.hubapi.com/crm/v3/objects/tasks/{task_id}"
    
    headers = {
        "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except Exception:
        return False
