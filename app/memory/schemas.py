"""Pydantic schemas for memory operations."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class MeetingCreate(BaseModel):
    """Schema for creating a meeting record."""
    client_name: str
    meeting_date: datetime
    calendar_event_id: str
    zoom_meeting_id: Optional[str] = None
    transcript: Optional[str] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting record."""
    summary: Optional[str] = None
    decisions: Optional[List[str]] = None
    action_items: Optional[List[Dict[str, Any]]] = None


class MemoryEntryCreate(BaseModel):
    """Schema for creating a memory entry."""
    meeting_id: Optional[int] = None
    key: str
    value: str
    metadata: Optional[Dict[str, Any]] = None


class CommitmentCreate(BaseModel):
    """Schema for creating a commitment."""
    meeting_id: int
    action_item_text: str
    hubspot_task_id: Optional[str] = None
    due_date: Optional[datetime] = None
