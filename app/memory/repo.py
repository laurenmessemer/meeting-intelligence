"""Memory repository - read/write operations only."""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.memory.models import Meeting, MemoryEntry, Commitment, Interaction
from app.memory.schemas import MeetingCreate, MeetingUpdate, MemoryEntryCreate, CommitmentCreate


class MemoryRepo:
    """Repository for memory operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Meeting operations
    def create_meeting(self, meeting_data: MeetingCreate) -> Meeting:
        """Create a new meeting record."""
        meeting = Meeting(**meeting_data.dict())
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)
        return meeting
    
    def get_meeting_by_calendar_id(self, calendar_event_id: str) -> Optional[Meeting]:
        """Get meeting by calendar event ID."""
        return self.db.query(Meeting).filter(Meeting.calendar_event_id == calendar_event_id).first()
    
    def get_recent_meeting_by_client(self, client_name: str, limit: int = 1) -> Optional[Meeting]:
        """Get most recent meeting for a client."""
        return self.db.query(Meeting).filter(
            Meeting.client_name.ilike(f"%{client_name}%")
        ).order_by(Meeting.meeting_date.desc()).limit(limit).first()
    
    def update_meeting(self, meeting_id: int, update_data: MeetingUpdate) -> Meeting:
        """Update meeting with summary, decisions, action items."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        if update_data.summary:
            meeting.summary = update_data.summary
        if update_data.decisions:
            meeting.decisions = update_data.decisions
        if update_data.action_items:
            meeting.action_items = update_data.action_items
        
        meeting.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(meeting)
        return meeting
    
    # Memory entry operations
    def create_memory_entry(self, entry_data: MemoryEntryCreate) -> MemoryEntry:
        """Create a memory entry."""
        data = entry_data.dict()
        # Map metadata to meta_data to avoid SQLAlchemy reserved name conflict
        if "metadata" in data:
            data["meta_data"] = data.pop("metadata")
        entry = MemoryEntry(**data)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_memory_by_key(self, key: str, limit: int = 10) -> List[MemoryEntry]:
        """Get memory entries by key."""
        return self.db.query(MemoryEntry).filter(MemoryEntry.key == key).order_by(
            MemoryEntry.created_at.desc()
        ).limit(limit).all()
    
    def get_memory_for_client(self, client_name: str) -> List[MemoryEntry]:
        """Get memory entries related to a client."""
        meetings = self.db.query(Meeting).filter(
            Meeting.client_name.ilike(f"%{client_name}%")
        ).all()
        meeting_ids = [m.id for m in meetings]
        return self.db.query(MemoryEntry).filter(
            MemoryEntry.meeting_id.in_(meeting_ids)
        ).all()
    
    # Commitment operations
    def create_commitment(self, commitment_data: CommitmentCreate) -> Commitment:
        """Create a commitment record."""
        commitment = Commitment(**commitment_data.dict())
        self.db.add(commitment)
        self.db.commit()
        self.db.refresh(commitment)
        return commitment
    
    def get_commitments_by_meeting(self, meeting_id: int) -> List[Commitment]:
        """Get all commitments for a meeting."""
        return self.db.query(Commitment).filter(Commitment.meeting_id == meeting_id).all()
    
    def update_commitment_status(self, commitment_id: int, status: str) -> Commitment:
        """Update commitment status."""
        commitment = self.db.query(Commitment).filter(Commitment.id == commitment_id).first()
        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found")
        
        commitment.status = status
        commitment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(commitment)
        return commitment
    
    # Interaction operations
    def create_interaction(self, user_message: str, intent: str, response: str, 
                          workflow: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Interaction:
        """Create an interaction record."""
        interaction = Interaction(
            user_message=user_message,
            intent=intent,
            workflow=workflow,
            response=response,
            meta_data=metadata  # Use meta_data to avoid SQLAlchemy reserved name
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction
