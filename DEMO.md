# Demo Mode Documentation

## Overview

Demo Mode is a special operating mode that allows the Meeting Intelligence Agent to run without requiring external API credentials. It uses fixture data for calendar events, transcripts, and memory, while still making real LLM calls for summarization and other AI-powered features.

Demo Mode is designed for reviewers, testers, and developers who want to evaluate the application's functionality without setting up Google Calendar, Zoom, or HubSpot integrations.

## Activating Demo Mode

### Method 1: Environment Variable

Set the `APP_MODE` environment variable to `demo`:

```bash
export APP_MODE=demo
```

### Method 2: .env Configuration

Add the following line to your `.env` file:

```
APP_MODE=demo
```

If `APP_MODE` is not set, the application defaults to demo mode automatically.

## Confirming Demo Mode is Active

When the application starts, you will see a startup message in the console:

```
⚠️⚠️⚠️ Application starting in APP_MODE=DEMO⚠️⚠️⚠️
```

You can also verify the mode by calling the health endpoint:

```bash
curl http://localhost:8000/health
```

The response will include the current mode:

```json
{
  "status": "ok",
  "mode": "demo"
}
```

## Switching to Production Mode

To run the application in production mode with full external API integrations:

1. Set `APP_MODE` to `production` in your `.env` file:
   ```
   APP_MODE=production
   ```

2. Ensure all required credentials are configured:
   - `GEMINI_API_KEY` or `LLM_API_KEY` (required for LLM calls)
   - `GOOGLE_CLIENT_SECRET_FILE` (for Google Calendar)
   - `ZOOM_CLIENT_ID` and `ZOOM_CLIENT_SECRET` (for Zoom transcripts)
   - `HUBSPOT_API_KEY` (for HubSpot integration)

3. Restart the application

## Demo Mode Guarantees

When running in Demo Mode, the application provides:

- **Fixture-based calendar events**: Pre-configured meeting data is used instead of querying Google Calendar
- **Fixture-based transcripts**: Sample Zoom meeting transcripts are provided without requiring Zoom API access
- **Fixture-based memory**: Pre-seeded memory entries are available for context
- **Real LLM calls**: The application still makes actual API calls to the Gemini LLM for summarization, intent recognition, and other AI features

**Important**: Demo Mode requires a valid `GEMINI_API_KEY` or `LLM_API_KEY` to function, as it still performs real LLM operations.

## Demo Commands

The following commands demonstrate core functionality and can be run immediately in Demo Mode:

### 1. Summarize Last Meeting

**Command:**
```
Summarize my last meeting
```

**What it demonstrates:**
- Intent recognition (classifying user intent)
- Meeting retrieval (finding the most recent meeting)
- Client name resolution
- Meeting summarization using LLM
- Extraction of decisions and action items

**Expected behavior:**
Returns a structured summary with meeting details, decisions made, and action items identified.

### 2. Generate Follow-up Email

**Command:**
```
Generate a follow-up email
```

**What it demonstrates:**
- Active meeting context (uses the most recently summarized meeting)
- Email generation based on meeting summary
- Professional email formatting
- Integration of decisions and action items into email content

**Expected behavior:**
Generates a professional follow-up email that can be sent to meeting attendees, including key discussion points and next steps.

### 3. Brief on Next Meeting

**Command:**
```
Brief me on my next meeting
```

**What it demonstrates:**
- Upcoming meeting retrieval
- Meeting preparation context
- Memory integration (uses past meeting context)
- Brief generation for meeting preparation

**Expected behavior:**
Provides a concise briefing with meeting purpose, relevant background from past meetings, likely discussion points, and suggested preparation notes.

## Recommended Evaluation Flow

For reviewers evaluating the application, follow this sequence:

1. **Start the application** in Demo Mode and verify the startup message confirms demo mode

2. **Test intent recognition** by running:
   ```
   Summarize my last meeting
   ```
   Observe the structured summary output and verify decisions and action items are extracted.

3. **Test follow-up generation** by running:
   ```
   Generate a follow-up email
   ```
   Verify the email is well-formatted and includes relevant meeting details.

4. **Test meeting briefing** by running:
   ```
   Brief me on my next meeting
   ```
   Confirm the briefing includes context from previous meetings and actionable preparation notes.

5. **Test date-specific queries** (if supported in demo fixtures):
   ```
   Summarize my meeting with MTCA on 12/12
   ```
   Verify date parsing and meeting retrieval work correctly.

6. **Verify error handling** by testing invalid queries:
   ```
   Summarize my meeting with NonexistentClient
   ```
   Confirm appropriate error messages are returned.

## No External Credentials Required

Demo Mode operates entirely without external service credentials except for the LLM API key. You do not need:

- Google Calendar OAuth credentials
- Zoom API credentials
- HubSpot API credentials
- Database setup (uses in-memory or configured database)

This makes Demo Mode ideal for quick evaluation, code reviews, and testing without complex setup procedures.

