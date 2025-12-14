# Application Directory Structure and File Inventory

Complete documentation of the Meeting Intelligence Agent application structure, responsibilities, and interactions.

---

## Root Directory

**Purpose:**  
Project root containing application entry points, configuration files, and documentation.

#### File: init_db.py

- **Responsibility:**  
  Database initialization script that creates all SQLAlchemy tables defined in the memory models.

- **What it should contain:**  
  Import statements for database engine, Base, and all model classes. Execution logic that calls `Base.metadata.create_all()` to create tables.

- **What it should NOT contain:**  
  Application logic, API endpoints, or runtime configuration. Should not modify existing data or perform migrations.

- **Dependencies:**  
  `app.db.session` (engine, Base), `app.memory.models` (Meeting, MemoryEntry, Commitment, Interaction).

- **Used by:**  
  Run manually during initial setup or when database schema changes. Not imported by application code.

- **Notes:**  
  One-time setup script. Should be run after database creation and before first application start.

#### File: README.md

- **Responsibility:**  
  Project documentation providing overview, architecture, setup instructions, and usage examples.

- **What it should contain:**  
  High-level description of the application, directory structure overview, setup steps, configuration requirements, usage examples, and design principles.

- **What it should NOT contain:**  
  Code implementation details, API documentation, or troubleshooting guides.

- **Dependencies:**  
  None (standalone documentation).

- **Used by:**  
  Developers, users, and contributors for understanding the project.

- **Notes:**  
  Primary entry point for project documentation. Should be kept up to date with architectural changes.

#### File: requirements.txt

- **Responsibility:**  
  Python dependency specification listing all required packages and their versions.

- **What it should contain:**  
  Package names and version pins for FastAPI, SQLAlchemy, Google APIs, Gemini SDK, and other dependencies.

- **What it should NOT contain:**  
  Development-only dependencies, system packages, or environment-specific configurations.

- **Dependencies:**  
  None (dependency specification file).

- **Used by:**  
  Package managers (pip) during installation. CI/CD systems for dependency resolution.

- **Notes:**  
  Version pins ensure reproducible builds. Should be updated when dependencies change.

#### File: LICENSE

- **Responsibility:**  
  Legal license text defining terms of use and distribution.

- **What it should contain:**  
  License type and full license text.

- **What it should NOT contain:**  
  Code or application logic.

- **Dependencies:**  
  None.

- **Used by:**  
  Legal compliance and distribution purposes.

- **Notes:**  
  Standard legal file.

---

### Directory: app/

**Purpose:**  
Main application package containing all application code organized by functional layer.

#### File: __init__.py

- **Responsibility:**  
  Package marker and documentation string for the app package.

- **What it should contain:**  
  Package-level docstring describing the application purpose.

- **What it should NOT contain:**  
  Imports, initialization logic, or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system to recognize the directory as a package.

- **Notes:**  
  Minimal package marker. No runtime behavior.

#### File: main.py

- **Responsibility:**  
  FastAPI application entry point that creates the application instance and registers routers.

- **What it should contain:**  
  FastAPI app instantiation, router registration (chat, ui), health check endpoint, and optional uvicorn run command for direct execution.

- **What it should NOT contain:**  
  Business logic, orchestration code, database operations, or LLM calls. Should not define routes directly (routes belong in api/ subdirectory).

- **Dependencies:**  
  `fastapi.FastAPI`, `app.api.chat`, `app.api.ui`.

- **Used by:**  
  Uvicorn server as the ASGI application entry point. Also executable directly via `python -m app.main`.

- **Notes:**  
  Configuration / startup layer. Thin entry point that delegates to routers. Health check provides basic liveness probe.

#### File: config.py

- **Responsibility:**  
  Centralized configuration management that loads environment variables and provides application-wide settings.

- **What it should contain:**  
  Config class with static attributes for database URL, LLM provider and API keys, Google OAuth credentials, HubSpot API keys, Zoom OAuth credentials. Backward-compatible fallbacks for legacy environment variable names.

- **What it should NOT contain:**  
  Business logic, API calls, or runtime state. Should not perform validation beyond basic type conversion.

- **Dependencies:**  
  `os`, `dotenv` (for environment variable loading).

- **Used by:**  
  All application modules that need configuration (database, LLM client, integrations).

- **Notes:**  
  Configuration / startup layer. Single source of truth for environment variables. Supports both new explicit naming (LLM_API_KEY, GOOGLE_CLIENT_ID) and legacy names (GEMINI_API_KEY, GOOGLE_CREDENTIALS_PATH) for backward compatibility.

---

### Directory: app/api/

**Purpose:**  
API layer providing HTTP endpoints for chat interface and web UI.

#### File: __init__.py

- **Responsibility:**  
  Package marker for API layer.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: chat.py

- **Responsibility:**  
  REST API endpoint for chat messages. Receives user messages, delegates to orchestrator, returns responses.

- **What it should contain:**  
  FastAPI router definition, POST /api/chat endpoint handler, Pydantic request/response models, database session dependency injection, orchestrator instantiation, and response formatting.

- **What it should NOT contain:**  
  Orchestration logic, intent recognition, workflow execution, or LLM calls. Should not contain business rules or memory operations.

- **Dependencies:**  
  `fastapi.APIRouter`, `fastapi.Depends`, `sqlalchemy.orm.Session`, `app.db.session.SessionLocal`, `app.agent.orchestrator.Orchestrator`, `app.memory.repo.MemoryRepo`.

- **Used by:**  
  FastAPI application (via router registration in main.py). External clients making HTTP requests.

- **Notes:**  
  API layer. Thin HTTP wrapper around orchestrator. Handles HTTP concerns (request validation, response formatting, error handling) but delegates all business logic to orchestrator.

#### File: ui.py

- **Responsibility:**  
  Serves the HTML chat interface as a single-page web application.

- **What it should contain:**  
  FastAPI router definition, GET / endpoint that returns HTMLResponse with embedded HTML, CSS, and JavaScript for the chat UI.

- **What it should NOT contain:**  
  Backend business logic, API endpoint definitions (except the UI route), or external dependencies beyond FastAPI.

- **Dependencies:**  
  `fastapi.APIRouter`, `fastapi.responses.HTMLResponse`.

- **Used by:**  
  Web browsers accessing the root URL. FastAPI application (via router registration).

- **Notes:**  
  API layer. Self-contained single-page application with inline CSS and JavaScript. Implements iOS 26-inspired design with glassmorphism, design tokens, and smooth animations. Communicates with /api/chat endpoint via fetch API.

---

### Directory: app/agent/

**Purpose:**  
Agent core layer responsible for orchestration, intent recognition, workflow coordination, and commitment management.

#### File: __init__.py

- **Responsibility:**  
  Package marker for agent core layer.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: orchestrator.py

- **Responsibility:**  
  Central coordination point that owns control flow. Processes user messages through intent recognition, workflow selection, and execution.

- **What it should contain:**  
  Orchestrator class with process_message method, intent recognition delegation, workflow selection logic, meeting summary workflow execution, calendar integration calls, memory repository operations, tool invocations, and response formatting.

- **What it should NOT contain:**  
  Direct SQL queries, HTTP requests, LLM prompt construction, or integration API calls. Should delegate to specialized modules.

- **Dependencies:**  
  `app.agent.intents.recognize_intent`, `app.agent.workflows.MEETING_SUMMARY_WORKFLOW`, `app.agent.commitments.create_commitments_from_action_items`, `app.memory.repo.MemoryRepo`, `app.integrations.calendar.get_most_recent_meeting_by_client`, `app.integrations.zoom.extract_zoom_meeting_id`, `app.integrations.zoom.fetch_zoom_transcript`, `app.tools.summarize.summarize_meeting`, `app.memory.schemas`.

- **Used by:**  
  API layer (chat.py) as the primary entry point for message processing.

- **Notes:**  
  Agent/orchestration layer. Core of the application. Owns all control flow and coordinates between layers. No direct external dependencies (HTTP, SQL, LLM) - all delegated. Implements the meeting summary workflow end-to-end: resolve meeting, fetch transcript, summarize, create commitments, save memory.

#### File: intents.py

- **Responsibility:**  
  Intent recognition using LLM to classify user messages and extract entities (client names, dates).

- **What it should contain:**  
  recognize_intent function that formats prompts, calls LLM client, parses JSON response, and returns intent classification with confidence and extracted entities.

- **What it should NOT contain:**  
  Workflow execution, database operations, or business logic beyond intent classification.

- **Dependencies:**  
  `app.llm.client.chat`, `app.llm.prompts.INTENT_RECOGNITION_SYSTEM`, `app.llm.prompts.INTENT_RECOGNITION_USER`.

- **Used by:**  
  Orchestrator (orchestrator.py) to determine which workflow to execute.

- **Notes:**  
  Agent/orchestration layer. Stateless function that uses LLM for classification. Returns structured data (intent, confidence, entities) for workflow routing. Includes fallback handling for JSON parsing errors.

#### File: workflows.py

- **Responsibility:**  
  Workflow definitions as data structures. No logic, only configuration.

- **What it should contain:**  
  Dictionary definitions of workflows with name, steps, and produces fields. Currently defines MEETING_SUMMARY_WORKFLOW.

- **What it should NOT contain:**  
  Executable code, function definitions, or business logic. Should be pure data.

- **Dependencies:**  
  None (pure data).

- **Used by:**  
  Orchestrator (orchestrator.py) to look up workflow definitions and metadata.

- **Notes:**  
  Agent/orchestration layer. Data-only file. Workflow execution logic lives in orchestrator, not here. Designed for extension with additional workflow definitions.

#### File: commitments.py

- **Responsibility:**  
  Translates action items from meeting summaries into HubSpot tasks deterministically.

- **What it should contain:**  
  create_commitments_from_action_items function that iterates action items, creates HubSpot tasks, creates commitment records in memory, and handles idempotency checks.

- **What it should NOT contain:**  
  Meeting summarization logic, LLM calls, or workflow orchestration. Should focus only on commitment creation policy.

- **Dependencies:**  
  `app.integrations.hubspot.create_task`, `app.integrations.hubspot.task_exists`, `app.memory.repo.MemoryRepo`, `app.memory.models.Commitment`, `app.memory.schemas.CommitmentCreate`.

- **Used by:**  
  Orchestrator (orchestrator.py) after meeting summarization to create tasks for action items.

- **Notes:**  
  Agent/orchestration layer. Implements deterministic policy: each action item becomes a HubSpot task with default due date (+3 business days). Handles idempotency to prevent duplicate tasks. Separates policy (this file) from integration (hubspot.py).

---

### Directory: app/llm/

**Purpose:**  
LLM layer providing abstraction over Gemini API with client wrapper and prompt management.

#### File: __init__.py

- **Responsibility:**  
  Package marker for LLM layer.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: client.py

- **Responsibility:**  
  Wraps Google Gemini API with safe, validated client. Handles model selection, API key configuration, and provides chat interface.

- **What it should contain:**  
  GeminiClient class with initialization, model selection logic, chat method. Global singleton pattern with lazy initialization. Model selection uses Config.GEMINI_MODEL with smoke test validation.

- **What it should NOT contain:**  
  Prompt construction, business logic, or workflow-specific code. Should be a generic LLM interface.

- **Dependencies:**  
  `google.generativeai`, `app.config.Config`.

- **Used by:**  
  Intent recognition (intents.py), tools (summarize.py, followup.py), and any module needing LLM capabilities.

- **Notes:**  
  LLM layer. Single point of Gemini API interaction. Implements deterministic model selection from Config.GEMINI_MODEL (formats as models/{model_name}). Includes smoke test to validate model is callable before use. Singleton pattern ensures single client instance.

#### File: prompts.py

- **Responsibility:**  
  Centralized storage of all LLM prompts as string templates.

- **What it should contain:**  
  String constants for system prompts and user prompt templates. Prompts for intent recognition, meeting summarization, and follow-up email generation.

- **What it should NOT contain:**  
  Executable code, prompt construction logic, or dynamic prompt generation. Should be pure string templates.

- **Dependencies:**  
  None (pure strings).

- **Used by:**  
  Intent recognition (intents.py), tools (summarize.py, followup.py) to format prompts before LLM calls.

- **Notes:**  
  LLM layer. Data-only file. All prompts centralized here for maintainability. Templates use .format() for variable substitution. No logic, only prompt text.

---

### Directory: app/tools/

**Purpose:**  
Tool layer providing LLM-powered stateless functions for specific tasks.

#### File: __init__.py

- **Responsibility:**  
  Package marker for tools layer.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: summarize.py

- **Responsibility:**  
  LLM-powered meeting summarization tool. Extracts summary, decisions, and action items from meeting transcripts and metadata.

- **What it should contain:**  
  summarize_meeting function that formats meeting data, calls LLM with meeting summary prompts, parses JSON response, and returns structured summary data.

- **What it should NOT contain:**  
  Database operations, workflow orchestration, or commitment creation. Should be a pure stateless function.

- **Dependencies:**  
  `app.llm.client.chat`, `app.llm.prompts.MEETING_SUMMARY_SYSTEM`, `app.llm.prompts.MEETING_SUMMARY_USER`.

- **Used by:**  
  Orchestrator (orchestrator.py) during meeting summary workflow execution.

- **Notes:**  
  Tool layer. Stateless function that takes transcript and metadata, returns structured data. Handles missing transcripts gracefully. JSON parsing includes fallback for malformed responses.

#### File: followup.py

- **Responsibility:**  
  LLM-powered follow-up email generation tool. Creates professional email text from meeting summaries.

- **What it should contain:**  
  generate_followup_email function that formats meeting data, calls LLM with follow-up email prompts, and returns email body text.

- **What it should NOT contain:**  
  Email sending logic, database operations, or workflow orchestration. Should only generate text, not send emails.

- **Dependencies:**  
  `app.llm.client.chat`, `app.llm.prompts.FOLLOWUP_EMAIL_SYSTEM`, `app.llm.prompts.FOLLOWUP_EMAIL_USER`.

- **Used by:**  
  Not currently used by orchestrator. Available for future workflow extensions.

- **Notes:**  
  Tool layer. Stateless function. Currently not wired into any workflow but available for use. Would be called by orchestrator or email-sending workflow if implemented.

#### File: meeting_brief.py

- **Responsibility:**  
  Stub for meeting brief generation tool. Not yet implemented.

- **What it should contain:**  
  generate_meeting_brief function stub that returns empty string. Placeholder for future implementation.

- **What it should NOT contain:**  
  Implementation logic (currently stubbed).

- **Dependencies:**  
  None (stub only).

- **Used by:**  
  Not currently used. Placeholder for future functionality.

- **Notes:**  
  Tool layer. Stub implementation. Not wired into any workflow. Reserved for future meeting brief generation feature.

---

### Directory: app/memory/

**Purpose:**  
Memory/database layer providing persistent storage for meetings, memory entries, commitments, and interactions.

#### File: __init__.py

- **Responsibility:**  
  Package marker for memory system.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: models.py

- **Responsibility:**  
  SQLAlchemy ORM models defining database schema for persistent memory.

- **What it should contain:**  
  SQLAlchemy model classes: Meeting, MemoryEntry, Commitment, Interaction. Column definitions, relationships, and table metadata.

- **What it should NOT contain:**  
  Business logic, query methods, or data manipulation code. Should be pure model definitions.

- **Dependencies:**  
  `sqlalchemy`, `app.db.session.Base`.

- **Used by:**  
  Memory repository (repo.py) for database operations. Database initialization (init_db.py) for table creation.

- **Notes:**  
  Memory/database layer. Defines four main tables: meetings (stores meeting records), memory_entries (contextual memory for personalization), commitments (tracked HubSpot tasks), interactions (user interaction history). Uses meta_data column name to avoid SQLAlchemy reserved name conflict.

#### File: schemas.py

- **Responsibility:**  
  Pydantic schemas for data validation and serialization in memory operations.

- **What it should contain:**  
  Pydantic BaseModel classes: MeetingCreate, MeetingUpdate, MemoryEntryCreate, CommitmentCreate. Field definitions with types and optional defaults.

- **What it should NOT contain:**  
  Database operations, business logic, or SQLAlchemy models.

- **Dependencies:**  
  `pydantic.BaseModel`.

- **Used by:**  
  Memory repository (repo.py) for type-safe data operations. Orchestrator (orchestrator.py) for creating and updating records.

- **Notes:**  
  Memory/database layer. Provides type safety and validation for memory operations. Separates API contracts (schemas) from database models (models.py). Uses metadata field name (not meta_data) in schemas, mapped to meta_data in models.

#### File: repo.py

- **Responsibility:**  
  Memory repository providing read/write operations for persistent memory. Abstraction over SQLAlchemy operations.

- **What it should contain:**  
  MemoryRepo class with methods for meeting operations (create, get, update), memory entry operations (create, get by key, get for client), commitment operations (create, get, update status), and interaction operations (create).

- **What it should NOT contain:**  
  Business logic, workflow orchestration, or LLM calls. Should be pure data access layer.

- **Dependencies:**  
  `sqlalchemy.orm.Session`, `app.memory.models`, `app.memory.schemas`.

- **Used by:**  
  Orchestrator (orchestrator.py) for all memory operations. API layer (chat.py) for creating repository instances.

- **Notes:**  
  Memory/database layer. Repository pattern providing clean interface to database. Handles mapping between schemas (metadata) and models (meta_data). All database operations go through this repository.

---

### Directory: app/integrations/

**Purpose:**  
Integration layer providing interfaces to external services (Google Calendar, Zoom, HubSpot, Gmail).

#### File: __init__.py

- **Responsibility:**  
  Package marker for integrations layer.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: calendar.py

- **Responsibility:**  
  Google Calendar integration for fetching meeting information from calendar events.

- **What it should contain:**  
  get_calendar_service function for OAuth authentication, get_recent_meetings function, search_meetings_by_client function, get_most_recent_meeting_by_client function. OAuth flow handling with token management.

- **What it should NOT contain:**  
  Meeting summarization logic, workflow orchestration, or database operations. Should only interact with Google Calendar API.

- **Dependencies:**  
  `google.oauth2.credentials`, `google.auth.transport.requests`, `google_auth_oauthlib.flow`, `googleapiclient.discovery`, `app.config.Config`.

- **Used by:**  
  Orchestrator (orchestrator.py) to find meetings for clients. Zoom integration (zoom.py) may use calendar service.

- **Notes:**  
  Integration layer. Handles Google OAuth Desktop App Flow. Uses new environment variables (GOOGLE_CLIENT_SECRET_FILE, GOOGLE_TOKEN_FILE) with fallback to legacy (GOOGLE_CREDENTIALS_PATH). Returns calendar events as dictionaries with id, summary, start, end, attendees, etc.

#### File: zoom.py

- **Responsibility:**  
  Zoom integration for extracting meeting IDs from calendar events and fetching transcripts.

- **What it should contain:**  
  extract_zoom_meeting_id function that parses Zoom URLs from calendar events, fetch_zoom_transcript function (currently stubbed) for transcript retrieval.

- **What it should NOT contain:**  
  Meeting summarization logic or workflow orchestration. Should only handle Zoom-specific operations.

- **Dependencies:**  
  `app.integrations.calendar.get_calendar_service`, `app.config.Config`.

- **Used by:**  
  Orchestrator (orchestrator.py) to extract Zoom meeting IDs and fetch transcripts.

- **Notes:**  
  Integration layer. extract_zoom_meeting_id is implemented (parses 11-digit IDs from URLs). fetch_zoom_transcript is stubbed (returns None). Zoom OAuth configuration available via Config but not yet implemented. Comments document new OAuth variable names (ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET).

#### File: hubspot.py

- **Responsibility:**  
  HubSpot integration for creating and checking tasks (action items).

- **What it should contain:**  
  create_task function that creates HubSpot tasks via API, task_exists function for idempotency checks. Default due date calculation (+3 business days).

- **What it should NOT contain:**  
  Meeting summarization logic, workflow orchestration, or database operations. Should only interact with HubSpot API.

- **Dependencies:**  
  `requests`, `app.config.Config`.

- **Used by:**  
  Commitments module (commitments.py) to create tasks from action items.

- **Notes:**  
  Integration layer. Implements HubSpot CRM API v3 for task creation. Handles authentication via HUBSPOT_API_KEY. Returns task IDs or None on failure. Includes idempotency check function.

#### File: gmail.py

- **Responsibility:**  
  Gmail integration stub for sending emails. Not yet implemented.

- **What it should contain:**  
  send_email function stub that returns False. Placeholder for future Gmail API integration.

- **What it should NOT contain:**  
  Implementation logic (currently stubbed).

- **Dependencies:**  
  None (stub only).

- **Used by:**  
  Not currently used. Placeholder for future email-sending functionality.

- **Notes:**  
  Integration layer. Stub implementation. Not wired into any workflow. Reserved for future email sending feature (would work with followup.py tool).

---

### Directory: app/db/

**Purpose:**  
Database configuration layer providing SQLAlchemy engine and session management.

#### File: __init__.py

- **Responsibility:**  
  Package marker for database layer.

- **What it should contain:**  
  Package-level docstring.

- **What it should NOT contain:**  
  Imports or executable code.

- **Dependencies:**  
  None.

- **Used by:**  
  Python import system.

- **Notes:**  
  Minimal package marker.

#### File: session.py

- **Responsibility:**  
  SQLAlchemy database session configuration. Creates engine, session factory, and declarative base.

- **What it should contain:**  
  SQLAlchemy engine creation from DATABASE_URL, SessionLocal sessionmaker, and Base declarative_base for model inheritance.

- **What it should NOT contain:**  
  Model definitions, business logic, or query operations. Should only configure database connection.

- **Dependencies:**  
  `sqlalchemy`, `app.config.Config`.

- **Used by:**  
  Memory models (models.py) for Base inheritance. Memory repository (repo.py) for session creation. API layer (chat.py) for database dependency injection. Database initialization (init_db.py) for engine access.

- **Notes:**  
  Configuration / startup layer. Single point of database configuration. Engine uses Config.DATABASE_URL (PostgreSQL connection string). SessionLocal used for dependency injection in FastAPI endpoints.

---

## Summary

This application follows a layered architecture:

- **API Layer** (app/api/): HTTP endpoints and web UI
- **Agent/Orchestration Layer** (app/agent/): Control flow and coordination
- **LLM Layer** (app/llm/): Gemini API abstraction and prompts
- **Tool Layer** (app/tools/): LLM-powered stateless functions
- **Memory/Database Layer** (app/memory/, app/db/): Persistent storage
- **Integration Layer** (app/integrations/): External service interfaces
- **Configuration/Startup Layer** (app/config.py, app/main.py, app/db/session.py): Application setup

Each layer has clear responsibilities and dependencies flow downward (API → Agent → Tools/Integrations → Memory). The orchestrator owns all control flow, ensuring deterministic behavior and clear separation of concerns.

