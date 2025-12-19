"""Initialize database tables."""
from app.db.session import engine, Base
from app.memory.models import Meeting, MemoryEntry, Commitment, Interaction


def init_db() -> None:
    """
    Create database tables if they do not exist.

    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)