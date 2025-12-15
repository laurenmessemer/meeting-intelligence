"""HubSpot integration - create tasks deterministically."""
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import Config
import logging
logger = logging.getLogger(__name__)


class HubSpotIntegrationError(Exception):
    """Raised when a HubSpot API request fails in a controlled way."""
    pass


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
        logger.info("HubSpot disabled: HUBSPOT_API_KEY not configured")
        return None

    # Deterministic fingerprint for idempotency (lightweight)
    task_fingerprint = action_item_text.strip().lower()[:80]

    # Default due date: +3 business days
    if not due_date:
        due_date = datetime.utcnow() + timedelta(days=3)
        # Skip weekends (simple implementation)
        while due_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            due_date += timedelta(days=1)
    
    url = "https://api.hubapi.com/crm/v3/objects/tasks"
    
    # headers = {
    #     "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    
    payload = {
        "properties": {
            "hs_task_subject": action_item_text[:100],  # HubSpot limit
            "hs_task_body": (
                f"[AUTO-GENERATED | fingerprint={task_fingerprint}]\n\n"
                f"{action_item_text}"
            ),
            "hs_task_status": "NOT_STARTED",
            "hs_timestamp": int(due_date.timestamp() * 1000),  # HubSpot expects milliseconds
        }
    }
    

    try:
        response = requests.post(
            "https://api.hubapi.com/crm/v3/objects/tasks",
            json=payload,
            headers={
                "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        response.raise_for_status()
        return response.json().get("id")

    except requests.RequestException as e:
        logger.warning("HubSpot request failed", exc_info=e)
        raise HubSpotIntegrationError("HubSpot API request failed") from e


    except HubSpotIntegrationError as e:
        logger.warning(str(e), exc_info=e)
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
