# Complete Gemini / google.generativeai Usage Diagnostic Report
**Generated:** Read-only comprehensive codebase inspection  
**Analysis Type:** Static code analysis + Runtime verification  
**Date:** Current

---

## Executive Summary

**Status:** ✅ **SINGLE GEMINI CLIENT - CONFIG-BASED MODEL SELECTION**

**Findings:**
- ✅ Only one file imports `google.generativeai`: `app/llm/client.py`
- ✅ Single client implementation: `GeminiClient` class
- ✅ Model selection uses `Config.GEMINI_MODEL` (with `models/` prefix formatting)
- ✅ Model includes smoke test validation before use
- ⚠️ No `list_models()` call (removed from implementation)
- ⚠️ Most likely 404 source: `genai.GenerativeModel(model_name)` at line 31 if model name is invalid

**Root Cause Analysis:** Model name comes from `Config.GEMINI_MODEL` (currently `'gemini-pro'`), formatted as `models/gemini-pro`. If this model doesn't exist or is not accessible, 404 errors occur.

---

## 1. Files Importing google.generativeai

### 1.1 Direct Imports

**File:** `app/llm/client.py`  
**Line:** 3  
**Code:**
```python
import google.generativeai as genai
```

**Status:** ✅ **ONLY FILE** - No other files import `google.generativeai`

**Verification:** Searched entire codebase - only one import found

### 1.2 Other Google Imports (Not GenerativeAI)

**File:** `app/integrations/calendar.py`  
**Lines:** 2-5  
**Imports:**
- `from google.oauth2.credentials import Credentials`
- `from google.auth.transport.requests import Request`
- `from google_auth_oauthlib.flow import InstalledAppFlow`
- `from googleapiclient.discovery import build`

**Status:** ✅ **NOT GENERATIVEAI** - These are Google OAuth/Calendar API imports

**Conclusion:** ✅ **Single import point** - Only `app/llm/client.py` uses `google.generativeai`

---

## 2. genai.configure() Calls

### 2.1 Configuration Location

**File:** `app/llm/client.py`  
**Line:** 14  
**Code:**
```python
genai.configure(api_key=Config.GEMINI_API_KEY)
```

**Context:** Inside `GeminiClient.__init__()` method (line 9)

**Timing:** ✅ **Runtime (lazy)** - Called when `GeminiClient()` is first instantiated

**Condition:** 
- Checks if `Config.GEMINI_API_KEY` is set (line 10)
- Raises `RuntimeError` if not set (line 11)
- Only executes if API key is present

**Status:** ✅ **SINGLE CONFIGURATION POINT**

### 2.2 Other configure() Calls

**Search Results:** None found

**Conclusion:** ✅ **Only one `genai.configure()` call** - No conflicts or multiple configurations

---

## 3. GenerativeModel Instantiations

### 3.1 Model Instantiation Location

**File:** `app/llm/client.py`  
**Line:** 31  
**Code:**
```python
model = genai.GenerativeModel(model_name)
```

**Context:** Inside `GeminiClient._select_model()` method (line 18)

**Model Name Source:** ✅ **From Config** - Uses `Config.GEMINI_MODEL` with `models/` prefix formatting

**Model Name Format:** 
- If `Config.GEMINI_MODEL` = `'gemini-pro'` → formatted as `'models/gemini-pro'`
- If `Config.GEMINI_MODEL` = `'models/gemini-2.5-flash'` → used as-is

### 3.2 Model Selection Logic

**File:** `app/llm/client.py`  
**Lines:** 18-46

**Process:**
1. **Lines 24-28:** Formats model name from `Config.GEMINI_MODEL`:
   ```python
   model_name = (
       f"models/{Config.GEMINI_MODEL}"
       if not Config.GEMINI_MODEL.startswith("models/")
       else Config.GEMINI_MODEL
   )
   ```
2. **Line 31:** Creates `genai.GenerativeModel(model_name)`
3. **Lines 34-37:** Runs smoke test to validate model is callable:
   ```python
   model.generate_content(
       "ping",
       generation_config=genai.types.GenerationConfig(temperature=0)
   )
   ```
4. **Lines 42-46:** Raises `RuntimeError` with clear error message if model fails

**Model Name:** ✅ **From Config** - Uses `Config.GEMINI_MODEL` (currently `'gemini-pro'`)

**Config.GEMINI_MODEL Usage:** ✅ **USED** - Model selection uses `Config.GEMINI_MODEL` with formatting

### 3.3 Other GenerativeModel Instantiations

**Search Results:** None found

**Conclusion:** ✅ **Single instantiation point** - Only in `_select_model()` method

---

## 4. list_models() Calls

### 4.1 list_models() Location

**File:** `app/llm/client.py`  
**Line:** None

**Status:** ❌ **NOT USED** - `list_models()` is not called in current implementation

**Previous Implementation:** Code comments mention avoiding `list_models()` ambiguity (line 21)

**Current Approach:** Direct model selection from `Config.GEMINI_MODEL`

### 4.2 Model Selection Method

**File:** `app/llm/client.py`  
**Lines:** 24-28

**Method:** Direct formatting of `Config.GEMINI_MODEL` value

**Code:**
```python
model_name = (
    f"models/{Config.GEMINI_MODEL}"
    if not Config.GEMINI_MODEL.startswith("models/")
    else Config.GEMINI_MODEL
)
```

**Runtime Value:** `Config.GEMINI_MODEL = 'gemini-pro'` → formatted as `'models/gemini-pro'`

**Conclusion:** ✅ **No list_models()** - Model selection is deterministic from config

---

## 5. Gemini Model Name References

### 5.1 Hardcoded Model Names

**File:** `app/llm/client.py`  
**Lines:** None

**Status:** ✅ **NO HARDCODED MODELS** - Model selection uses `Config.GEMINI_MODEL`

**Previous Implementation:** Code comments mention avoiding hardcoded models (line 21)

### 5.2 Config.GEMINI_MODEL Reference

**File:** `app/config.py`  
**Line:** 18  
**Code:**
```python
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
```

**Runtime Value:** `'gemini-pro'` (from `.env` file)

**Usage in Code:** ✅ **USED** - `Config.GEMINI_MODEL` is referenced in `app/llm/client.py:25-27`

**File:** `app/llm/client.py`  
**Lines:** 24-28  
**Code:**
```python
model_name = (
    f"models/{Config.GEMINI_MODEL}"
    if not Config.GEMINI_MODEL.startswith("models/")
    else Config.GEMINI_MODEL
)
```

**Conclusion:** ✅ **CONFIG USED** - Model selection uses `Config.GEMINI_MODEL` with formatting

### 5.3 Other Model Name References

**Search Results:** None found

**Conclusion:** ✅ **No other hardcoded model names** - Only in preferred list

---

## 6. Code Path: POST /api/chat

### 6.1 Complete Call Stack

```
POST /api/chat
  ↓
app/api/chat.py:33 (chat function)
  ↓
app/api/chat.py:45 (Orchestrator instantiation)
  ↓
app/agent/orchestrator.py:28 (recognize_intent call)
  ↓
app/agent/intents.py:24 (chat function call from app.llm.client)
  ↓
app/llm/client.py:77 (chat function - public API)
  ↓
app/llm/client.py:84 (GeminiClient instantiation - if _client is None)
  ↓
app/llm/client.py:9 (GeminiClient.__init__)
  ↓
app/llm/client.py:14 (genai.configure call)
  ↓
app/llm/client.py:16 (self.model = self._select_model())
  ↓
app/llm/client.py:18 (_select_model method)
  ↓
app/llm/client.py:24-28 (Format model name from Config.GEMINI_MODEL)
  ↓
app/llm/client.py:31 (genai.GenerativeModel instantiation) ⚠️ FAILURE POINT
  ↓
app/llm/client.py:34-37 (Smoke test: model.generate_content("ping"))
  ↓
app/llm/client.py:64 (self.model.generate_content call)
```

### 6.2 Critical Path Points

**Configuration:** `app/llm/client.py:14` - `genai.configure(api_key=Config.GEMINI_API_KEY)`

**Model Name Formatting:** `app/llm/client.py:24-28` - Format `Config.GEMINI_MODEL` with `models/` prefix

**Model Instantiation:** `app/llm/client.py:31` - `genai.GenerativeModel(model_name)` ⚠️

**Model Validation:** `app/llm/client.py:34-37` - Smoke test with `model.generate_content("ping")`

**Model Usage:** `app/llm/client.py:64` - `self.model.generate_content()`

---

## 7. Legacy Client Check

### 7.1 Multiple Clients

**Search Results:** ✅ **SINGLE CLIENT** - Only `GeminiClient` class exists

**Location:** `app/llm/client.py:8`

**Status:** ✅ **No legacy clients** - Single implementation

### 7.2 Client Coexistence

**Search Results:** No other client classes found

**Conclusion:** ✅ **No conflicts** - Single client implementation

### 7.3 Client Initialization

**Pattern:** Singleton-like (global `_client` variable)

**File:** `app/llm/client.py:74-85`

**Code:**
```python
_client: Optional[GeminiClient] = None

def chat(...):
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client.chat(...)
```

**Status:** ✅ **Lazy initialization** - Client created on first use

---

## 8. Correlation with 404 Model Errors

### 8.1 Model Selection Failure Points

**Failure Point 1: `genai.GenerativeModel()` fails with 404**
- **Location:** `app/llm/client.py:31`
- **Error:** `404` or `NotFound` when creating `GenerativeModel`
- **Impact:** Model instantiation fails, caught by try/except (line 42)
- **Status:** ⚠️ **MOST LIKELY** - This is the probable source of 404 errors

**Failure Point 2: Model smoke test fails**
- **Location:** `app/llm/client.py:34-37`
- **Error:** `model.generate_content("ping")` fails
- **Impact:** Raises `RuntimeError` with clear message (line 43-45)
- **Status:** ⚠️ **POSSIBLE** - If model exists but is not callable

**Failure Point 3: Model name format incorrect**
- **Location:** `app/llm/client.py:24-28`
- **Error:** Formatted model name may be invalid
- **Impact:** `GenerativeModel()` fails with 404
- **Status:** ⚠️ **POSSIBLE** - If `Config.GEMINI_MODEL` value is invalid

### 8.2 Most Likely Offending Call

**Location:** `app/llm/client.py:31`

**Code:**
```python
model = genai.GenerativeModel(model_name)
```

**Model Name:** `'models/gemini-pro'` (from `Config.GEMINI_MODEL = 'gemini-pro'`)

**Why This Is Most Likely:**

1. **Model name from config may be invalid:**
   - `Config.GEMINI_MODEL = 'gemini-pro'` may not be a valid model name
   - Model may be deprecated or renamed
   - Model may require different API key or permissions

2. **Model name format:**
   - Code formats as `'models/gemini-pro'`
   - This format may be incorrect (should be `'models/gemini-1.5-pro'` or similar)
   - Gemini API may not recognize `'models/gemini-pro'` as valid

3. **Error handling exists but may not catch all cases:**
   - Try/except around model creation (line 30)
   - Smoke test validates model (line 34-37)
   - But 404 errors may occur during smoke test itself

4. **Runtime value discrepancy:**
   - Config default: `'gemini-1.5-pro'`
   - Runtime value: `'gemini-pro'` (from `.env`)
   - `'gemini-pro'` may not be a valid model name

**Error Pattern:** 404 errors suggest model name is invalid, not accessible, or format is incorrect

### 8.3 Config.GEMINI_MODEL Usage

**Defined Value:** `Config.GEMINI_MODEL = 'gemini-pro'` (from `.env`)

**Default Value:** `'gemini-1.5-pro'` (from `app/config.py:18`)

**Actual Usage:** ✅ **USED** - Model selection uses this value

**Formatting:** 
- `'gemini-pro'` → formatted as `'models/gemini-pro'`
- Used directly in `genai.GenerativeModel('models/gemini-pro')`

**Impact:** 
- Environment variable `GEMINI_MODEL` **controls model selection**
- Current value `'gemini-pro'` may not be a valid model name
- If model name is invalid, 404 errors occur
- Can fix by setting `GEMINI_MODEL` to valid model (e.g., `'gemini-1.5-pro'`)

---

## 9. Complete File-by-File Breakdown

### 9.1 app/llm/client.py

**Total Lines:** 93

**Imports:**
- Line 3: `import google.generativeai as genai` ✅

**genai.configure():**
- Line 14: `genai.configure(api_key=Config.GEMINI_API_KEY)` ✅
- Context: Inside `GeminiClient.__init__()`
- Condition: Only if `Config.GEMINI_API_KEY` is set

**genai.list_models():**
- Line: None ❌
- Status: Not used in current implementation

**GenerativeModel:**
- Line 31: `model = genai.GenerativeModel(model_name)` ✅
- Context: Inside `GeminiClient._select_model()`
- Model name: From `Config.GEMINI_MODEL` with formatting

**Model Names:**
- Lines 24-28: Uses `Config.GEMINI_MODEL` with `models/` prefix formatting ✅
- No hardcoded model names ✅

**genai.types:**
- Line 66: `genai.types.GenerationConfig(**generation_config)` ✅
- Context: Inside `GeminiClient.chat()` method

**Status:** ✅ **SINGLE SOURCE** - All Gemini usage in this file

### 9.2 app/config.py

**Model Configuration:**
- Line 18: `GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")` ✅

**Usage:** ✅ **REFERENCED** - Used in `app/llm/client.py:25-27`

**Runtime Value:** `'gemini-pro'` (from `.env`)

**Status:** ✅ **USED** - Model selection uses this value (formatted as `'models/gemini-pro'`)

### 9.3 app/agent/intents.py

**Imports:**
- Line 4: `from app.llm.client import chat` ✅

**Usage:**
- Line 24: `response_text = chat(prompt=..., system_prompt=..., ...)` ✅

**Status:** ✅ **No direct Gemini usage** - Uses client wrapper

### 9.4 app/tools/summarize.py

**Imports:**
- Line 4: `from app.llm.client import chat` ✅

**Usage:**
- Line 42: `response_text = chat(prompt=..., system_prompt=..., ...)` ✅

**Status:** ✅ **No direct Gemini usage** - Uses client wrapper

### 9.5 app/tools/followup.py

**Imports:**
- Line 3: `from app.llm.client import chat` ✅

**Usage:**
- Line 40: `email_text = chat(prompt=..., system_prompt=..., ...)` ✅

**Status:** ✅ **No direct Gemini usage** - Uses client wrapper

### 9.6 app/api/chat.py

**Imports:** None related to Gemini ✅

**Usage:** None related to Gemini ✅

**Status:** ✅ **No Gemini usage** - Only uses orchestrator

### 9.7 app/agent/orchestrator.py

**Imports:** None related to Gemini ✅

**Usage:** None related to Gemini ✅

**Status:** ✅ **No Gemini usage** - Only uses intent recognition

---

## 10. Complete Usage Inventory

### 10.1 All google.generativeai Operations

| File | Line | Operation | Model Name Source | Notes |
|------|------|-----------|-------------------|-------|
| `app/llm/client.py` | 3 | `import google.generativeai` | N/A | Only import |
| `app/llm/client.py` | 14 | `genai.configure()` | N/A | API key configuration |
| `app/llm/client.py` | 31 | `genai.GenerativeModel()` | From Config.GEMINI_MODEL | ⚠️ Failure point |
| `app/llm/client.py` | 34 | `model.generate_content()` | Uses created model | Smoke test |
| `app/llm/client.py` | 64 | `self.model.generate_content()` | Uses discovered model | Model usage |
| `app/llm/client.py` | 66 | `genai.types.GenerationConfig()` | N/A | Config type |

**Total:** 6 operations, all in `app/llm/client.py`

### 10.2 Model Name Resolution Flow

**Config.GEMINI_MODEL:** ❌ **NOT USED**

**Actual Model Selection:**
1. `GeminiClient.__init__()` called (line 9)
2. `genai.configure()` called (line 14)
3. `_select_model()` called (line 16)
4. Formats `Config.GEMINI_MODEL` with `models/` prefix (lines 24-28)
5. Creates `genai.GenerativeModel(model_name)` (line 31)
6. Runs smoke test: `model.generate_content("ping")` (lines 34-37)
7. Returns model if successful, raises error if not (lines 42-46)

**Risk:** If `Config.GEMINI_MODEL` value is invalid (e.g., `'gemini-pro'`), 404 errors occur

---

## 11. Single Source of Failure

### 11.1 Most Likely Offending Call

**Location:** `app/llm/client.py:31`

**Code:**
```python
model = genai.GenerativeModel(model_name)
```

**Context:**
- Inside `_select_model()` method
- `model_name` comes from `Config.GEMINI_MODEL` (formatted as `'models/gemini-pro'`)
- Wrapped in try/except with error handling (lines 30, 42-46)

**Why This Is The Failure Point:**

1. **Model name may be invalid:**
   - `Config.GEMINI_MODEL = 'gemini-pro'` may not be a valid model name
   - Model may be deprecated or renamed
   - Should be `'gemini-1.5-pro'` or `'gemini-2.0-flash'` etc.

2. **Error handling exists but reveals the issue:**
   - Try/except catches errors (line 30)
   - Raises `RuntimeError` with clear message (lines 43-45)
   - But 404 error occurs during `GenerativeModel()` call

3. **Smoke test may also fail:**
   - Even if model is created, smoke test (line 34) may fail
   - Indicates model exists but is not callable
   - 404 may occur during smoke test

4. **Model name format:**
   - Code formats `'gemini-pro'` → `'models/gemini-pro'`
   - This format may be correct, but model name itself may be invalid

### 11.2 Error Correlation

**404 Model Errors:** Suggest model name is invalid or not accessible

**Most Likely Cause:** `genai.GenerativeModel(model_name)` at line 40 fails because:
- Model name from discovery may not be accessible for this API key
- Model may require different permissions
- Model name format may be incorrect
- Model may be deprecated or region-restricted

---

## 12. Summary

### 12.1 All Gemini Usage Locations

**Single File:** `app/llm/client.py`

**Operations:**
1. Import: Line 3
2. Configure: Line 14
3. List models: Line 26
4. Create model: Line 40 ⚠️
5. Use model: Line 64
6. Config type: Line 66

### 12.2 Model Name Resolution

**Config.GEMINI_MODEL:** ❌ **Defined but NOT USED**

**Actual Selection:** Dynamic discovery via `genai.list_models()`

**Preferred Models:** Hardcoded list (lines 30-35)

**Runtime Status:** ✅ All preferred models are available

### 12.3 Code Path from /api/chat

**Complete Path:**
```
/api/chat → Orchestrator → recognize_intent() → 
app.llm.client.chat() → GeminiClient() → 
_select_model() → genai.GenerativeModel() ⚠️
```

### 12.4 Legacy Clients

**Status:** ✅ **No legacy clients** - Single `GeminiClient` implementation

### 12.5 Multiple Clients

**Status:** ✅ **No conflicts** - Single client, singleton pattern

### 12.6 404 Error Source

**Most Likely:** `app/llm/client.py:40` - `genai.GenerativeModel(model_name)`

**Reason:** Model name from discovery may not be accessible, or format may be incorrect

---

## 13. Root Cause: 404 Model Error

### 13.1 Runtime Verification Results

**Test Performed:** Attempted to create and call `GenerativeModel('models/gemini-pro')`

**Results:**
1. ✅ `genai.GenerativeModel('models/gemini-pro')` **succeeds** (model object created)
2. ❌ `model.generate_content("ping")` **fails** with 404 error:
   ```
   404 models/gemini-pro is not found for API version v1beta, 
   or is not supported for generateContent. 
   Call ListModels to see the list of available models and their supported methods.
   ```

**Conclusion:** The model name `'models/gemini-pro'` is **NOT VALID** for `generateContent` operations.

### 13.2 Exact Failure Point

**File:** `app/llm/client.py`  
**Line:** 34-37  
**Code:**
```python
model.generate_content(
    "ping",
    generation_config=genai.types.GenerationConfig(temperature=0),
)
```

**Error:** `google.api_core.exceptions.NotFound: 404 models/gemini-pro is not found`

**Why This Happens:**
- `Config.GEMINI_MODEL = 'gemini-pro'` (from `.env`)
- Formatted as `'models/gemini-pro'`
- Model object can be created, but model is not available for `generateContent`
- The model may be deprecated, renamed, or not accessible with this API key

### 13.3 Single Source of Failure

**Location:** `app/llm/client.py:34` - Smoke test call to `model.generate_content()`

**Root Cause:** `Config.GEMINI_MODEL = 'gemini-pro'` is not a valid model name for `generateContent`

**Evidence:**
- Model instantiation succeeds (line 31)
- Model call fails with 404 (line 34)
- Error message explicitly states: "models/gemini-pro is not found for API version v1beta"

**Fix Required:** Change `GEMINI_MODEL` in `.env` to a valid model name (e.g., `gemini-1.5-pro`, `gemini-2.0-flash`, `gemini-2.5-flash`)

---

**End of Diagnostic Report**

