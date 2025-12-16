from app.integrations.hubspot import create_task, HubSpotIntegrationError
from app.memory.repo import MemoryRepo
from dateutil import parser
from datetime import datetime
import logging


logger = logging.getLogger(__name__)

def _parse_deadline(deadline_raw):
    """
    Convert LLM-generated deadline text into a datetime.
    Returns None if parsing fails or deadline is empty.
    """
    if not deadline_raw:
        return None

    if isinstance(deadline_raw, datetime):
        return deadline_raw

    if isinstance(deadline_raw, str):
        try:
            parsed = parser.parse(deadline_raw, fuzzy=True)
            return parsed
        except Exception as e:
            logger.warning(
                f"[HUBSPOT DEADLINE PARSE FAILED] raw='{deadline_raw}' error={e}"
            )
            return None

    return None



def create_selected_hubspot_tasks(
    *,
    tasks: list,
    meeting_id: int,
    memory_repo: MemoryRepo,
):
    created = []
    failed = []

    meeting = memory_repo.get_meeting(meeting_id)

    for task in tasks:
        try:
            deadline_raw = task.get("deadline")
            due_date = _parse_deadline(deadline_raw)

            logger.info(
                f"[HUBSPOT TASK PREP] text='{task.get('text')}' "
                f"raw_deadline='{deadline_raw}' parsed_deadline='{due_date}'"
            )

            task_id = create_task(
                action_item_text=task.get("text"),
                due_date=due_date,
                company_id=meeting.hubspot_company_id if meeting else None,
            )


            created.append(task.get("text"))

        except HubSpotIntegrationError as e:
            failed.append({
                "text": task.get("text"),
                "error": str(e),
            })

    return {
        "created": created,
        "failed": failed,
    }
