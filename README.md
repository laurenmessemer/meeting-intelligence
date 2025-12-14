# Meeting Intelligence Agent v1

A minimal, general-purpose agent framework with a fully implemented meeting intelligence workflow.

## Overview

This is a production-quality Python agent that demonstrates coordination, memory, and determinism. The agent accepts chat messages, recognizes intent, executes workflows, and integrates with real systems (Google Calendar, Zoom, HubSpot).

## Architecture

The framework emphasizes:
- **Coordination over LLM cleverness**: Code coordinates, LLMs reason
- **Deterministic outcomes**: Predictable behavior through explicit policies
- **Persistent memory**: Cross-session personalization
- **Single responsibility**: Each file has one clear purpose

## Directory Structure

```
app/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration management
├── api/                   # API layer
│   ├── chat.py           # POST /api/chat endpoint
│   └── ui.py             # HTML chat UI
├── agent/                 # Agent core
│   ├── orchestrator.py   # Control flow coordinator
│   ├── intents.py        # Intent recognition
│   ├── workflows.py      # Workflow definitions
│   └── commitments.py    # Task creation logic
├── llm/                   # LLM layer
│   ├── client.py         # Gemini API wrapper
│   └── prompts.py        # All prompts
├── tools/                 # LLM-powered tools
│   ├── summarize.py      # Meeting summarization
│   ├── meeting_brief.py  # Stub
│   └── followup.py       # Follow-up email generation
├── integrations/          # External integrations
│   ├── calendar.py       # Google Calendar
│   ├── zoom.py           # Zoom transcript
│   ├── hubspot.py        # HubSpot tasks
│   └── gmail.py          # Stub
├── memory/                # Memory system
│   ├── models.py         # SQLAlchemy models
│   ├── repo.py           # Memory operations
│   └── schemas.py        # Pydantic schemas
└── db/                    # Database
    └── session.py         # SQLAlchemy session
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required configuration:
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_CREDENTIALS_PATH`: Path to Google OAuth credentials JSON
- `HUBSPOT_API_KEY`: HubSpot API key (for task creation)

### 3. Initialize Database

```bash
# Create database tables
python -c "from app.db.session import engine, Base; from app.memory.models import *; Base.metadata.create_all(bind=engine)"
```

### 4. Run the Application

```bash
python -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`

## Usage

### Chat Interface

Navigate to `http://localhost:8000` to access the web chat interface.

### API Endpoint

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize my last meeting with MTCA"}'
```

## Workflow: Meeting Summary

The implemented workflow handles requests like:
- "Summarize my last meeting with [client name]"

**Execution steps:**
1. Recognize intent and extract client name
2. Find most recent calendar meeting for client
3. Extract Zoom meeting ID from calendar event
4. Fetch transcript (if available)
5. Summarize meeting using LLM
6. Extract decisions and action items
7. Create HubSpot tasks for action items
8. Save summary and memory
9. Return formatted response

## Key Design Principles

1. **Orchestrator owns control flow**: All coordination happens in `orchestrator.py`
2. **No unnecessary abstractions**: Direct, clear code paths
3. **Deterministic policies**: Task creation rules are code, not LLM prompts
4. **Memory persistence**: All interactions and summaries are stored
5. **Graceful degradation**: Works with or without transcripts

## Notes

- Zoom transcript fetching is stubbed (requires Zoom API implementation)
- Gmail integration is stubbed
- Meeting brief tool is stubbed
- The framework is designed for extension with additional workflows

## License

See LICENSE file.
