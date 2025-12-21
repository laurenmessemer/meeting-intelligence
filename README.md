# Meeting Intelligence Agent

## Overview
The Meeting Intelligence Agent is a Python-based, multi-workflow chat agent designed to extract structured intelligence from meetings. It enables users to summarize past meetings, generate professional follow-up emails, and prepare briefings for upcoming meetings by coordinating calendar data, transcripts, persistent memory, and LLM-powered tools.

This system is intentionally designed as a coordination-first agent, not a thin wrapper around an LLM. It applies deterministic policies, multi-step orchestration, and persistent memory to steer LLM outputs toward reliable, context-aware results.

The application supports two environments—a fully self-contained demo mode and a production mode with live integrations—while preserving identical orchestration logic across both.

## Quick Start — Interactive Demo

This project includes a fully self-contained **demo mode** designed for fast evaluation.

You can clone the repo and run the agent locally in minutes — no production services required.

### Requirements

* Python 3.11+
* macOS or Linux
* Gemini LLM API key (free tier is sufficient)

### Setup

From the project root:

make setup-demo

This creates a local virtual environment and installs all dependencies.No production services or credentials are required.

### Run the Demo

Set your LLM API key:

export LLM\_API\_KEY=your\_gemini\_api\_key\_here

Then start the app:

make run-demo

The agent will be available at:

[http://localhost:8000](http://localhost:8000)

### What You Can Do in Demo Mode

* Chat with the agent via the web UI
* Summarize past meetings• Generate follow-up emails
* Prepare upcoming meeting briefs
* Observe full orchestration, memory usage, and workflow behavior

Demo mode mirrors **production orchestration exactly**, using fixture-based data instead of live integrations.

## What Problem This Solves
Meetings generate large volumes of unstructured information across calendars, transcripts, and follow-ups. This application transforms that raw data into:

* Concise summaries
* Explicit decisions
* Actionable next steps
* Context-aware follow-up communications
* Personalized briefings grounded in prior history

Rather than relying on a single LLM call, the system coordinates multiple data sources and tools to produce structured, auditable outputs.

## Agent Definition & Classification
Under the provided criteria, this system qualifies as an agent because it:

* Wraps multiple LLM-powered tools
* Applies explicit coordination logic beyond model inference
* Maintains persistent memory across sessions
* Executes specialized, stateful workflows
* Uses deterministic guardrails for critical decisions

It is not a “thinking model with a large context window.” Intelligence emerges from orchestration.

## High-Level Architecture
At a system level, the application is composed of seven distinct layers:

UI / API
   ↓
Intent Recognition
   ↓
Orchestrator (Control Flow)
   ↓
Workflow Execution
   ↓
LLM-Powered Tools
   ↓
Memory & Persistence
   ↓
External Integrations

Each layer has a single responsibility and does not leak concerns into adjacent layers.

## Layer-by-Layer Architecture

### 1. UI & Interaction Layer
**Purpose:** Accept user input and render structured responses.

**Responsibilities**
* Accept natural language input via web UI or REST API
* Instantiate orchestration dependencies
* Display responses, agent notes, memory provenance, and suggested actions

**Key Characteristics**
* Stateless with respect to business logic
* Does not perform orchestration, memory access, or LLM calls
* Acts as a thin presentation layer

### 2. Intent Recognition Layer
**Purpose:** Classify user intent and extract entities.

**Responsibilities**
* Determine user intent (e.g. summarize, brief, follow-up)
* Extract raw entities (client name, date text)
* Return structured intent metadata

**Design Notes**
* Powered by an LLM with temperature = 0.0 for determinism
* Performs classification only—no execution
* Avoids date parsing or client resolution (handled later)

### 3. Orchestration Layer (Core Intelligence)
**Purpose:** Coordinate all system behavior.
This is the heart of the agent.

**Responsibilities**
* Route requests to specialized workflows
* Enforce deterministic policies for:
    * Client resolution
    * Date parsing
    * Meeting selection
* Assemble memory context prior to LLM invocation
* Manage workflow state (active meetings, interaction history)
* Generate agent notes and suggested next actions

**Explicit Non-Responsibilities**
* No SQL
* No HTTP
* No LLM prompt construction

This separation ensures orchestration logic remains auditable and testable.

### 4. Workflow Execution Layer
**Purpose:** Implement specialized, multi-step workflows.

The system supports multiple workflows, including:
* Meeting summarization
* Follow-up email generation
* Upcoming meeting briefings
* CRM task approval

**Each workflow:**
* Has dedicated control flow
* Handles its own validation and fallbacks
* Coordinates calendar data, transcripts, memory, and tools
* Workflows are stateful, but tools remain stateless.

### 5. LLM-Powered Tool Layer
**Purpose:** Perform content generation.

**Characteristics**
* Each tool is a stateless function
* Accepts fully prepared context
* Returns structured output (JSON or text)
* Performs no data access or orchestration

**Examples**
* Meeting summarization
* Follow-up email drafting
* Meeting brief generation
* Intent classification

This design makes tools reusable, testable, and swappable.

### 6. Memory & Persistence Layer
**Purpose:** Provide persistent, cross-session intelligence.
The agent stores and retrieves structured memory using a relational database.

**Memory Types**
* **Meetings:** Canonical records of processed meetings
* **Memory Entries:** Extracted intelligence (summaries, decisions, actions)
* **Interactions:** Full audit trail of user requests and agent responses
* **Commitments:** CRM-linked action items (extensible)

**Memory Behavior**
* Retrieved by client scope
* Prioritized deterministically:
    1. Decisions
    2. Action items
    3. Summaries
    4. Notes
* Limited to prevent context overload
* Passed explicitly into tools as context
* Memory directly influences future responses, enabling personalization.

### 7. External Integrations Layer
**Purpose:** Interface with third-party systems.

**Current integrations include:**
* Calendar provider (event metadata)
* Video conferencing provider (transcripts)
* CRM system (company resolution, task creation)

**Design Principles**
* Loose coupling
* Standardized return shapes
* No business logic
* Graceful failure handling

## Demo Mode vs Production Mode
The application supports two parallel environments:

**Demo Mode (default):**
* Uses file-based fixtures
* Requires no external credentials
* Mirrors production APIs exactly

**Production Mode:**
* Uses live APIs
* Shares identical orchestration logic

Mode selection is centralized and explicit. Demo mode is not a collection of conditional hacks—it is a parallel data source implementation designed for evaluation, development, and testing.

## End-to-End Orchestration Flow (Summary)
For a request like “Summarize my last meeting”:

1. User submits message
2. Intent is classified
3. Orchestrator selects workflow
4. Meeting is deterministically resolved
5. Transcript is retrieved
6. Relevant memory is selected and prioritized
7. LLM tool is invoked with structured context
8. Results are persisted
9. Suggested next actions are generated
10. Response is returned with transparency metadata

Every step is explicit, logged, and traceable.

## Mapping to Agent Requirements
* **Written in Python**
    * ✔ Entire system implemented in Python with modern frameworks and typing.
* **Interactive**
    * ✔ Web UI and REST API enable smooth, conversational interaction.
* **LLM-Powered Tools**
    * ✔ Multiple tools are directly powered by an LLM, each with a focused responsibility.
* **Coordination Beyond Raw LLM Calls**
    * ✔ Deterministic orchestration governs data selection, memory, and control flow.
* **Persistent Memory**
    * ✔ Structured memory is stored in a database and influences future behavior.
* **Specialized Workflows**
    * ✔ Multiple personalized workflows exist beyond generic chat.

## Alignment with Guidelines
* **Use Free / Low-Cost Tools**
    * Supports free-tier LLM usage
* **Make It Easy**
    * Demo mode runs without setup complexity
    * Clear separation between demo and production environments
* **Use AI as an Aid, Not a Crutch**
    * Deterministic logic precedes LLM usage
    * LLMs generate content, not decisions
    * Critical paths are governed by code, not inference

## Memory Model & Evolution
Memory is designed as a first-class system primitive, not conversation history.
It enables:
* Contextual personalization
* Cross-session continuity
* Transparent provenance

The model is intentionally extensible, allowing future evolution into:
* Semantic memory relationships
* Conflict resolution
* Temporal reasoning
* User- or team-scoped memory

## Extensibility & Future Integrations
The architecture supports straightforward expansion into:
* Additional CRMs
* Task management systems
* Knowledge bases
* Communication platforms
* Analytics workflows
* Document storage
* Direct email sending

New integrations follow established patterns without altering orchestration logic.

## Observations & Improvement Areas (Analytical)
This codebase is functional and well-structured. Areas identified for future improvement include:
* Memory query optimization
* Caching of repeated LLM outputs
* Async I/O for scalability
* Authentication and rate limiting
* Structured logging and observability
* Cleanup of legacy diagnostic code

These are evolutionary improvements, not blockers.

## Conclusion
This Meeting Intelligence Agent demonstrates a clear understanding of applied agent design:
* Intelligence emerges from coordination, not prompt size
* LLMs are used strategically, not indiscriminately
* Memory is structured, persistent, and influential
* Workflows are explicit, specialized, and extensible

The system is intentionally designed to be understandable, auditable, and evolvable.

[![Meeting Intelligence Agent Demo](https://img.youtube.com/vi/3rSsK8P8mQ8/0.jpg)](https://youtu.be/3rSsK8P8mQ8)
*Click the image above to watch the production environment demonstration.*

## Interactive Demo

A live, interactive demo of the Meeting Intelligence Agent is available here:

**👉 https://meeting-intelligence-demo-d78c338946a3.herokuapp.com/**

This demo runs in **Demo Mode** and requires no external credentials.  
It mirrors the full production orchestration flow using fixture-based data, allowing you to interact with the agent exactly as a reviewer or evaluator would.
