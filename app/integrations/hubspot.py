"""HubSpot integration - create tasks deterministically."""
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import Config
import logging
logger = logging.getLogger(__name__)
from app.runtime.mode import is_demo_mode



class HubSpotIntegrationError(Exception):
    """Raised when a HubSpot API request fails in a controlled way."""
    pass

def normalize_company_name(raw_name: str) -> str:
    """
    Normalize meeting titles or noisy client strings
    into a clean company name for HubSpot matching.
    """
    if not raw_name:
        return raw_name

    # Common patterns to strip
    blacklist_phrases = [
        "meeting",
        "call",
        "sync",
        "review",
        "crm",
        "college list",
        ":",
        "-",
    ]

    name = raw_name.lower()

    for phrase in blacklist_phrases:
        name = name.replace(phrase, "")

    # Collapse whitespace and title-case
    name = " ".join(name.split()).title()

    return name

def get_company_by_name(company_name: str):
    """
    Find a HubSpot company by name (best-effort).
    Returns company dict or None.
    """

    if is_demo_mode():
        return None

    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "name",
                        "operator": "CONTAINS_TOKEN",
                        "value": company_name,
                    }
                ]
            }
        ],
        "properties": ["name"],
        "limit": 1,
    }

    response = _hubspot_post("/crm/v3/objects/companies/search", payload)

    results = response.get("results", [])
    return results[0] if results else None

def get_or_create_company_id(company_name: str) -> str:
    """
    Resolve a HubSpot company ID by name.
    Creates the company if it does not exist.
    """

    if is_demo_mode():
        return "MTCA"

    company = get_company_by_name(company_name)
    if company:
        return company["id"]

    response = _hubspot_post(
        "/crm/v3/objects/companies",
        {"properties": {"name": company_name}},
    )
    return response["id"]

def _hubspot_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Internal helper for HubSpot POST requests.
    Raises HubSpotIntegrationError on failure.
    """
    if not Config.HUBSPOT_API_KEY:
        raise HubSpotIntegrationError("HubSpot API key not configured")

    url = f"https://api.hubapi.com{path}"

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.warning(f"HubSpot POST failed: {path}", exc_info=e)
        raise HubSpotIntegrationError("HubSpot API request failed") from e

def create_task(
    action_item_text: str,
    due_date: Optional[datetime],
    company_id: Optional[str] = None,
) -> str:
    """
    Create a HubSpot task for an action item.
    
    Args:
        action_item_text: Description of the action item
        due_date: Due date (defaults to +3 business days if not provided)
    
    Returns:
        HubSpot task ID or None if creation failed
    """

    if is_demo_mode():
        return "DEMO_TASK_ID"

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
        }
    }

    if due_date:
        payload["properties"]["hs_timestamp"] = int(due_date.timestamp() * 1000)

    

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
        task_id = response.json().get("id")

        # -------------------------------------------------
        # Associate task to company (if provided)
        # -------------------------------------------------
        if company_id:
            assoc_url = (
                f"https://api.hubapi.com/crm/v3/objects/tasks/"
                f"{task_id}/associations/companies/{company_id}/task_to_company"
            )

            assoc_response = requests.put(
                assoc_url,
                headers={
                    "Authorization": f"Bearer {Config.HUBSPOT_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=5,
            )

            # We do NOT raise here — association failure should not kill task creation
            if assoc_response.status_code not in (200, 201, 204):
                logger.warning(
                    f"Failed to associate task {task_id} to company {company_id}: "
                    f"{assoc_response.text}"
                )

        return task_id

        

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
