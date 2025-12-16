# Date Resolution Root Cause Diagnostic

**Issue:** "Summarize my meeting with MTCA on December 12th, 2025" returns October 17, 2025 meeting.

**Mode:** READ-ONLY (no code changes, no fixes)

---

## STEP 1 — INTENT OUTPUT (GROUND TRUTH)

### Prompt Definition

**File:** `app/llm/prompts.py` (lines 3-18)

```
INTENT_RECOGNITION_SYSTEM = """You are an intent classifier for a meeting intelligence agent.
Analyze the user's message and determine their intent. Extract relevant entities.

Respond in JSON format:
{
  "intent": "summarize_meeting" | "other",
  "confidence": 0.0-1.0,
  "entities": {
    "client_name": "string or null",
    "date": "YYYY-MM-DD or null"
  }
}
```

**Key Instruction:** `"date": "YYYY-MM-DD or null"`

### User Input

**Input:** "Summarize my meeting with MTCA on December 12th, 2025"

### Expected Entity Value

**Question:** What EXACT value does `entities["date"]` contain?

**Answer:** The LLM is instructed to return `"YYYY-MM-DD or null"`. For "December 12th, 2025", the LLM should ideally return `"2025-12-12"`.

**However:** The prompt does NOT explicitly instruct the LLM to convert natural language dates. The LLM may:
- Return `"2025-12-12"` (correct ISO format)
- Return `"December 12, 2025"` (natural language, not ISO)
- Return `null` (if it doesn't recognize the date)
- Return `"12/12/2025"` (other format)

**Cannot determine exact value without runtime inspection.** However, if the orchestrator receives a date string, it will attempt to parse it.

### Orchestrator Receipt

**File:** `app/agent/orchestrator.py` (line 44)

```python
entities = intent_result.get("entities", {})
```

**File:** `app/agent/orchestrator.py` (line 92)

```python
date_str = entities.get("date")
```

**Finding:** The orchestrator receives `entities["date"]` unchanged from intent recognition. If the LLM returns a non-ISO format or null, the orchestrator will receive that exact value.

---

## STEP 2 — ORCHESTRATOR CONTROL FLOW

### Execution Path Analysis

**File:** `app/agent/orchestrator.py` (lines 92-121)

```python
date_str = entities.get("date")
calendar_event = None

# --- DATE-AWARE RESOLUTION ---
if date_str:
    try:
        target_date = self._parse_target_date(date_str)
        calendar_event = get_meeting_by_client_and_date(
            client_name=client_name,
            target_date=target_date,
        )
    except Exception:
        calendar_event = None

    # If user explicitly asked for a date, do NOT silently fall back
    if not calendar_event:
        return {
            "message": (
                f"I couldn't find a meeting with {client_name} on {date_str}."
            ),
            "metadata": {
                "error": "meeting_not_found_for_date",
                "client_name": client_name,
                "date": date_str,
            },
        }

# --- MOST RECENT FALLBACK ---
if not calendar_event:
    calendar_event = get_most_recent_meeting_by_client(client_name)
```

### Answers

**Question 1:** Does `_execute_meeting_summary_workflow()` enter the `if date_str:` branch?

**Answer:** YES, if `entities.get("date")` is truthy (not None, not empty string). The branch is entered at line 96.

**Question 2:** Does it call `get_meeting_by_client_and_date()`?

**Answer:** YES, at line 99-102, if `date_str` is truthy and `_parse_target_date()` succeeds.

**Question 3:** Under what condition does execution proceed to `get_most_recent_meeting_by_client()`?

**Answer:** Execution proceeds to `get_most_recent_meeting_by_client()` at line 121 ONLY if:
- `date_str` is falsy (None or empty), OR
- `date_str` is truthy BUT `get_meeting_by_client_and_date()` returns None AND an exception occurred during parsing (line 103-104), causing `calendar_event` to remain None

**However, there is a CRITICAL ISSUE:**

Lines 107-117 show that if `date_str` is truthy and `calendar_event` is None, the function should RETURN an error message, NOT fall back. This means the fallback at line 121 should ONLY execute if `date_str` was falsy to begin with.

**But wait:** If an exception occurs at line 98 (`_parse_target_date()`), `calendar_event` is set to None (line 104), and then lines 107-117 check `if not calendar_event:` and return an error. So the fallback should NOT execute if a date was provided.

**Conclusion:** If October 17 is being returned, it means either:
1. `date_str` was None/empty (date not extracted), OR
2. An exception occurred that bypassed the error return, OR
3. The code path is different than shown

---

## STEP 3 — DATE PARSING ACCURACY

### Parse Function

**File:** `app/agent/orchestrator.py` (lines 28-32)

```python
def _parse_target_date(self, date_str: str) -> date:
    """
    Parse YYYY-MM-DD into a date object.
    """
    return datetime.fromisoformat(date_str).date()
```

### Type Analysis

**Question 1:** What type is passed into `get_meeting_by_client_and_date()`?

**Answer:** `datetime.date` object (not `datetime.datetime`).

**Evidence:**
- `_parse_target_date()` returns `datetime.fromisoformat(date_str).date()` which returns a `date` object
- This `date` object is assigned to `target_date` at line 98
- `target_date` is passed to `get_meeting_by_client_and_date()` at line 101

**Question 2:** Confirm whether timezone conversion occurs.

**Answer:** NO timezone conversion occurs. `datetime.fromisoformat(date_str).date()` extracts only the date portion, losing all time and timezone information.

**Question 3:** Confirm whether December 12, 2025 could be shifted by parsing logic.

**Answer:** NO, the date itself is not shifted. However, there is a **TYPE MISMATCH**:

**File:** `app/integrations/calendar.py` (line 108)

```python
def get_meeting_by_client_and_date(
    client_name: str,
    target_date: datetime,  # <-- EXPECTS datetime, but receives date!
    days_buffer: int = 7
) -> Optional[Dict[str, Any]]:
```

**File:** `app/integrations/calendar.py` (lines 115-116)

```python
start_range = (target_date - timedelta(days=days_buffer)).isoformat() + "Z"
end_range = (target_date + timedelta(days=days_buffer)).isoformat() + "Z"
```

**CRITICAL ISSUE:** The function signature expects `datetime`, but the orchestrator passes a `date` object. When Python tries to execute `target_date - timedelta(days=days_buffer)`, it will work (date objects support timedelta arithmetic), but when it calls `.isoformat()` on the result, it will return a date-only string like `"2025-12-05"`, not a datetime string like `"2025-12-05T00:00:00Z"`.

**However, this may still work** because Google Calendar API may accept date-only strings in ISO format.

**But there's another issue:** When a `date` object is used with `timedelta`, the result is still a `date` object. Calling `.isoformat()` on a `date` object returns `"YYYY-MM-DD"`, not `"YYYY-MM-DDTHH:MM:SSZ"`. The `+ "Z"` at the end creates strings like `"2025-12-05Z"` which is NOT valid ISO 8601 format.

**Finding:** The date parsing does not shift the date, but the type mismatch may cause the query to fail or behave unexpectedly.

---

## STEP 4 — CALENDAR QUERY WINDOW

### Query Window Construction

**File:** `app/integrations/calendar.py` (lines 115-116)

```python
start_range = (target_date - timedelta(days=days_buffer)).isoformat() + "Z"
end_range = (target_date + timedelta(days=days_buffer)).isoformat() + "Z"
```

**Default:** `days_buffer = 7` (line 109)

**For December 12, 2025:**
- `start_range = (2025-12-12 - 7 days).isoformat() + "Z"` = `"2025-12-05Z"`
- `end_range = (2025-12-12 + 7 days).isoformat() + "Z"` = `"2025-12-19Z"`

### Answers

**Question 1:** What exact `timeMin` and `timeMax` values are sent to Google Calendar?

**Answer:** 
- `timeMin = "2025-12-05Z"` (December 5, 2025 at 00:00:00 UTC, but formatted incorrectly)
- `timeMax = "2025-12-19Z"` (December 19, 2025 at 00:00:00 UTC, but formatted incorrectly)

**However, the format is INVALID:** `"2025-12-05Z"` is not valid ISO 8601. It should be `"2025-12-05T00:00:00Z"` for datetime or just `"2025-12-05"` for date-only.

**Question 2:** Are they midnight → 23:59 of the target date?

**Answer:** NO. They are:
- `target_date - 7 days` (start of day, but incorrectly formatted)
- `target_date + 7 days` (start of day, but incorrectly formatted)

**Question 3:** Confirm whether October 17 could be included in this window.

**Answer:** NO. October 17, 2025 is approximately 56 days before December 12, 2025. The query window is `[December 5, December 19]`, which does not include October 17.

**However, if the query fails due to invalid date format, Google Calendar API may:**
- Return an error
- Return no results
- Return unexpected results
- Fall back to some default behavior

**Finding:** The query window should exclude October 17, but if the query fails due to invalid date format, the behavior is undefined.

---

## STEP 5 — CLIENT NAME MATCHING VALIDATION

### Matching Logic

**File:** `app/integrations/calendar.py` (lines 131-137)

```python
client_lower = client_name.lower()

for event in events:
    summary = event.get("summary", "").lower()
    description = event.get("description", "").lower()

    if client_lower in summary or client_lower in description:
        return {
            ...
        }
```

### Answers

**Question 1:** What fields are searched?

**Answer:** `summary` and `description` fields of calendar events.

**Question 2:** Is matching exact, substring, or case-insensitive?

**Answer:** **Case-insensitive substring matching.**
- `client_lower = client_name.lower()` (line 131)
- `summary = event.get("summary", "").lower()` (line 134)
- `description = event.get("description", "").lower()` (line 135)
- `if client_lower in summary or client_lower in description:` (line 137)

**Question 3:** Could an October meeting match MTCA while a December one exists but is skipped?

**Answer:** YES, if:
1. The query window excludes December 12 (due to format error or other issue)
2. The query returns events from a different time range (e.g., if the API ignores the invalid format and uses a default range)
3. October 17 event is in the returned set and matches "mtca"
4. December 12 event is not in the returned set

**However, the function returns the FIRST match (line 138-150), so if both October and December meetings are in the results, it would return whichever appears first in the `events` list, which is ordered by `orderBy="startTime"` (line 126).

**Finding:** Client name matching is case-insensitive substring, which should work correctly. The issue is likely in the query window or date format.

---

## STEP 6 — RETURN VALUE SOURCE

### Return Path Analysis

**File:** `app/integrations/calendar.py` (lines 106-152)

The function `get_meeting_by_client_and_date()`:
1. Constructs query window (lines 115-116)
2. Queries Google Calendar API (lines 120-127)
3. Iterates through returned events (line 133)
4. Returns FIRST match (lines 138-150)
5. Returns None if no match (line 152)

**If this function returns None:**
- Orchestrator should return error (lines 107-117)
- Should NOT fall back to `get_most_recent_meeting_by_client()`

**If this function returns a meeting:**
- It should be the December 12 meeting (if it exists and matches)

**But if October 17 is being returned, it means:**
- Either `get_meeting_by_client_and_date()` returned October 17 (wrong match), OR
- The fallback `get_most_recent_meeting_by_client()` was called (date was not provided or query failed)

### Answer

**Question 1:** From which function does the October 17 event originate?

**Answer:** Cannot determine without runtime inspection, but based on code analysis:

**Most Likely:** `get_most_recent_meeting_by_client()` (fallback function)

**Evidence:**
- If `get_meeting_by_client_and_date()` worked correctly, it should return December 12 (if it exists) or None (if it doesn't)
- If it returns None and a date was provided, orchestrator should return error (lines 107-117)
- The fallback at line 121 only executes if `date_str` was falsy OR if an exception bypassed the error return

**However, there's a possibility:** If `get_meeting_by_client_and_date()` queries with invalid date format and Google Calendar API returns events from a default range (e.g., past 90 days), it might return October 17 as the first match.

**Question 2:** Prove this by tracing the return path.

**Return Path if date_str is provided:**
1. Line 96: `if date_str:` → enters branch
2. Line 98: `target_date = self._parse_target_date(date_str)` → may raise exception
3. Line 99-102: `get_meeting_by_client_and_date()` → may return None or a meeting
4. Line 103-104: If exception, `calendar_event = None`
5. Line 107-117: If `not calendar_event`, return error (should NOT reach fallback)
6. Line 120-121: Fallback only if `not calendar_event` AND date_str was falsy

**Return Path if date_str is None/empty:**
1. Line 96: `if date_str:` → skips branch, `calendar_event` remains None
2. Line 120-121: `if not calendar_event:` → enters fallback
3. Line 121: `get_most_recent_meeting_by_client(client_name)` → returns October 17

**Conclusion:** If October 17 is returned, the most likely path is that `date_str` was None/empty, causing the fallback to execute.

---

## STEP 7 — FINAL DIAGNOSIS

### SINGLE ROOT CAUSE

**ROOT CAUSE: Date Entity Not Extracted or Invalid Format**

The LLM intent recognition is not extracting the date in the required `YYYY-MM-DD` format, OR the date string is in an invalid format that causes `_parse_target_date()` to raise an exception, OR the date string is None/empty.

When `date_str` is None/empty or parsing fails, the orchestrator falls back to `get_most_recent_meeting_by_client()`, which returns October 17, 2025 (the most recent meeting within the 90-day window).

### Supporting Evidence

**File:** `app/llm/prompts.py` (line 12)
- Prompt specifies: `"date": "YYYY-MM-DD or null"`
- Does NOT explicitly instruct LLM to convert "December 12th, 2025" to "2025-12-12"

**File:** `app/agent/orchestrator.py` (line 98)
- `target_date = self._parse_target_date(date_str)`
- If `date_str` is not in `YYYY-MM-DD` format, `datetime.fromisoformat()` will raise `ValueError`

**File:** `app/agent/orchestrator.py` (line 103-104)
- `except Exception: calendar_event = None`
- Any exception during parsing sets `calendar_event = None`

**File:** `app/agent/orchestrator.py` (line 120-121)
- `if not calendar_event: calendar_event = get_most_recent_meeting_by_client(client_name)`
- Fallback executes when `calendar_event` is None

**File:** `app/integrations/calendar.py` (line 96-104)
- `get_most_recent_meeting_by_client()` uses `days_back=90` default
- Returns most recent meeting within past 90 days
- October 17, 2025 is within this window (if current date is after October 17, 2025)

### Why October 17 is Selected Deterministically

1. `get_most_recent_meeting_by_client()` calls `search_meetings_by_client(client_name)` with `days_back=90` default
2. This queries meetings from the past 90 days
3. October 17, 2025 is the most recent MTCA meeting within that window
4. Function sorts by `start` field (string sort) and returns first (line 103)
5. October 17 is returned as the most recent match

### Why December 12 is Ignored

1. **If date was not extracted:** `date_str` is None, so date-aware branch is skipped, fallback executes
2. **If date format is invalid:** `_parse_target_date()` raises exception, `calendar_event` set to None, but error return may be bypassed if exception handling is incorrect
3. **If date query fails:** `get_meeting_by_client_and_date()` returns None due to invalid date format in query, but orchestrator may not return error if exception occurred

**Most Likely Scenario:** The LLM returns the date in natural language format ("December 12, 2025") or null, causing `_parse_target_date()` to fail, which triggers the fallback to most recent meeting.

### Additional Issues Identified

1. **Type Mismatch:** `get_meeting_by_client_and_date()` expects `datetime` but receives `date`, causing invalid ISO format strings (`"2025-12-05Z"` instead of `"2025-12-05T00:00:00Z"`)

2. **Invalid Date Format:** The query uses `date.isoformat() + "Z"` which creates invalid ISO 8601 strings

3. **Exception Handling:** Broad `except Exception:` may hide specific parsing errors

---

## Summary

**Root Cause:** Date entity is either not extracted by LLM, extracted in wrong format, or parsing fails, causing fallback to most recent meeting (October 17).

**Supporting Code:**
- `app/llm/prompts.py:12` - Prompt does not enforce date format conversion
- `app/agent/orchestrator.py:98` - `_parse_target_date()` will fail on non-ISO format
- `app/agent/orchestrator.py:103-104` - Exception sets `calendar_event = None`
- `app/agent/orchestrator.py:120-121` - Fallback executes when `calendar_event` is None
- `app/integrations/calendar.py:96-104` - Fallback returns most recent meeting (October 17)

**End of Diagnostic**


