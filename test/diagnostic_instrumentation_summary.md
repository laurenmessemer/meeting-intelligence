# Diagnostic Instrumentation Summary

**Purpose:** READ-ONLY diagnostic logging to identify why December 12, 2025 events are not resolved while October 17, 2025 is returned.

**Status:** Instrumentation complete. Ready for runtime observation.

---

## Instrumented Files

### 1. app/integrations/calendar.py

**Functions instrumented:**

#### get_recent_meetings()
- **Pagination logging:** Logs pageToken before/after, events per page, total events across all pages
- **Query parameters:** Logs timeMin, timeMax, maxResults, days_back, calendarId
- **Raw event dump:** Logs ALL events before filtering (id, summary, start, organizer, creator, attendees, location)

#### get_meeting_by_client_and_date()
- **Date window logging:** Logs start_dt, end_dt, timeMin, timeMax with timezone info
- **Pagination logging:** Logs pageToken before/after, events per page, total events
- **Raw event dump:** Logs ALL events in query window before client filtering
- **Client matching trace:** For each event, logs which fields match (summary, description, location, organizer, creator, attendees)

#### get_most_recent_meeting_by_client()
- **Candidate logging:** Logs all candidate meetings BEFORE sorting
- **Sorting trace:** Logs meetings AFTER sorting with parsed datetimes
- **Selection logging:** Logs which meeting was selected and why

### 2. app/agent/orchestrator.py

**Functions instrumented:**

#### _parse_target_date()
- **Input logging:** Logs raw date_str input
- **Parsing steps:** Logs dateutil.parser result, extracted date, year detection, year adjustment
- **Output logging:** Logs final parsed date

#### _execute_meeting_summary_workflow()
- **Entity logging:** Logs raw entities dict from intent recognition
- **Date string logging:** Logs date_str value and whether it's truthy
- **Branch execution:** Logs whether date-aware branch is entered
- **Date lookup:** Logs target_date, whether get_meeting_by_client_and_date() is called, and its return value
- **Fallback trace:** Logs when and why fallback to get_most_recent_meeting_by_client() occurs

### 3. app/agent/intents.py

**Functions instrumented:**

#### recognize_intent()
- **LLM response logging:** Logs raw JSON response from LLM
- **Parsed result:** Logs parsed result dict
- **Entity extraction:** Logs entities dict and specifically entities['date']
- **Error logging:** Logs JSON parsing failures

---

## How to Use

### Step 1: Run the Application

The application is already running with diagnostic logging enabled. All diagnostic output will appear in the console/terminal where uvicorn is running.

### Step 2: Make a Test Request

Send a request to the API with:
```
"Summarize my meeting with MTCA on December 12th, 2025"
```

### Step 3: Observe Console Output

The console will show:
1. Intent recognition results (what date was extracted)
2. Date parsing steps (how the date was parsed)
3. Calendar query parameters (timeMin, timeMax)
4. Pagination details (pages retrieved)
5. Raw events (all events before filtering)
6. Client matching (which events match MTCA)
7. Sorting results (order of meetings)
8. Control flow (which branch executed, why fallback occurred)

### Step 4: Run Diagnostic Test Script (Optional)

```bash
python3 test/diagnostic_test_script.py
```

This will test multiple date input formats and show parsing behavior for each.

### Step 5: Fill Diagnostic Report

Use the output from the console to fill in `test/diagnostic_report_template.md` with:
- Exact values from logs
- Yes/No answers based on evidence
- Root cause identification

---

## Diagnostic Output Format

All diagnostic logs are prefixed with `DIAGNOSTIC:` and use clear section separators (`===` and `---`).

**Example output structure:**
```
================================================================================
DIAGNOSTIC: get_meeting_by_client_and_date()
================================================================================
DIAGNOSTIC: Input parameters:
  client_name: MTCA
  target_date: 2025-12-12 (type: <class 'datetime.date'>)

DIAGNOSTIC: Date window computation:
  start_dt: 2025-12-12 00:00:00+00:00 (timezone: UTC)
  end_dt: 2025-12-12 23:59:59.999999+00:00 (timezone: UTC)
  timeMin: 2025-12-12T00:00:00+00:00
  timeMax: 2025-12-12T23:59:59.999999+00:00
  ...
```

---

## What to Look For

### Critical Observations

1. **Pagination:** Are all pages being retrieved, or only the first page?
2. **Raw Events:** Is December 12, 2025 event present in the raw API response?
3. **Date Window:** Does the query window include December 12, 2025?
4. **Date Parsing:** Is "December 12th, 2025" correctly parsed to 2025-12-12?
5. **Client Matching:** Does the December 12 event match "MTCA"?
6. **Sorting:** If both October and December events exist, which is selected?
7. **Fallback:** Why does the fallback execute? Is date_str missing or is lookup failing?

---

## Notes

- All diagnostic logging is TEMPORARY and should be removed after diagnosis
- Logging does NOT modify business logic, only observes behavior
- No code fixes or optimizations have been applied
- This is purely observability instrumentation

---

**Next Steps:** Make a test request and observe the console output, then fill in the diagnostic report template with findings.


