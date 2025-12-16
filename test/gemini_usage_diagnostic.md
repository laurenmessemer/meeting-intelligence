# Gemini / google.generativeai Usage Diagnostic Report
**Generated:** Read-only codebase inspection  
**Analysis Type:** Static code analysis + Runtime verification  
**Date:** Current

---

## Executive Summary

**Status:** ✅ **SINGLE GEMINI CLIENT IMPLEMENTATION**

**Findings:**
- ✅ Only one file imports `google.generativeai`: `app/llm/client.py`
- ✅ Single client implementation: `GeminiClient` class
- ✅ Model discovery via `genai.list_models()` (not hardcoded)
- ⚠️ `Config.GEMINI_MODEL` is defined but NOT used
- ⚠️ Model selection uses hardcoded preferred list, not config

**Root Cause of 404 Errors:** Model discovery selects from preferred list; if none available, may fail or select unavailable model.

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

### 1.2 Indirect Google Imports

**File:** `app/integrations/calendar.py`  
**Lines:** 2-5  
**Imports:**
- `from google.oauth2.credentials import Credentials`
- `from google.auth.transport.requests import Request`
- `from google_auth_oauthlib.flow import InstalledAppFlow`
- `from googleapiclient.discovery import build`

**Status:** ✅ **NOT GENERATIVEAI** - These are Google OAuth/API client imports, not Gemini

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

**Context:** Inside `GeminiClient.__init__()` method

**Timing:** ✅ **Runtime** - Called when `GeminiClient()` is instantiated (lazy initialization)

**Condition:** Only if `Config.GEMINI_API_KEY` is set (raises RuntimeError if not)

**Status:** ✅ **SINGLE CONFIGURATION POINT**

### 2.2 Other configure() Calls

**Search Results:** None found

**Conclusion:** ✅ **Only one `genai.configure()` call** - No conflicts or multiple configurations

---

## 3. GenerativeModel Instantiations

### 3.1 Model Instantiation Location

**File:** `app/llm/client.py`  
**Line:** 40  
**Code:**
```python
return genai.GenerativeModel(model_name)
```

**Context:** Inside `GeminiClient._select_model()` method

**Model Name Source:** ✅ **Dynamic discovery** - Not from `Config.GEMINI_MODEL`

### 3.2 Model Selection Logic

**File:** `app/llm/client.py`  
**Lines:** 18-47

**Process:**
1. Calls `genai.list_models()` (line 26)
2. Filters for models with `generateContent` support (line 27)
3. Checks preferred models list (lines 30-35):
   - `"models/gemini-2.5-flash"`
   - `"models/gemini-2.5-pro"`
   - `"models/gemini-flash-latest"`
   - `"models/gemini-pro-latest"`
4. Returns first available model from preferred list (line 40)
5. Raises RuntimeError if none found (line 42)

**Model Name:** ✅ **Dynamic** - Selected from API, not hardcoded

**Config.GEMINI_MODEL Usage:** ❌ **NOT USED** - Model selection ignores `Config.GEMINI_MODEL`

### 3.3 Other GenerativeModel Instantiations

**Search Results:** None found

**Conclusion:** ✅ **Single instantiation point** - Only in `_select_model()` method

---

## 4. list_models() Calls

### 4.1 list_models() Location

**File:** `app/llm/client.py`  
**Line:** 26  
**Code:**
```python
for m in genai.list_models()
```

**Context:** Inside `GeminiClient._select_model()` method

**Purpose:** Discover available models that support `generateContent`

**Status:** ✅ **SINGLE CALL** - Only one `list_models()` usage

### 4.2 Other list_models() Calls

**Search Results:** None found

**Conclusion:** ✅ **Single discovery point** - Model discovery happens once per client initialization

---

## 5. Gemini Model Name References

### 5.1 Hardcoded Model Names

**File:** `app/llm/client.py`  
**Lines:** 30-35  
**Code:**
```python
preferred_models = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
]
```

**Status:** ⚠️ **HARDCODED PREFERRED LIST** - These are preference order, not direct usage

**Usage:** Used to select from available models (line 37-40)

### 5.2 Config.GEMINI_MODEL Reference

**File:** `app/config.py`  
**Line:** 18  
**Code:**
```python
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
```

**Runtime Value:** `'gemini-pro'` (from `.env`)

**Usage in Code:** ❌ **NOT USED** - `Config.GEMINI_MODEL` is defined but never referenced

**Search Results:** No references to `Config.GEMINI_MODEL` in `app/llm/client.py`

**Conclusion:** ⚠️ **CONFIG IGNORED** - Model selection does not use `Config.GEMINI_MODEL`

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
app/agent/intents.py:24 (chat function call)
  ↓
app/llm/client.py:77 (chat function)
  ↓
app/llm/client.py:84 (GeminiClient instantiation - if None)
  ↓
app/llm/client.py:9 (GeminiClient.__init__)
  ↓
app/llm/client.py:14 (genai.configure call)
  ↓
app/llm/client.py:16 (self.model = self._select_model())
  ↓
app/llm/client.py:18 (_select_model method)
  ↓
app/llm/client.py:26 (genai.list_models call)
  ↓
app/llm/client.py:40 (genai.GenerativeModel instantiation)
  ↓
[USAGE] self.model.generate_content() at line 64
```

### 6.2 Critical Path Points

**Configuration:** `app/llm/client.py:14` - `genai.configure(api_key=Config.GEMINI_API_KEY)`

**Model Discovery:** `app/llm/client.py:26` - `genai.list_models()`

**Model Instantiation:** `app/llm/client.py:40` - `genai.GenerativeModel(model_name)`

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

---

## 8. Correlation with 404 Model Errors

### 8.1 Model Selection Failure Points

**Failure Point 1: `genai.list_models()` fails**
- **Location:** `app/llm/client.py:26`
- **Error:** Would raise exception in `_select_model()`
- **Impact:** `RuntimeError: Gemini model discovery failed`

**Failure Point 2: No preferred models available**
- **Location:** `app/llm/client.py:37-44`
- **Error:** `RuntimeError: No supported Gemini models found`
- **Impact:** Client initialization fails

**Failure Point 3: Selected model doesn't exist**
- **Location:** `app/llm/client.py:40`
- **Error:** `404` or `NotFound` when creating `GenerativeModel`
- **Impact:** Model instantiation fails

**Failure Point 4: Model name format mismatch**
- **Location:** `app/llm/client.py:40`
- **Error:** Model name from `list_models()` may not match expected format
- **Impact:** `GenerativeModel()` may fail with 404

### 8.2 Most Likely Offending Call

**Location:** `app/llm/client.py:40`

**Code:**
```python
return genai.GenerativeModel(model_name)
```

**Why This Is Likely:**
1. Model name comes from `genai.list_models()` - may return model names that don't work
2. Preferred models list may contain models not available for this API key
3. Model name format may be incorrect (e.g., missing `models/` prefix or wrong version)
4. No validation that model actually exists before instantiation

**Error Pattern:** 404 errors suggest model name is invalid or not accessible

### 8.3 Config.GEMINI_MODEL Discrepancy

**Defined Value:** `Config.GEMINI_MODEL = 'gemini-pro'` (from `.env`)

**Actual Usage:** ❌ **NOT USED** - Model selection ignores this value

**Impact:** 
- Environment variable `GEMINI_MODEL` has no effect
- Model selection relies entirely on API discovery
- If discovery fails or returns invalid models, 404 errors occur

---

## 9. File-by-File Breakdown

### 9.1 app/llm/client.py

**Imports:**
- Line 3: `import google.generativeai as genai` ✅

**genai.configure():**
- Line 14: `genai.configure(api_key=Config.GEMINI_API_KEY)` ✅

**genai.list_models():**
- Line 26: `for m in genai.list_models()` ✅

**GenerativeModel:**
- Line 40: `return genai.GenerativeModel(model_name)` ✅

**Model Names:**
- Lines 30-35: Hardcoded preferred list ✅
- No use of `Config.GEMINI_MODEL` ❌

**Status:** ✅ **SINGLE SOURCE** - All Gemini usage in this file

### 9.2 app/config.py

**Model Configuration:**
- Line 18: `GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")` ✅

**Usage:** ❌ **NOT REFERENCED** - Defined but never used

**Runtime Value:** `'gemini-pro'` (from `.env`)

### 9.3 Other Files

**app/agent/intents.py:**
- Line 4: `from app.llm.client import chat` ✅
- Line 24: `chat()` function call ✅
- **No direct Gemini usage** ✅

**app/tools/summarize.py:**
- Line 4: `from app.llm.client import chat` ✅
- Line 42: `chat()` function call ✅
- **No direct Gemini usage** ✅

**app/tools/followup.py:**
- Line 3: `from app.llm.client import chat` ✅
- Line 40: `chat()` function call ✅
- **No direct Gemini usage** ✅

**app/api/chat.py:**
- **No Gemini imports** ✅
- **No direct Gemini usage** ✅

---

## 10. Summary

### 10.1 All Gemini Usage Locations

| File | Line | Operation | Model Name Source |
|------|------|----------|-------------------|
| `app/llm/client.py` | 3 | `import google.generativeai` | N/A |
| `app/llm/client.py` | 14 | `genai.configure()` | N/A |
| `app/llm/client.py` | 26 | `genai.list_models()` | N/A |
| `app/llm/client.py` | 40 | `genai.GenerativeModel()` | Dynamic (from list_models) |
| `app/llm/client.py` | 64 | `self.model.generate_content()` | Uses discovered model |

**Total:** 5 operations, all in `app/llm/client.py`

### 10.2 Model Name Resolution

**Config.GEMINI_MODEL:** ❌ **NOT USED**

**Actual Model Selection:**
1. Calls `genai.list_models()` to discover available models
2. Filters for `generateContent` support
3. Selects first match from preferred list:
   - `models/gemini-2.5-flash`
   - `models/gemini-2.5-pro`
   - `models/gemini-flash-latest`
   - `models/gemini-pro-latest`
4. Creates `GenerativeModel(model_name)` with discovered name

**Risk:** If preferred models are not available or API returns invalid names, 404 errors occur

### 10.3 Single Source of Failure

**Most Likely Offending Call:** `app/llm/client.py:40`

**Code:**
```python
return genai.GenerativeModel(model_name)
```

**Why:**
- Model name comes from API discovery
- No validation that model is accessible
- Preferred models may not be available for this API key
- Model name format may be incorrect

**Error Pattern:** 404 errors indicate model name is invalid or not accessible

---

## 11. Findings Summary

### ✅ Working Correctly

1. **Single Import Point:** Only `app/llm/client.py` imports `google.generativeai`
2. **Single Configuration:** Only one `genai.configure()` call
3. **Single Client:** Only `GeminiClient` class exists
4. **No Conflicts:** No multiple clients or configurations

### ⚠️ Potential Issues

1. **Config.GEMINI_MODEL Ignored:**
   - Defined in config but never used
   - Model selection relies entirely on API discovery
   - Environment variable has no effect

2. **Model Discovery Risk:**
   - `genai.list_models()` may return models not accessible
   - Preferred models may not be available
   - No fallback to `Config.GEMINI_MODEL`

3. **404 Error Source:**
   - Most likely: `genai.GenerativeModel(model_name)` at line 40
   - Model name from discovery may be invalid
   - No validation before instantiation

---

**End of Diagnostic Report**


