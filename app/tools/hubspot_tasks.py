from app.integrations.hubspot import create_task, HubSpotIntegrationError
from app.memory.repo import MemoryRepo



def create_approved_hubspot_tasks(
    meeting_id: int,
    memory_repo: MemoryRepo,
):
    pending_commitments = memory_repo.get_pending_commitments(meeting_id)

    created = []
    failed = []

    for commitment in pending_commitments:
        try:
            meeting = memory_repo.get_meeting(meeting_id)

            task_id = create_task(
                action_item_text=commitment.action_item_text,
                due_date=commitment.due_date,
                company_id=meeting.hubspot_company_id if meeting else None,
            )

            memory_repo.mark_commitment_created(
                commitment_id=commitment.id,
                hubspot_task_id=task_id,
            )

            created.append(commitment.action_item_text)

        except HubSpotIntegrationError as e:
            memory_repo.mark_commitment_failed(commitment.id)
            failed.append({
                "text": commitment.action_item_text,
                "error": str(e),
            })


    return {"created": created, "failed": failed}
