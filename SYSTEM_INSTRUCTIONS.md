# Urban Planning Event Intelligence System - Complete Instructions

## For Future AI Assistants and Developers

This document contains everything needed to understand, maintain, and fix this system.

---

## 1. SYSTEM OVERVIEW

### Purpose
A web application that automatically discovers and displays urban planning, recovery, and housing events in Ukraine.

### Tech Stack
- **Frontend**: Next.js (React) deployed on Vercel
- **Backend**: Python scripts (research agent, validators)
- **Database**: Supabase (PostgreSQL)
- **APIs**: 
  - Tavily (web search)
  - OpenAI GPT-4o-mini (event extraction, translation)
- **Automation**: GitHub Actions (daily research, weekly cleanup)

### Key Files
```
frontend/
  app/page.tsx          - Main UI component
  lib/supabase.ts       - Database client

backend/
  agent/
    research_agent.py   - Main workflow orchestrator
    llm_processor.py    - LLM extraction & validation (MOST IMPORTANT)
    search.py           - Tavily search queries
    duplicate_detector.py - Duplicate filtering
    translator.py       - Ukrainian → English translation
    url_validator.py    - URL accessibility checks
    url_follower.py     - Deep link crawling
    url_content_analyzer.py - Date extraction from pages
  
  smart_event_corrector.py - Verification & auto-fix system
  validate_all_events.py   - Manual validation script
  
.github/workflows/
  daily-research.yml    - Runs at 2:00 AM UTC daily
  weekly-cleanup.yml    - Runs Sundays at 3:00 AM UTC
```

---

## 2. API KEYS & CONFIGURATION

### Environment Variables Required
```bash
SUPABASE_URL=https://qjuaqnhwpwmywgshghpq.supabase.co
SUPABASE_KEY=<service_role_key>  # For backend operations
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key>  # For frontend
OPENAI_API_KEY=<key>
TAVILY_API_KEY=<key>
```

### GitHub Secrets (for Actions)
- `SUPABASE_URL`
- `SUPABASE_KEY` (service role)
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

### Supabase Service Role Key (for full database access)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDI0MjkyNywiZXhwIjoyMDc5ODE4OTI3fQ.I7F3X8wHTieUL4evoCiFPPYSD2-ryIbtVcD44Nh32L8
```

---

## 3. COMMON ISSUES & SOLUTIONS

### Issue: Events not translated to English
**Location**: `backend/agent/research_agent.py` (lines ~150-165)
**Solution**: The research agent should translate after LLM extraction:
```python
# Translate all fields
for event in all_events:
    if self.translator.is_ukrainian(event.event_title):
        event.event_title = self.translator.translate(event.event_title, "event title")
    if event.organizer and self.translator.is_ukrainian(event.organizer):
        event.organizer = self.translator.translate(event.organizer, "organizer name")
    if event.summary and self.translator.is_ukrainian(event.summary):
        event.summary = self.translator.translate(event.summary, "event description")
```

### Issue: Spam conference sites appearing
**Location**: `backend/agent/llm_processor.py` (lines ~630-645)
**Blocked sites list**:
```python
spam_aggregators = [
    'conferencealerts.co.in',
    'allconferencealert.net',
    'internationalconferencealerts.com',
    'conferencealert.com',
    'conferencealerts.com',
    'waset.org',
    'conferenceineurope.org',
    'conferenceseries.com',
    '10times.com',
    'eventbrite.com/d/',
]
```

### Issue: Listing pages instead of specific event URLs
**Location**: `backend/agent/llm_processor.py` (lines ~654-675)
**Rejected patterns**:
```python
listing_patterns = [
    '/all-events',
    '/category/',
    '/news/',
    '/naukovi-konferenciyi/',
    '/upcoming-events',
    '/event-list',
    '/events/',
]
```

### Issue: Duplicate events appearing
**Solution**: Run duplicate detection with URL-based check:
```python
# In duplicate_detector.py - find_duplicates method
# Checks both URL exact match AND title similarity
```

### Issue: Past events showing on main page
**Location**: `frontend/app/page.tsx` (lines ~52-77)
**Solution**: Server-side date filtering is implemented:
```typescript
// Only fetch events from today onwards
if (!includePastEvents) {
    query = query.gte('event_date', todayStr)
}
```
- "Show Past Events" button reveals historical events
- Past events are NOT deleted, just hidden by default

---

## 4. DATABASE CLEANUP COMMANDS

### Delete all events (fresh start)
```python
import requests
SUPABASE_URL = "https://qjuaqnhwpwmywgshghpq.supabase.co"
SUPABASE_KEY = "<service_role_key>"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=neq.0", headers=headers)
```

### Delete specific event by ID
```python
requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=eq.{event_id}", headers=headers)
```

### Translate all Ukrainian titles
```python
# Run: python3 backend/cleanup_and_translate.py
# Or use the code from smart_event_corrector.py
```

### Full validation & cleanup
```bash
cd backend
export SUPABASE_URL="..."
export SUPABASE_KEY="..."
export TAVILY_API_KEY="..."
python3 smart_event_corrector.py
```

---

## 5. WORKFLOW: How Search Works

```
1. SEARCH (Tavily)
   └─> Search queries from search.py
   └─> Returns ~10 results per query
   └─> ~15 queries = ~150 results

2. LLM EXTRACTION (OpenAI)
   └─> llm_processor.py extracts structured events
   └─> Validates: date, URL, relevance
   └─> Rejects: spam, listing pages, past events

3. TRANSLATION
   └─> Ukrainian titles/organizers/summaries → English

4. DUPLICATE DETECTION
   └─> URL exact match
   └─> Title similarity (85% threshold)

5. URL VALIDATION
   └─> Check accessibility (HTTP status)
   └─> Skip inaccessible URLs

6. SAVE TO DATABASE
   └─> Upsert events to Supabase

7. SMART CORRECTOR (Post-processing)
   └─> Verify all saved events
   └─> Fix URLs via Tavily re-search if needed
   └─> Correct dates based on page content
   └─> Remove truly unfixable events
```

---

## 6. VALIDATION RULES SUMMARY

### KEEP Events If:
- Has urban/recovery keywords: urban, city, planning, recovery, housing, reconstruction, municipal, forum, conference, workshop, ukraine
- Has event type: forum, conference, workshop, seminar, webinar, meeting, summit
- Has location: ukraine, kyiv, lviv, kharkiv, europe

### REJECT Events If:
- From spam sites (see blocked list above)
- URL is listing page (ends with /events, /category/, etc.)
- **URL is news article** (has date pattern like /2025/09/17/, or from news sites)
- Clearly irrelevant: teacher education, biotechnology, AI/ML, language studies, blockchain, cryptocurrency, fintech
- Date is past OR more than 6 months in future
- Title contains news indicators without event keywords

### News Sites Blocklist:
```
kyivindependent.com, pravda.com.ua, ukrinform.ua, unian.ua,
korrespondent.net, thepeninsulaqatar.com, zygonjournal.org,
hmarochos.kiev.ua
```

### URL RULES:
- REJECT: homepages (just domain/)
- REJECT: listing pages (/events, /all-events, /category/)
- REJECT: news articles (/news/, /article/, /blog/)
- ALLOW: specific event pages (eventdetail/123, /event/name)

---

## 7. RUNNING MANUAL OPERATIONS

### Run full research manually
```bash
cd backend
export SUPABASE_URL="https://qjuaqnhwpwmywgshghpq.supabase.co"
export SUPABASE_KEY="<service_role_key>"
export OPENAI_API_KEY="<key>"
export TAVILY_API_KEY="<key>"
python3 -m agent.research_agent
```

### Run smart corrector only
```bash
python3 smart_event_corrector.py
```

### Run validation check (no changes)
```bash
python3 validate_all_events.py
```

---

## 8. FRONTEND BEHAVIOR

### Main Page (`/`)
- Shows ONLY upcoming events (today onwards) by default
- "Show Past Events" button reveals all events
- Filter by category: All, Legislation, Housing, Recovery, General
- "Run Research Now" button triggers GitHub Actions

### Event Display
- Date & Time
- Event Title (clickable link)
- Organizer
- Target Audience
- Category (badge)
- Description/Summary
- Register link

---

## 9. GITHUB ACTIONS

### Daily Research (`daily-research.yml`)
- Runs: 2:00 AM UTC daily
- Steps: Install → Research → Smart Correct
- Can be triggered manually from Actions tab

### Weekly Cleanup (`weekly-cleanup.yml`)
- Runs: Sundays 3:00 AM UTC
- Steps: Install → Smart Correct → Additional cleanup

---

## 10. TROUBLESHOOTING CHECKLIST

When events have issues, check in this order:

1. **Ukrainian titles?** → Run translator
2. **Spam site URLs?** → Add to blocklist in `llm_processor.py`
3. **Listing page URLs?** → Add pattern to rejection list
4. **Duplicates?** → Check `duplicate_detector.py` is running
5. **Past events showing?** → Check frontend date filter
6. **Wrong dates?** → Check `url_content_analyzer.py` date extraction
7. **Events not saving?** → Check Supabase connection & RLS policies

---

## 11. QUICK FIX SCRIPTS

### Fix all current issues at once
```python
import requests
import os
from openai import OpenAI

SUPABASE_URL = "https://qjuaqnhwpwmywgshghpq.supabase.co"
SUPABASE_KEY = "<service_role_key>"
OPENAI_API_KEY = "<key>"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Get all events
events = requests.get(f"{SUPABASE_URL}/rest/v1/events?select=*", headers=headers).json()

# Spam sites to delete
spam = ['conferencealerts', 'conferenceineurope', 'waset.org', 'allconferencealert']

# Listing patterns to delete
listings = ['/all-events', '/category/', '/news/', '/events/']

client = OpenAI(api_key=OPENAI_API_KEY)
ukr_chars = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'

for e in events:
    url = e['url'].lower()
    title = e['event_title']
    
    # Delete spam
    if any(s in url for s in spam):
        requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=eq.{e['id']}", headers=headers)
        print(f"Deleted spam: {title[:40]}")
        continue
    
    # Delete listing pages
    if any(p in url for p in listings):
        requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=eq.{e['id']}", headers=headers)
        print(f"Deleted listing: {title[:40]}")
        continue
    
    # Translate Ukrainian
    if any(c in title.lower() for c in ukr_chars):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Translate Ukrainian to English concisely."},
                {"role": "user", "content": f"Translate: {title}"}
            ]
        )
        new_title = resp.choices[0].message.content.strip()
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/events?id=eq.{e['id']}",
            headers=headers,
            json={"event_title": new_title}
        )
        print(f"Translated: {title[:30]} → {new_title[:30]}")

print("Done!")
```

---

## 12. CONTACT & RESOURCES

- **GitHub Repo**: Check repository settings for secrets
- **Supabase Dashboard**: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq
- **Vercel Dashboard**: Check deployments and environment variables
- **Tavily Dashboard**: Check API usage and credits

---

## 13. VERSION HISTORY

### December 2025 Fixes
1. Added `conferenceineurope.org` to spam blocklist
2. Added stricter listing page URL rejection
3. Fixed translation to run on all events automatically
4. Integrated smart corrector into research workflow
5. Added URL-based duplicate detection
6. Fixed past events filtering (hidden by default, shown via button)

---

## 14. IMPORTANT NOTES FOR AI ASSISTANTS

1. **Always use service role key** for database operations (anon key has limited permissions)
2. **Don't delete past events** - they should be hidden, not removed
3. **Check llm_processor.py first** - most validation happens there
4. **Test with 2-3 search queries** to save API credits
5. **Smart corrector is the safety net** - it runs after every search
6. **Translation happens in research_agent.py** after LLM extraction
7. **Duplicate detection uses both URL and title similarity**

---

*Last updated: December 3, 2025*

