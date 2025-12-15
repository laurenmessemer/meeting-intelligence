"""SQLAlchemy models for persistent memory."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Meeting(Base):
    """Stored meeting information."""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    meeting_date = Column(DateTime)
    calendar_event_id = Column(String, unique=True)
    zoom_meeting_id = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    decisions = Column(JSON, nullable=True)  # List of decision strings
    action_items = Column(JSON, nullable=True)  # List of action item dicts
    
    hubspot_company_id = Column(String, nullable=True)

    is_active = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    # Relationships
    memory_entries = relationship("MemoryEntry", back_populates="meeting")
    commitments = relationship("Commitment", back_populates="meeting")


class MemoryEntry(Base):
    """Contextual memory entries for personalization."""
    __tablename__ = "memory_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    key = Column(String, index=True)  # e.g., "client_preference", "context"
    value = Column(Text)
    meta_data = Column("metadata", JSON, nullable=True)  # Using meta_data to avoid SQLAlchemy reserved name
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="memory_entries")


class Commitment(Base):
    """Tracked commitments (e.g., HubSpot tasks)."""
    __tablename__ = "commitments"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    action_item_text = Column(Text)
    hubspot_task_id = Column(String, nullable=True, unique=True)
    status = Column(String, default="pending")  # pending, completed, cancelled
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="commitments")


class Interaction(Base):
    """User interaction history."""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    intent = Column(String)
    workflow = Column(String, nullable=True)
    response = Column(Text)
    meta_data = Column("metadata", JSON, nullable=True)  # Using meta_data to avoid SQLAlchemy reserved name
    created_at = Column(DateTime, default=datetime.utcnow)
