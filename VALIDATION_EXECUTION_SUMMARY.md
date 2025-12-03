# Validation Rules Execution Summary

This document explains **when** and **where** each validation rule is applied.

---

## ✅ AUTOMATIC VALIDATION (During Every Search)

When you click "Run Research Now" or the daily search runs, **these validations happen automatically**:

### 1. **LLM Extraction Phase** (`llm_processor.py`)

**Applied to each event as it's extracted:**

✅ **URL Improvement** (Lines 58-59)
- Automatically follows listing pages (`/events`, `/event-list`, `/calendar`)
- Crawls up to 3 levels deep for listing pages
- Extracts `eventdetail` URLs from aggregator pages
- Matches event titles to find correct event detail pages

✅ **Past Event Detection** (Lines 61-65)
- Checks if event is in the past
- Validates against URL content
- Rejects past events automatically

✅ **Program Description Detection** (Lines 70-73)
- Detects if URL is a program description (not specific event)
- Rejects program announcements

✅ **URL Content Analysis** (Lines 68-79)
- Analyzes URL content for validity
- Extracts dates from URL content
- Validates date consistency
- Rejects invalid URLs

✅ **Date Validation** (Lines 81-93)
- Checks if extracted date is in the past (more than 1 year ago)
- Allows small date differences (multi-day events, timezone issues)

✅ **URL Accessibility Check** (Lines 95-103)
- Verifies URL is accessible (HTTP status < 400)
- Rejects inaccessible URLs

✅ **Event Validation** (`_is_valid_event` method, Lines 574-660)
- Date must be in future and within 6 months
- Title validation (length, news indicators, program indicators)
- URL format validation (must be http/https, not news/article/blog)
- Local/narrow events filtering (rejects routine council meetings)
- Summary validation (rejects news/program phrases)

---

### 2. **Research Agent Phase** (`research_agent.py`)

**Applied after all events are extracted:**

✅ **Basic Relevance Check** (Lines 101-140)
- Ultra conservative mode
- Checks for clearly irrelevant topics (teacher education, language studies, biotechnology)
- Only rejects if clearly irrelevant AND no urban keywords AND no event type AND no location
- Keeps all events with urban/recovery keywords, event types, or location keywords

✅ **Duplicate Detection** (Lines 142-167)
- Checks against all existing events in database
- Fuzzy title matching (85% similarity)
- Exact date matching
- Filters out duplicates automatically

✅ **URL Validation** (Lines 168-206)
- Validates URL format (http/https)
- Checks URL accessibility
- Validates registration URLs
- Filters out events with invalid URLs

---

## ⚠️ MANUAL/SEPARATE VALIDATION (Not Automatic)

These validations are **NOT** automatically run during search. They must be run separately:

### 1. **Enhanced Relevance Validation** (`enhanced_relevance_validation.py`)

**Status:** Currently **DISABLED** in weekly cleanup (too aggressive)

**What it does:**
- Title-content matching (checks if event title matches URL content)
- Enhanced relevance checking
- URL improvement for listing pages (with max_depth=3)

**When to run:**
- Manually: `python backend/enhanced_relevance_validation.py`
- Weekly cleanup workflow (currently disabled)

**Note:** The conservative relevance checks are now integrated into the research agent, so this is less needed.

---

### 2. **Enhanced Validation Fix** (`enhanced_validation_fix.py`)

**Status:** Separate script, not automatically run

**What it does:**
- Past event detection
- Date mismatch fixing
- Program description detection
- Generic page detection and URL improvement

**When to run:**
- Manually: `python backend/enhanced_validation_fix.py`
- Not scheduled automatically

**Note:** Most of these checks are already in the LLM processor, so this is mainly for fixing existing events.

---

## 📋 SUMMARY: What Runs When

### ✅ **During Every Search (Automatic):**

1. ✅ URL improvement (listing pages → eventdetail URLs)
2. ✅ Past event detection
3. ✅ Program description detection
4. ✅ URL content analysis
5. ✅ Date validation
6. ✅ URL accessibility check
7. ✅ Event validation (`_is_valid_event`)
8. ✅ Basic relevance check (ultra conservative)
9. ✅ Duplicate detection
10. ✅ URL format/accessibility validation

### ⚠️ **Separate Scripts (Manual):**

1. ⚠️ Enhanced relevance validation (disabled - too aggressive)
2. ⚠️ Enhanced validation fix (for fixing existing events)
3. ⚠️ Cleanup existing events (weekly cleanup workflow)

---

## 🔄 RECOMMENDATION

**Current State:**
- ✅ All essential validation runs automatically during search
- ✅ Conservative validation keeps relevant events
- ✅ URL improvement happens automatically for listing pages
- ⚠️ Enhanced validation is disabled (was too aggressive)

**To Apply Enhanced Validation to New Events:**

If you want the enhanced validation (title-content matching, deeper URL following) to run automatically after each search, we can integrate it into the research agent. However, it's currently disabled because it was removing valid events.

**Current approach is working well:**
- Automatic validation during search ✅
- Conservative rules keep relevant events ✅
- URL improvement happens automatically ✅
- Weekly cleanup for existing events ✅

---

## 📝 FILES TO MODIFY

If you want to add more automatic validation:

1. **Add to research agent:** `backend/agent/research_agent.py` (after line 220)
2. **Add to LLM processor:** `backend/agent/llm_processor.py` (in `extract_events` method)


