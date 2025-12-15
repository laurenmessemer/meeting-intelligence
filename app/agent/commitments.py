from typing import List, Dict, Any
from datetime import datetime
from app.memory.repo import MemoryRepo
from app.memory.schemas import CommitmentCreate


def create_commitments_from_action_items(
    action_items: List[Dict[str, Any]],
    meeting_id: int,
    memory_repo: MemoryRepo,
):
    commitments = []

    for item in action_items:
        text = item.get("text")
        if not text:
            continue

        due_date = None
        if item.get("deadline"):
            try:
                due_date = datetime.fromisoformat(item["deadline"])
            except Exception:
                pass

        commitment = memory_repo.create_commitment(
            CommitmentCreate(
                meeting_id=meeting_id,
                action_item_text=text,
                due_date=due_date,
            )
        )

        commitments.append(commitment)

    return commitments
