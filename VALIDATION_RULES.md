# Complete Validation Rules Documentation

This document contains ALL validation rules currently active in the system. You can adjust these rules by modifying the corresponding files.

---

## 1. LLM EXTRACTION RULES (llm_processor.py)

### System Prompt Rules (Lines 302-383)

**MUST EXTRACT:**
- Actual events: conferences, workshops, seminars, webinars, forums, training sessions, public talks, round tables, public presentations
- Topics: urban planning, public space design, INGOs recovery programs and strategies, post-war recovery, housing policy, municipal governance, built environment professionals
- National and international events
- Major regional conferences/forums

**MUST REJECT:**
- News articles or news stories
- Blog posts or opinion pieces
- Policy announcements or program launches
- Program/initiative launches (e.g., "Compensation Program", "Housing Program")
- Research papers or publications
- General information pages
- Student projects or academic assignments
- Protests or political rallies (unless professional policy forums)
- Past events (only next 6 months)
- Non-Ukraine related events (unless international events about Ukraine)
- Government program announcements (e.g., "IDPs can submit applications")

**SCOPE FILTERING:**
- ❌ EXCLUDE: Very local/regional events (e.g., regional council meetings unless event open to participants from all the Ukraine)
- ❌ EXCLUDE: Events limited to single oblast/region (unless major conferences and open to participants from around Ukraine)
- ❌ EXCLUDE: Routine administrative meetings (рада, засідання ради, etc. unless major forum)
- ✅ INCLUDE: National and international events
- ✅ INCLUDE: Major regional conferences/forums
- ✅ INCLUDE: Specific events by NGOs and INGOs related to Urban Recovery, Public Space Design, Inclusive Design, etc.

**DATE EXTRACTION:**
- Extract EVENT DATE, not article publication date
- Look for dates after "Дата та час:", "Date:", "Event date:", "When:"
- IGNORE dates near "на читання", "reading time", "опубліковано", "published"
- For date ranges (e.g., "December 1-5"), use DATE RANGE (filter by the first date)

---

## 2. EVENT VALIDATION RULES (_is_valid_event method, llm_processor.py:574-660)

### Date Validation
- ✅ Event date must be in the future
- ✅ Event date must be within 6 months (180 days)
- ❌ Reject if date is in the past
- ❌ Reject if date is more than 6 months away

### Title Validation
- ✅ Title must exist and be at least 5 characters
- ❌ Reject if title contains news indicators: "news", "article", "blog", "report", "analysis", "opinion"
  - Exception: Allow if title also contains event indicators (e.g., "Conference News")
- ❌ Reject if title contains program indicators: "compensation program", "housing program", "program for", "applications open", "submitting applications", "can submit", "program starts"

### URL Validation
- ❌ Reject if URL contains: "/news/", "/article/", "/blog/"
- ✅ **ALLOW listing pages** (`/events`, `/event-list`, `/calendar`) - System will automatically:
  - Crawl to second level to extract event details and links
  - Follow links up to 3 levels deep for listing pages
  - Extract actual event detail URLs from listing pages
  - Match event titles to find the correct event detail page

### Local/Narrow Events Filtering
- ❌ Reject if title contains local indicators AND no major event indicators:
  - Local indicators: "засідання архітектурно", "засідання містобудівної ради", "council meeting", "рада", "обласна рада"

### Summary Validation
- ❌ Reject if summary contains news phrases: "news article", "blog post", "reports that", "according to news"
- ❌ Reject if summary contains program phrases: "can submit applications", "applications open", "program starts", "submitting applications", "access to", "compensation program", "housing program"
  - Exception: Allow if summary also contains event indicators

---

## 3. RELEVANCE VALIDATION RULES (enhanced_relevance_validation.py)

### Urban/Recovery Keywords (Lines 25-36)
**KEEP if event contains ANY of these:**
```
'urban', 'city', 'cities', 'planning', 'spatial', 'municipal', 'local government',
'recovery', 'reconstruction', 'housing', 'infrastructure', 'development',
'урбаністика', 'місто', 'планування', 'відбудова', 'житло', 'інфраструктура',
'municipality', 'governance', 'community', 'resilience', 'sustainability',
'digital', 'forum', 'capacity', 'building', 'decentralization',
'green', 'sustainable', 'waste', 'management', 'energy', 'efficiency',
'reform', 'eurointegration', 'public', 'officials', 'smart', 'building',
'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'event',
'ukraine', 'ukrainian', 'europe', 'partnership', 'cooperation',
'investment', 'finance', 'funding', 'project', 'program', 'programme', 'data'
```

### Irrelevant Keywords (Lines 39-43)
**REMOVE ONLY if event is CLEARLY about these AND has NO urban keywords AND no event type AND no location:**
```
'teacher education', 'pedagogy', 'teaching methods',  # Education (not urban)
'spanish', 'latin american', 'language studies', 'literature',  # Language studies
'biology', 'biotechnology', 'medical research', 'healthcare'  # Science/medical
```

### Relevance Check Logic (check_relevance method, Lines 134-183)

**KEEP if:**
1. Has urban/recovery keywords → ✅ ALWAYS KEEP
2. Has event type keywords: 'forum', 'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'summit' → ✅ KEEP
3. Has location keywords: 'ukraine', 'ukrainian', 'sumy', 'kyiv', 'lviv', 'kharkiv', 'odessa', 'europe' → ✅ KEEP
4. Not clearly irrelevant → ✅ KEEP (default)

**REMOVE ONLY if:**
- Clearly about irrelevant topic (teacher education, language studies, biotechnology, blockchain, cryptocurrency, fintech)
- AND has NO urban keywords
- AND has NO event type keywords
- AND has NO location keywords

### Title-Content Matching (check_title_content_match method, Lines 46-114)

**REMOVE if:**
1. Title topic doesn't match URL content topic (e.g., "urban studies" → "spanish studies")
2. Title is about urban planning but page is about irrelevant topic (spanish, latin american, arabic, islamic, teacher, education, pedagogy)
3. No title keywords found in page title/h1 AND less than 1 keyword match in content

**KEEP if:**
- Title matches content
- Network error (don't reject on errors)

---

## 4. RESEARCH AGENT FILTERING (research_agent.py:101-133)

### Basic Relevance Check (Lines 101-133)

**Reject ONLY if:**
- Clearly irrelevant topic: 'teacher education', 'pedagogy', 'spanish language', 'latin american studies', 'language studies', 'biotechnology research', 'blockchain', 'cryptocurrency', 'crypto', 'bitcoin', 'fintech', 'defi', 'nft', 'web3'
- AND has NO urban keywords
- AND has NO event type keywords
- AND has NO location keywords

**Urban Keywords (Lines 115-119):**
```
'urban', 'city', 'planning', 'recovery', 'housing', 'reconstruction', 'municipal', 
'local government', 'decentralization', 'forum', 'conference', 'digital',
'capacity', 'building', 'green', 'sustainable', 'resilience', 'infrastructure',
'workshop', 'seminar', 'webinar', 'meeting', 'ukraine', 'ukrainian', 'europe',
'partnership', 'cooperation', 'investment', 'finance', 'project', 'program', 'data'
```

**Event Types (Line 123):**
```
'forum', 'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'summit'
```

**Location Keywords (Line 127):**
```
'ukraine', 'ukrainian', 'sumy', 'kyiv', 'lviv', 'kharkiv', 'odessa', 'europe'
```

---

## 5. ENHANCED VALIDATION FIX RULES (enhanced_validation_fix.py)

### Past Event Detection (Lines 54-61)
- ❌ Remove if event is in the past (checked via DateValidator)

### Date Mismatch (Lines 66-88)
- ❌ Remove if extracted date from URL is in the past
- ⚠️ Update date if extracted date is 1 year different but more recent
- ❌ Remove if extracted date is in past year

### Program Description Detection (Lines 90-96)
- ❌ Remove if URL is a program description (not specific event) AND no date extracted

### Generic Page Detection (Lines 98-112)
- ⚠️ Try to find better URL (follow links up to 3 levels)
- ❌ Remove if generic page AND no better URL found

### Date Validation After URL Fix (Lines 126-150)
- ❌ Remove if extracted date is in the past
- ❌ Remove if extracted date is in past year
- ⚠️ Warn if date is more than 1 year in future (but keep)

---

## 6. DATE VALIDATION RULES (date_validator.py)

### Past Event Detection
- Checks URL content for past event indicators:
  - "was held", "took place", "вже відбулося", "already happened"
  - Past years in event context (e.g., "2023", "2024")
  - "from X to Y 2023" patterns

---

## 7. URL VALIDATION RULES (url_validator.py, url_follower.py)

### URL Format Validation
- ✅ Must start with `http://` or `https://`
- ✅ Must be accessible (HTTP status < 400)

### URL Following (url_follower.py)
- **For listing pages** (`/events`, `/event-list`, `/calendar`):
  - Automatically crawls to **second level** to extract event details
  - Follows links up to **3 levels deep** (increased from 2 for listing pages)
  - Extracts all event links from listing page
  - Follows each link to find event detail pages
  - Matches event titles to find the correct event detail URL
  - Prioritizes `eventdetail` URLs
- **For other aggregator pages**: Follows up to 2 levels deep
- Detects generic pages: `/home`, `/contact`, `/about`, `/events?`, `/event-list`, `/calendar`

---

## 8. SMART EVENT VERIFICATION & CORRECTION SYSTEM v2.0 (smart_event_corrector.py)

### Overview
The smart corrector doesn't just remove problematic events - it **attempts to fix them first**.

### Verification Flow
```
Event Found → Is URL Working?
    ├── YES → Is it specific event page?
    │         ├── YES → Verify date → KEEP/UPDATE
    │         └── NO  → Deep crawl (3 levels)
    │                   ├── Found → KEEP/UPDATE
    │                   └── Not found → Tavily re-search
    └── NO  → Multi-query Tavily search
              ├── Found alternative → Verify & UPDATE
              └── Not found → Check if date is future
                              ├── Future → KEEP (with URL issues flag)
                              └── Past → REMOVE
```

### Features

**✅ Multi-Query Tavily Search:**
- Searches: `"{title}" event registration 2025`
- Searches: `"{title}" conference official site`
- Searches: `{organizer} "{title}" 2025`
- Searches: `"{title}" {month} 2025`
- Filters out spam sites automatically

**✅ Deep Crawling (3 levels):**
- Extracts and scores all links from listing pages
- Follows top 5 candidate links
- Goes 3 levels deep to find specific event pages
- Matches event title words to verify correct page

**✅ Date Extraction with Confidence Scoring:**
```
Source                          Confidence
─────────────────────────────────────────
"Дата та час:" marker           95%
"Event date:" marker            95%
"When:" / "Коли:" marker        90%
Date with time (e.g., "об 11:00") 85%
Date near title keywords         70%
Any date on page                 40%
```

**✅ Social Media Fallback:**
- Detects Facebook/Instagram URLs (often HTTP 400)
- Searches for alternative sources automatically
- Can exclude social media from re-search results

**✅ Keeps Future Events:**
- Events with future dates are kept even if URL has issues
- Only removes if date confirms event is past

### What Gets Corrected (Not Removed)

| Issue | Action |
|-------|--------|
| Generic/listing URL | Find specific event URL via crawling or Tavily |
| Broken URL (404) | Search for alternative URL |
| Social media URL (400) | Find non-social media source |
| Wrong date (extracted future) | Update to correct date |
| Spam site URL | Find legitimate event URL |

### What Gets Removed

| Condition | Reason |
|-----------|--------|
| URL broken AND no alternative found AND date is past | Unfixable + past |
| High confidence extracted date is past AND stored is future | Event already happened |
| All correction attempts failed AND date is past | Truly unfixable |

### Integration
- **Daily Workflow**: Runs after research to verify new events
- **Weekly Cleanup**: Full database verification

---

## SUMMARY: What Gets Removed?

An event is REMOVED **only after correction attempts fail** if it meets ALL of these conditions:
1. ❌ URL not accessible AND no alternative found via Tavily
2. ❌ Date is in the past (confirmed)

**OR if:**
- Clearly about irrelevant topic AND has NO urban/recovery keywords
- News article
- Very local routine meeting (not major forum/conference)
- Title doesn't match URL content (clear mismatch)
- High-confidence extracted date is past but stored date is future (event already happened)

---

## FILES TO MODIFY

To adjust these rules, edit these files:

| File | What It Does |
|------|--------------|
| `backend/smart_event_corrector.py` | Main verification & correction logic |
| `backend/agent/llm_processor.py` (lines 302-383, 574-660) | LLM extraction rules |
| `backend/agent/research_agent.py` (lines 101-133) | Research agent filtering |
| `backend/enhanced_relevance_validation.py` (lines 24-183) | Relevance validation |

---

## SYSTEM CAPABILITIES & LIMITATIONS

### ✅ What's Possible

| Capability | How |
|------------|-----|
| Re-search for URLs | Tavily multi-query search |
| Crawl deeper (3 levels) | Link extraction & scoring |
| Extract event dates | Regex with confidence scoring |
| Social media fallback | Find alternative sources |
| Date correction | Auto-update based on page content |
| Keep future events | Preserve even with URL issues |

### ❌ Current Limitations

| Limitation | Reason |
|------------|--------|
| Login-protected pages | Facebook/Instagram return 400 |
| Geo-restricted sites | Some .eu sites return 403 |
| PDF event details | No PDF parsing |
| Image-based dates | No OCR |
| JavaScript-rendered | No headless browser |

---

## RECOMMENDATIONS FOR FURTHER IMPROVEMENT

1. **Add headless browser** (Playwright) for JavaScript-rendered sites
2. **Add PDF parsing** for event PDFs
3. **Add OCR** for image-based dates
4. **Add VPN rotation** for geo-restricted sites
5. **Add alternative URL database** for social media events

