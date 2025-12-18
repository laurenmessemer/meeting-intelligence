"""Chat API endpoint - receives messages, calls orchestrator."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.agent.orchestrator import Orchestrator
from app.memory.repo import MemoryRepo
from typing import Optional
from app.runtime.mode import is_demo_mode
from datetime import datetime

router = APIRouter()


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChatRequest(BaseModel):
    message: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[dict] = None



class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str
    metadata: dict = {}


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    POST /api/chat
    
    Receives user message, calls orchestrator, returns response.
    No reasoning. No orchestration logic.
    """
    if not request.message and not request.intent:
        raise HTTPException(
            status_code=400,
            detail="Either message or intent must be provided"
        )

    
    # Create orchestrator with memory repo
    memory_repo = MemoryRepo(db)


    # If in demo mode, create a demo meeting
    if is_demo_mode():
        existing_meeting = memory_repo.get_most_recent_meeting()
        if not existing_meeting:
            memory_repo.create_meeting(
                MeetingCreate(
                    client_name="Good Health",
                    meeting_date=datetime.utcnow(),
                    calendar_event_id="demo_event_001",
                    zoom_meeting_id="12345678901",
                    transcript=None,
                )
            )

    orchestrator = Orchestrator(memory_repo)
    
    # Process message
    result = orchestrator.process_message(
        user_message=request.message or "",
        intent_override=request.intent,
        entities_override=request.entities,
    )

    
    return ChatResponse(
        message=result.get("message", ""),
        metadata=result.get("metadata", {})
    )
