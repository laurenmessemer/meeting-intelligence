"""Chat API endpoint - receives messages, calls orchestrator."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.agent.orchestrator import Orchestrator
from app.memory.repo import MemoryRepo

router = APIRouter()


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str


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
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Create orchestrator with memory repo
    memory_repo = MemoryRepo(db)
    orchestrator = Orchestrator(memory_repo)
    
    # Process message
    result = orchestrator.process_message(request.message)
    
    return ChatResponse(
        message=result.get("message", ""),
        metadata=result.get("metadata", {})
    )
