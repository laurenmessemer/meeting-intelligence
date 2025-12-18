"""Configuration management - loads environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    

    # App mode - defaults to demo so a reviewer can run without credentials
    APP_MODE = (os.getenv("APP_MODE") or "demo").strip().lower()

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/meeting_intelligence")
    
    # LLM
    # New variables (primary)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # Default to gemini for backward compatibility
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    # Backward compatibility: fallback to old GEMINI_API_KEY if LLM_API_KEY not set
    _GEMINI_API_KEY_LEGACY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEY = LLM_API_KEY if LLM_API_KEY else _GEMINI_API_KEY_LEGACY
    
    # Google OAuth (Desktop App Flow)
    # New variables (primary)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_CLIENT_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "")  # Path to client_secrets.json
    GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")  # Default token storage
    GOOGLE_SCOPES = os.getenv("GOOGLE_SCOPES", "https://www.googleapis.com/auth/calendar.readonly").split(",")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    # Backward compatibility: fallback to old GOOGLE_CREDENTIALS_PATH if GOOGLE_CLIENT_SECRET_FILE not set
    _GOOGLE_CREDENTIALS_PATH_LEGACY = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
    GOOGLE_CREDENTIALS_PATH = GOOGLE_CLIENT_SECRET_FILE if GOOGLE_CLIENT_SECRET_FILE else _GOOGLE_CREDENTIALS_PATH_LEGACY
    
    # HubSpot
    HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY", "")
    HUBSPOT_PORTAL_ID = os.getenv("HUBSPOT_PORTAL_ID", "")
    
    # Zoom (Server-to-Server OAuth)
    # New variables (primary)
    ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID", "")
    ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID", "")
    ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET", "")
    
    # Backward compatibility: fallback to old ZOOM_API_KEY/ZOOM_API_SECRET if new vars not set
    _ZOOM_API_KEY_LEGACY = os.getenv("ZOOM_API_KEY", "")
    _ZOOM_API_SECRET_LEGACY = os.getenv("ZOOM_API_SECRET", "")
    ZOOM_API_KEY = ZOOM_CLIENT_ID if ZOOM_CLIENT_ID else _ZOOM_API_KEY_LEGACY
    ZOOM_API_SECRET = ZOOM_CLIENT_SECRET if ZOOM_CLIENT_SECRET else _ZOOM_API_SECRET_LEGACY
