"""Initialize database tables."""
from app.db.session import engine, Base
from app.memory.models import Meeting, MemoryEntry, Commitment, Interaction

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

