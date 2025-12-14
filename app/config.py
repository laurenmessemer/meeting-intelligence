"""Configuration management - loads environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/meeting_intelligence")
    
    # LLM
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    # Google APIs
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    # HubSpot
    HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY", "")
    HUBSPOT_PORTAL_ID = os.getenv("HUBSPOT_PORTAL_ID", "")
    
    # Zoom (for transcript access)
    ZOOM_API_KEY = os.getenv("ZOOM_API_KEY", "")
    ZOOM_API_SECRET = os.getenv("ZOOM_API_SECRET", "")
