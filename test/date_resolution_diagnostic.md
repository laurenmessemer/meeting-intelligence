# Date Resolution Diagnostic Report

**Issue:** "Summarize my meeting with MTCA on December 12th, 2025" returns meeting from October 17, 2025 instead of December 12, 2025.

**Analysis Date:** Current  
**Mode:** READ-ONLY (no code changes)

---

## Observed Behavior

**User Input:** "Summarize my meeting with MTCA on December 12th, 2025"  
**Expected Result:** Meeting from December 12, 2025  
**Actual Result:** Meeting from October 17, 2025  
**Conclusion:** Date filtering is being ignored or failing silently.

---

## A) Intent Recognition - Entity Extraction

### Prompt Templates

**File:** `app/llm/prompts.py`

**System Prompt (lines 3-18):**
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

**User Prompt (lines 20-22):**
```
INTENT_RECOGNITION_USER = """User message: {user_message}

Classify the intent and extract entities."""
```

### JSON Parsing Logic

**File:** `app/agent/intents.py` (lines 31-37)

```python
try:
    result = json.loads(response_text)
    return {
        "intent": result.get("intent", "other"),
        "confidence": float(result.get("confidence", 0.0)),
        "entities": result.get("entities", {})
    }
except (json.JSONDecodeError, ValueError, KeyError):
    # Fallback to default
    return {
        "intent": "other",
        "confidence": 0.0,
        "entities": {}
    }
```

### Analysis

**Expected Entity Format:**
- `entities.date` should be `"YYYY-MM-DD"` format (e.g., `"2025-12-12"`)
- User input: "December 12th, 2025" must be normalized by LLM to `"2025-12-12"`

**Potential Issues:**
1. **LLM may not normalize date:** The prompt specifies `"YYYY-MM-DD or null"` but does not explicitly instruct the LLM to convert natural language dates ("December 12th, 2025") to ISO format. The LLM may return:
   - `null` (if it doesn't recognize the date format)
   - `"December 12, 2025"` (natural language, not ISO)
   - `"12/12/2025"` (other format)
   - `"2025-12-12"` (correct ISO format)

2. **Fallback drops entities:** If JSON parsing fails (line 38), the fallback returns `entities: {}`, completely losing the date entity.

3. **No validation:** There is no validation that `entities.get("date")` is actually in `YYYY-MM-DD` format before use.

**Finding:** The prompt does not explicitly instruct the LLM to convert natural language dates to ISO format. The LLM may return the date in an unexpected format or as `null`.

---

## B) Orchestrator Date Usage

### Code Analysis

**File:** `app/agent/orchestrator.py` (lines 79-94)

```python
# Find most recent meeting for client
date_str = entities.get("date")
calendar_event = None

if date_str:
    try:
        target_date = datetime.fromisoformat(date_str)
        calendar_event = get_meeting_by_client_and_date(
            client_name=client_name,
            target_date=target_date,
        )
    except ValueError:
        calendar_event = None

# Fallback to most recent if no date match found
if not calendar_event:
    calendar_event = get_most_recent_meeting_by_client(client_name)
```

### Analysis

**Date IS Used:** The orchestrator DOES check for `entities.get("date")` and attempts to use it.

**Critical Issues:**

1. **Silent Failure on ValueError:** If `datetime.fromisoformat(date_str)` fails (line 84), the exception is caught and `calendar_event` is set to `None`. This silently falls back to `get_most_recent_meeting_by_client()` without logging or error indication.

2. **Fallback Always Executes:** If `get_meeting_by_client_and_date()` returns `None` (no match found), the code immediately falls back to `get_most_recent_meeting_by_client()` (line 94). This means:
   - If date parsing fails → fallback to most recent
   - If date match not found → fallback to most recent
   - No distinction between "date not provided" and "date match not found"

3. **No Logging:** There is no logging to indicate:
   - What date string was extracted
   - Whether date parsing succeeded
   - Whether `get_meeting_by_client_and_date()` was called
   - Why the fallback was used

**Finding:** The orchestrator attempts to use the date, but silently falls back to "most recent" if any step fails. This explains why the wrong meeting is returned without error.

---

## C) Calendar Integration - Date Format and Query Window

### Calendar Event Format

**File:** `app/integrations/calendar.py` (lines 65-77)

```python
return [
    {
        'id': event.get('id'),
        'summary': event.get('summary', ''),
        'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
        ...
    }
    for event in events
]
```

**Start Field Format:**
- Can be ISO datetime: `"2025-10-17T09:30:00-05:00"` or `"2025-10-17T09:30:00Z"`
- Can be date-only: `"2025-10-17"`
- Depends on whether the calendar event is all-day or timed

### Query Window Analysis

**File:** `app/integrations/calendar.py`

**get_recent_meetings()** (lines 43-77):
- Default `days_back = 30`
- `timeMin = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'`
- `timeMax = datetime.utcnow().isoformat() + 'Z'`
- **Query window:** `[utcnow - 30 days, utcnow]` (past 30 days only)

**search_meetings_by_client()** (lines 80-93):
- Default `days_back = 90`
- Calls `get_recent_meetings(days_back)` (line 87)
- **Query window:** `[utcnow - 90 days, utcnow]` (past 90 days only)

**Critical Finding:**

If the current date is **after March 12, 2026**, then December 12, 2025 is **more than 90 days in the past** and will be **excluded from the query window**.

**Example Calculation:**
- Current date: March 15, 2026
- Requested date: December 12, 2025
- Days difference: ~93 days
- Query window: `[December 15, 2025, March 15, 2026]`
- **December 12, 2025 is OUTSIDE the query window**

**Conclusion:** If the runtime date is after March 12, 2026, the December 12, 2025 meeting will never be retrieved by `search_meetings_by_client()` because it's outside the 90-day window.

### Sorting Logic

**File:** `app/integrations/calendar.py` (lines 96-104)

```python
def get_most_recent_meeting_by_client(client_name: str) -> Optional[Dict[str, Any]]:
    """Get the most recent meeting for a client."""
    meetings = search_meetings_by_client(client_name)
    if not meetings:
        return None
    
    # Sort by start time, most recent first
    meetings.sort(key=lambda x: x['start'], reverse=True)
    return meetings[0]
```

**Sorting Issue:**
- Sorts by raw string value of `meeting['start']`
- If formats are mixed (some ISO datetime, some date-only), string sorting may not match chronological order
- Example: `"2025-10-17"` vs `"2025-10-17T09:30:00Z"` - string sort may not be correct

**Finding:** String-based sorting may produce incorrect results if date formats are mixed.

---

## D) Date-Specific Lookup Function

**File:** `app/integrations/calendar.py` (lines 106-130)

```python
def get_meeting_by_client_and_date(
    client_name: str,
    target_date: datetime,
    tolerance_days: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Find a meeting for a client on or near a specific date.
    """
    meetings = search_meetings_by_client(client_name)
    if not meetings:
        return None

    for meeting in meetings:
        try:
            start_str = meeting["start"]
            meeting_date = datetime.fromisoformat(
                start_str.replace("Z", "+00:00")
            )
        except Exception:
            continue

        if abs((meeting_date.date() - target_date.date()).days) <= tolerance_days:
            return meeting

    return None
```

### Analysis

**Function Logic:**
1. Calls `search_meetings_by_client(client_name)` which uses `days_back=90` default
2. Iterates through returned meetings
3. Parses `meeting["start"]` with `datetime.fromisoformat()`
4. Compares dates with 1-day tolerance
5. Returns first match or `None`

**Critical Issues:**

1. **Depends on Query Window:** This function can only find meetings that are within the 90-day window. If December 12, 2025 is outside that window, it will never be found.

2. **Date Parsing May Fail:** If `meeting["start"]` is date-only (`"2025-10-17"`), `datetime.fromisoformat()` will succeed. But if it's an unexpected format, the exception is caught and the meeting is skipped (line 124).

3. **No Logging:** No indication of:
   - How many meetings were searched
   - Which meetings failed parsing
   - What the closest match was

**Finding:** This function will return `None` if:
- The requested date is outside the 90-day window
- No meetings match within 1-day tolerance
- All meetings fail date parsing

---

## E) Calendar Query Window Exclusion

### Explicit Calculation

**Scenario:** User requests meeting from "December 12th, 2025"

**Query Window (from search_meetings_by_client):**
- `days_back = 90` (default)
- `timeMin = utcnow - 90 days`
- `timeMax = utcnow`

**If current date is after March 12, 2026:**
- December 12, 2025 is **>90 days in the past**
- Meeting is **excluded from query results**
- `get_meeting_by_client_and_date()` will never see this meeting
- Falls back to `get_most_recent_meeting_by_client()` which returns October 17, 2025 (most recent within window)

**Conclusion:** The calendar query window (`days_back=90`) excludes the requested meeting date if it's more than 90 days in the past.

---

## F) API Request Flow Verification

**File:** `app/api/chat.py` (lines 32-53)

```python
@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    memory_repo = MemoryRepo(db)
    orchestrator = Orchestrator(memory_repo)
    
    result = orchestrator.process_message(request.message)
    
    return ChatResponse(
        message=result.get("message", ""),
        metadata=result.get("metadata", {})
    )
```

**Analysis:**
- Request message is passed directly to `orchestrator.process_message()` without modification
- No lowercasing or trimming that would remove date phrases
- UI sends exact user input to the endpoint

**Finding:** The API correctly passes the user message unchanged to the orchestrator.

---

## Complete Call Chain

```
POST /api/chat
  ↓
app/api/chat.py:48 → orchestrator.process_message(request.message)
  ↓
app/agent/orchestrator.py:31 → recognize_intent(user_message)
  ↓
app/agent/intents.py:24 → chat() with INTENT_RECOGNITION prompts
  ↓
app/llm/client.py → Gemini API call
  ↓
app/agent/intents.py:32 → json.loads(response_text) → entities dict
  ↓
app/agent/orchestrator.py:79 → date_str = entities.get("date")
  ↓
app/agent/orchestrator.py:84 → datetime.fromisoformat(date_str) [may fail]
  ↓
app/agent/orchestrator.py:85 → get_meeting_by_client_and_date(...)
  ↓
app/integrations/calendar.py:114 → search_meetings_by_client(client_name)
  ↓
app/integrations/calendar.py:87 → get_recent_meetings(days_back=90)
  ↓
app/integrations/calendar.py:51 → timeMin = utcnow - 90 days, timeMax = utcnow
  ↓
Google Calendar API → Returns only meetings within [utcnow-90, utcnow]
  ↓
app/integrations/calendar.py:118-128 → Iterate meetings, compare dates
  ↓
[If no match or date outside window] → Returns None
  ↓
app/agent/orchestrator.py:94 → Fallback: get_most_recent_meeting_by_client(client_name)
  ↓
Returns October 17, 2025 (most recent within 90-day window)
```

---

## Root Cause Analysis

### Most Likely Root Cause

**PRIMARY ISSUE: Calendar Query Window Excludes Requested Date**

The requested meeting date (December 12, 2025) is **outside the 90-day query window** if the current runtime date is after March 12, 2026. The `search_meetings_by_client()` function uses `days_back=90` by default, which means it only queries meetings from the past 90 days. If December 12, 2025 is more than 90 days ago, it will never be retrieved from Google Calendar, causing `get_meeting_by_client_and_date()` to return `None`, which triggers the fallback to `get_most_recent_meeting_by_client()`.

**Supporting Evidence:**

1. **Code:** `app/integrations/calendar.py:80` - `search_meetings_by_client(client_name: str, days_back: int = 90)`
2. **Code:** `app/integrations/calendar.py:87` - `all_meetings = get_recent_meetings(days_back)`
3. **Code:** `app/integrations/calendar.py:51` - `timeMin = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'`
4. **Code:** `app/integrations/calendar.py:114` - `get_meeting_by_client_and_date()` calls `search_meetings_by_client()` which uses the 90-day window
5. **Code:** `app/agent/orchestrator.py:94` - Silent fallback when `get_meeting_by_client_and_date()` returns `None`

### Secondary Issues

1. **Date Format Normalization:** The LLM may not convert "December 12th, 2025" to "2025-12-12" format, causing `datetime.fromisoformat()` to fail silently.

2. **Silent Failure:** No logging or error indication when date parsing fails or when date-specific lookup returns `None`, making debugging difficult.

3. **String-Based Sorting:** `get_most_recent_meeting_by_client()` sorts by raw string, which may not work correctly with mixed date formats.

---

## Step-by-Step Inspection Tasks

### Task 1: Verify Intent Recognition Output

**Action:** Add temporary logging to `app/agent/intents.py` after line 36:
```python
# Log the extracted entities for debugging
print(f"DEBUG: Intent entities: {result.get('entities', {})}")
```

**Expected Output:** Should show `{"client_name": "MTCA", "date": "2025-12-12"}` or similar.

**If date is null or wrong format:** The LLM is not normalizing the date correctly.

### Task 2: Verify Orchestrator Date Handling

**Action:** Add temporary logging to `app/agent/orchestrator.py` after line 79:
```python
print(f"DEBUG: Extracted date_str: {date_str}")
print(f"DEBUG: Entities: {entities}")
```

**Expected Output:** Should show the date string extracted from entities.

**If date_str is None:** Intent recognition failed to extract date.

**If date_str is not "YYYY-MM-DD":** Date format normalization failed.

### Task 3: Verify Calendar Query Window

**Action:** Add temporary logging to `app/integrations/calendar.py` after line 51:
```python
print(f"DEBUG: Query window: timeMin={time_min}, timeMax={time_max}")
print(f"DEBUG: Requested date (Dec 12, 2025) is within window: {datetime(2025, 12, 12).isoformat() + 'Z' >= time_min}")
```

**Expected Output:** Should show whether December 12, 2025 is within the query window.

**If outside window:** This is the root cause - the meeting is excluded from the query.

### Task 4: Verify Date-Specific Lookup

**Action:** Add temporary logging to `app/integrations/calendar.py` inside `get_meeting_by_client_and_date()`:
```python
print(f"DEBUG: Searching {len(meetings)} meetings for date {target_date.date()}")
for meeting in meetings:
    print(f"DEBUG: Meeting date: {meeting['start']}")
```

**Expected Output:** Should show all meetings being searched and their dates.

**If no meetings match:** Either the date is outside the window or parsing failed.

---

## Minimal Recommended Fix (DESCRIBE ONLY)

### Fix 1: Expand Query Window for Date-Specific Requests

**Location:** `app/integrations/calendar.py`

**Change:** Modify `get_meeting_by_client_and_date()` to use a larger `days_back` value when a specific date is requested, or query a date range around the target date instead of relying on the default 90-day window.

**Approach:**
- Calculate the number of days between `target_date` and `utcnow`
- If `target_date` is in the past and more than 90 days ago, expand `days_back` to include it
- Or, query a specific date range: `[target_date - tolerance_days, target_date + tolerance_days]` instead of `[utcnow - 90, utcnow]`

### Fix 2: Improve Date Format Normalization

**Location:** `app/llm/prompts.py`

**Change:** Update `INTENT_RECOGNITION_SYSTEM` to explicitly instruct the LLM to convert natural language dates to ISO format.

**Approach:**
- Add instruction: "Convert all dates to YYYY-MM-DD format (e.g., 'December 12th, 2025' → '2025-12-12')"
- Add example in the prompt showing the conversion

### Fix 3: Add Logging for Debugging

**Location:** `app/agent/orchestrator.py` and `app/integrations/calendar.py`

**Change:** Add logging statements to track:
- Extracted date string from entities
- Whether date parsing succeeded
- Query window boundaries
- Number of meetings found and searched
- Why fallback was used

**Approach:**
- Use Python `logging` module
- Log at INFO level for normal flow, WARNING for fallbacks

### Fix 4: Improve Error Handling

**Location:** `app/agent/orchestrator.py`

**Change:** Distinguish between "date not provided" and "date match not found" scenarios.

**Approach:**
- If `date_str` is provided but `get_meeting_by_client_and_date()` returns `None`, return an error message indicating the specific date was not found
- Only fall back to "most recent" if no date was provided in the request

---

## Summary

**Root Cause:** The calendar query window (`days_back=90`) excludes meetings more than 90 days in the past. If December 12, 2025 is outside this window, it will never be retrieved, causing the system to fall back to the most recent meeting within the window (October 17, 2025).

**Supporting Factors:**
1. Silent fallback when date-specific lookup fails
2. No logging to indicate why fallback occurred
3. Potential date format normalization issues in intent recognition

**Recommended Fix Priority:**
1. **HIGH:** Expand query window for date-specific requests
2. **MEDIUM:** Improve date format normalization in prompts
3. **MEDIUM:** Add logging for debugging
4. **LOW:** Improve error messages to distinguish scenarios

---

**End of Diagnostic Report**

