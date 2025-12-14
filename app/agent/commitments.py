"""Commitment coordination - translate action items to HubSpot tasks deterministically."""
from typing import List, Dict, Any
from datetime import datetime
from app.integrations.hubspot import create_task, task_exists
from app.memory.repo import MemoryRepo


def create_commitments_from_action_items(action_items: List[Dict[str, Any]], 
                                        meeting_id: int, 
                                        memory_repo: MemoryRepo) -> List[Dict[str, Any]]:
    """
    Create HubSpot tasks from action items.
    
    Deterministic policy:
    - Each action item becomes a HubSpot task
    - Tasks assigned to user (default)
    - Due date = action item deadline or +3 business days
    
    Args:
        action_items: List of action item dicts with text, owner, deadline
        meeting_id: Meeting ID for tracking
        memory_repo: Memory repository instance
    
    Returns:
        List of commitment records created
    """
    commitments = []
    
    for action_item in action_items:
        action_text = action_item.get("text", "")
        if not action_text:
            continue
        
        # Parse deadline if provided
        due_date = None
        deadline_str = action_item.get("deadline")
        if deadline_str:
            try:
                due_date = datetime.fromisoformat(deadline_str)
            except (ValueError, TypeError):
                pass  # Use default
        
        # Create HubSpot task
        hubspot_task_id = create_task(action_text, due_date)
        
        # Create commitment record
        if hubspot_task_id:
            # Check for idempotency - see if commitment already exists
            from app.memory.models import Commitment
            existing = memory_repo.db.query(Commitment).filter(
                Commitment.hubspot_task_id == hubspot_task_id
            ).first()
            if existing:
                commitments.append(existing)
                continue
            
            from app.memory.schemas import CommitmentCreate
            commitment = memory_repo.create_commitment(CommitmentCreate(
                meeting_id=meeting_id,
                action_item_text=action_text,
                hubspot_task_id=hubspot_task_id,
                due_date=due_date
            ))
            commitments.append(commitment)
    
    return commitments
