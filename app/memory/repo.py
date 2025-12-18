"""Memory repository - read/write operations only."""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.memory.models import Meeting, MemoryEntry, Commitment, Interaction
from app.memory.schemas import MeetingCreate, MeetingUpdate, MemoryEntryCreate, CommitmentCreate

class MemoryRepo:
    """Repository for memory operations."""
    
    def __init__(self, db: Session):
        self.session = db

    # Client resolution operations
    def get_distinct_client_names(self, limit: int = 200):
        rows = (
            self.session.query(Meeting.client_name)
            .filter(Meeting.client_name.isnot(None))
            .filter(Meeting.client_name != "")
            .distinct()
            .limit(limit)
            .all()
        )
        return [r[0] for r in rows]


    # Meeting operations
    def create_meeting(self, meeting_data: MeetingCreate) -> Meeting:
        """Create a new meeting record."""
        meeting = Meeting(**meeting_data.dict())
        self.session.add(meeting)
        self.session.commit()
        self.session.refresh(meeting)
        return meeting
    
    def get_meeting_by_calendar_id(self, calendar_event_id: str) -> Optional[Meeting]:
        """Get meeting by calendar event ID."""
        return self.session.query(Meeting).filter(Meeting.calendar_event_id == calendar_event_id).first()
    
    def get_recent_meeting_by_client(self, client_name: str, limit: int = 1) -> Optional[Meeting]:
        """Get most recent meeting for a client."""
        return self.session.query(Meeting).filter(
            Meeting.client_name.ilike(f"%{client_name}%")
        ).order_by(Meeting.meeting_date.desc()).limit(limit).first()
    
    def get_most_recent_meeting(self):

        return (
            self.session.query(Meeting)
            .order_by(Meeting.meeting_date.desc())
            .first()
        )

    def get_next_upcoming_meeting(self, client_name: Optional[str] = None):
        """
        Returns the next upcoming meeting.
        If client_name is provided, scopes to that client.
        """

        query = (
            self.session.query(Meeting)
            .filter(Meeting.meeting_date >= datetime.utcnow())
        )

        if client_name:
            query = query.filter(Meeting.client_name.ilike(f"%{client_name}%"))

        return (
            query
            .order_by(Meeting.meeting_date.asc())
            .first()
        )

    def update_meeting(self, meeting_id: int, update_data: MeetingUpdate) -> Meeting:
        """Update meeting with summary, decisions, action items."""
        meeting = self.session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        if update_data.summary:
            meeting.summary = update_data.summary
        if update_data.decisions:
            meeting.decisions = update_data.decisions
        if update_data.action_items:
            meeting.action_items = update_data.action_items
        
        meeting.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(meeting)
        return meeting
    
    def set_active_meeting(self, meeting_id: int) -> None:
        """
        Persistently marks a meeting as active.
        Clears any previously active meeting.
        """
        # Clear existing active meeting(s)
        self.session.query(Meeting).filter(Meeting.is_active == True).update(
            {"is_active": False}
        )

        meeting = self.session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.is_active = True
            self.session.commit()

    def get_active_meeting(self) -> Optional[Meeting]:
        """
        Returns the most recently active meeting.
        """
        return (
            self.session.query(Meeting)
            .filter(Meeting.is_active == True)
            .order_by(Meeting.meeting_date.desc())
            .first()
        )

    def update_meeting_company(self, meeting_id: int, hubspot_company_id: str):
        meeting = (
            self.session.query(Meeting)
            .filter(Meeting.id == meeting_id)
            .first()
        )
        if meeting:
            meeting.hubspot_company_id = hubspot_company_id
            self.session.commit()

    def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        return (
            self.session.query(Meeting)
            .filter(Meeting.id == meeting_id)
            .first()
        )


    # Memory entry operations
    def create_memory_entry(self, entry_data: MemoryEntryCreate) -> MemoryEntry:
        """Create a memory entry."""
        data = entry_data.dict()
        # Map metadata to meta_data to avoid SQLAlchemy reserved name conflict
        if "metadata" in data:
            data["meta_data"] = data.pop("metadata")
        entry = MemoryEntry(**data)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry
    
    def get_memory_by_key(self, key: str, limit: int = 10) -> List[MemoryEntry]:
        """Get memory entries by key."""
        return self.session.query(MemoryEntry).filter(MemoryEntry.key == key).order_by(
            MemoryEntry.created_at.desc()
        ).limit(limit).all()
    
    def get_memory_for_client(self, client_name: str) -> List[MemoryEntry]:
        """Get memory entries related to a client."""
        meetings = self.session.query(Meeting).filter(
            Meeting.client_name.ilike(f"%{client_name}%")
        ).all()
        meeting_ids = [m.id for m in meetings]
        return self.session.query(MemoryEntry).filter(
            MemoryEntry.meeting_id.in_(meeting_ids)
        ).all()


    
    # Commitment operations
    def create_commitment(self, commitment_data: CommitmentCreate) -> Commitment:
        """Create a commitment record."""
        commitment = Commitment(**commitment_data.dict())
        self.session.add(commitment)
        self.session.commit()
        self.session.refresh(commitment)
        return commitment
    
    def get_commitments_by_meeting(self, meeting_id: int) -> List[Commitment]:
        """Get all commitments for a meeting."""
        return self.session.query(Commitment).filter(Commitment.meeting_id == meeting_id).all()
    
    def update_commitment_status(self, commitment_id: int, status: str) -> Commitment:
        """Update commitment status."""
        commitment = self.session.query(Commitment).filter(Commitment.id == commitment_id).first()
        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found")
        
        commitment.status = status
        commitment.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(commitment)
        return commitment
    
    def get_pending_commitments(self, meeting_id: int) -> List[Commitment]:
        """Return all pending commitments for a meeting."""
        return (
            self.session.query(Commitment)
            .filter(
                Commitment.meeting_id == meeting_id,
                Commitment.status == "pending",
            )
            .all()
        )

    def mark_commitment_created(
        self,
        commitment_id: int,
        hubspot_task_id: str,
    ) -> Commitment:
        """Mark commitment as successfully created in HubSpot."""
        commitment = (
            self.session.query(Commitment)
            .filter(Commitment.id == commitment_id)
            .first()
        )
        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found")

        commitment.hubspot_task_id = hubspot_task_id
        commitment.status = "created"
        commitment.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(commitment)
        return commitment

    def mark_commitment_failed(self, commitment_id: int) -> Commitment:
        """Mark commitment as failed during HubSpot creation."""
        commitment = (
            self.session.query(Commitment)
            .filter(Commitment.id == commitment_id)
            .first()
        )
        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found")

        commitment.status = "failed"
        commitment.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(commitment)
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
        self.session.add(interaction)
        self.session.commit()
        self.session.refresh(interaction)
        return interaction


    def get_last_interaction(self) -> Optional[Interaction]:
        """
        Returns the most recent interaction.
        """
        return (
            self.session.query(Interaction)
            .order_by(Interaction.created_at.desc())
            .first()
        )


    def get_recent_interactions(self, limit: int = 3) -> List[Interaction]:
        """
        Returns the most recent N interactions.
        """
        return (
            self.session.query(Interaction)
            .order_by(Interaction.created_at.desc())
            .limit(limit)
            .all()
        )
