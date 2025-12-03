"""
Final cleanup script - runs after research agent.
Ensures all events are translated and no duplicates remain.
"""
import os
import sys
import re
import requests
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Spam sites blocklist
SPAM_SITES = [
    'conferencealerts', 'allconferencealert', 'internationalconferencealerts',
    'conferenceineurope', 'waset.org', '10times.com', 'eventbrite.com/d/',
    'competitioncorner.net', 'wordreference.com', 'addtoany.com', 'espconferences.org',
    'conferenceseries.com'
]

# News sites blocklist (not event pages)
NEWS_SITES = [
    'kyivindependent.com', 'pravda.com.ua', 'ukrinform.ua', 'unian.ua',
    'korrespondent.net', 'thepeninsulaqatar.com', 'zygonjournal.org',
    'hmarochos.kiev.ua', 'misto.media', 'archi.ru'
]

# Listing page patterns
LISTING_PATTERNS = [
    '/all-events', '/category/', '/news/', '/events/', '/upcoming-events',
    'naukovi-konferenciyi', '/event-list', '/article/', '/articles/', '/blog/',
    '/newsroom/', '/past-events', '/archive/'
]

# Legitimate event URL domains (whitelist)
LEGITIMATE_EVENT_URLS = [
    'facebook.com', 'instagram.com/p/', 'jotform.com', 'rada.gov.ua',
    'irf.ua', 'cfr.org/event', 'fes.de', 'gov.ua', 'dpu.edu.ua',
    'dilovamova.com', 'ubc.net', 'usubc.org', 'msb.se'
]

# Semantic duplicate mappings (Ukrainian -> English)
SEMANTIC_MAPPINGS = {
    'енергоефективності': ['energy efficiency', 'energy saving'],
    'енергоменеджер': ['energy manager', 'energy management'],
    'відбудова': ['recovery', 'reconstruction', 'rebuild'],
    'форум': ['forum'],
    'конференція': ['conference'],
    'деокуповані': ['de-occupied', 'liberated'],
    'громад': ['communities', 'community'],
    'тиждень': ['week'],
}

# Allowed cities for local events (UN-Habitat recovery focus)
ALLOWED_CITIES = [
    'stryi', 'стрий', 'makariv', 'макарів', 'borodianka', 'бородянка',
    'drohobych', 'дрогобич', 'irpin', 'ірпінь', 'truskavets', 'трускавець',
    'opishnia', 'опішня', 'myrhorod', 'миргород',
    'kyiv', 'київ', 'lviv', 'львів', 'kharkiv', 'харків', 'odesa', 'одеса', 'dnipro', 'дніпро'
]

# Local cities to exclude
LOCAL_CITIES_TO_EXCLUDE = [
    'khmelnytskyi', 'хмельниц', 'sumy', 'сум', 'chernihiv', 'черніг',
    'zhytomyr', 'житомир', 'rivne', 'рівн', 'lutsk', 'луцьк',
    'ternopil', 'терноп', 'ivano-frankivsk', 'івано-франків', 'uzhhorod', 'ужгород',
    'chernivtsi', 'чернівц', 'vinnytsia', 'вінниц', 'poltava', 'полтав',
    'kherson', 'херсон', 'zaporizhzhia', 'запоріж', 'mykolaiv', 'миколаїв',
    'kropyvnytskyi', 'кропивниц'
]

UKR_CHARS = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'


def is_ukrainian(text: str) -> bool:
    """Check if text contains Ukrainian characters."""
    return any(c in text.lower() for c in UKR_CHARS) if text else False


def translate(client: OpenAI, text: str, context: str = "event title") -> str:
    """Translate Ukrainian text to English."""
    if not text or not is_ukrainian(text):
        return text
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate this {context} from Ukrainian to English. Return only the translation."},
                {"role": "user", "content": text}
            ],
            max_tokens=300
        )
        return resp.choices[0].message.content.strip().strip('"\'')
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def is_spam_url(url: str) -> bool:
    """Check if URL is from a spam site."""
    url_lower = url.lower()
    return any(s in url_lower for s in SPAM_SITES)


def is_news_article(url: str) -> bool:
    """Check if URL is a news article (not an event page)."""
    url_lower = url.lower()
    
    # Check if from whitelisted event domains
    if any(d in url_lower for d in LEGITIMATE_EVENT_URLS):
        return False
    
    # Check if from news sites
    if any(s in url_lower for s in NEWS_SITES):
        return True
    
    # Check for date pattern in URL (e.g., /2025/09/17/)
    date_pattern = re.search(r'/\d{4}/\d{2}/\d{2}/', url)
    if date_pattern:
        return True
    
    return False


def is_listing_page(url: str) -> bool:
    """Check if URL is a listing page (not a specific event)."""
    url_lower = url.lower()
    if any(p in url_lower for p in LISTING_PATTERNS):
        # Allow if has specific event ID
        if 'eventdetail' in url_lower or 'eventid' in url_lower:
            return False
        return True
    return False


def is_local_event(title: str, organizer: str) -> bool:
    """Check if event is a local event from excluded cities."""
    combined = f"{title} {organizer or ''}".lower()
    
    # Check if from excluded local city
    is_local = any(city in combined for city in LOCAL_CITIES_TO_EXCLUDE)
    
    # Check if from allowed city
    is_allowed = any(city in combined for city in ALLOWED_CITIES)
    
    # Check if national/international (always allowed)
    national_indicators = ['national', 'international', 'all-ukrainian', 'всеукраїн', 
                           'ukraine', 'україн', 'european', 'європ']
    is_national = any(ind in combined for ind in national_indicators)
    
    # Reject if local and not allowed and not national
    return is_local and not is_allowed and not is_national


def has_past_year_in_title(title: str) -> bool:
    """Check if title contains a past year (indicates past event)."""
    from datetime import datetime
    current_year = datetime.now().year
    
    # Find years in title like "2024", "2023", etc.
    years_in_title = re.findall(r'\b(20\d{2})\b', title)
    for year_str in years_in_title:
        year = int(year_str)
        if year < current_year:
            return True
    return False


def is_semantic_duplicate(title1: str, title2: str, date1: str, date2: str) -> bool:
    """Check if two events are semantic duplicates (same event in different languages)."""
    # Must be same date
    if date1 != date2:
        return False
    
    t1_lower = title1.lower()
    t2_lower = title2.lower()
    
    # Check if one has Ukrainian and other doesn't
    t1_ukr = is_ukrainian(title1)
    t2_ukr = is_ukrainian(title2)
    
    if t1_ukr == t2_ukr:
        return False
    
    ukr_title = t1_lower if t1_ukr else t2_lower
    eng_title = t2_lower if t1_ukr else t1_lower
    
    matches = 0
    for ukr_word, eng_equivalents in SEMANTIC_MAPPINGS.items():
        if ukr_word in ukr_title:
            if any(eng in eng_title for eng in eng_equivalents):
                matches += 1
    
    return matches >= 2


def main():
    print("=" * 60)
    print("FINAL CLEANUP - Translate & Remove Duplicates")
    print("=" * 60)
    
    if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
        print("ERROR: Missing environment variables")
        return
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Fetch all events
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=*&order=event_date",
        headers=HEADERS
    )
    events = response.json()
    print(f"Total events: {len(events)}")
    
    # STEP 1: Remove spam URLs, news articles, listing pages, local events, and past year events
    print("\nStep 1: Removing problematic events...")
    removed = 0
    for e in events[:]:  # Copy list for safe removal
        url = e['url']
        title = e['event_title']
        reason = None
        
        if is_spam_url(url):
            reason = "spam URL"
        elif is_news_article(url):
            reason = "news article URL"
        elif is_listing_page(url):
            reason = "listing page URL"
        elif is_local_event(title, e.get('organizer', '')):
            reason = "local event (not from allowed cities)"
        elif has_past_year_in_title(title):
            reason = "past year in title (past event)"
        
        if reason:
            print(f"  🗑️ Removing ({reason}): {title[:40]}...")
            requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=eq.{e['id']}", headers=HEADERS)
            events.remove(e)
            removed += 1
    print(f"  Removed {removed} problematic events")
    
    # STEP 2: Translate all Ukrainian content
    print("\nStep 2: Translating Ukrainian content...")
    translated = 0
    for e in events:
        updates = {}
        
        if is_ukrainian(e['event_title']):
            updates['event_title'] = translate(client, e['event_title'], "event title")
            print(f"  ✅ Title: {e['event_title'][:30]}... → {updates['event_title'][:30]}...")
        
        if e.get('organizer') and is_ukrainian(e['organizer']):
            updates['organizer'] = translate(client, e['organizer'], "organization name")
        
        if e.get('summary') and is_ukrainian(e['summary']):
            updates['summary'] = translate(client, e['summary'], "event description")
        
        if updates:
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{e['id']}",
                headers=HEADERS,
                json=updates
            )
            # Update local copy
            e.update(updates)
            translated += 1
    
    print(f"  Translated {translated} events")
    
    # STEP 3: Remove semantic duplicates (prefer English version)
    print("\nStep 3: Removing semantic duplicates...")
    to_remove = set()
    
    for i, e1 in enumerate(events):
        if e1['id'] in to_remove:
            continue
        for e2 in events[i+1:]:
            if e2['id'] in to_remove:
                continue
            
            if is_semantic_duplicate(e1['event_title'], e2['event_title'], 
                                    e1['event_date'], e2['event_date']):
                # Remove Ukrainian version
                if is_ukrainian(e1['event_title']):
                    to_remove.add(e1['id'])
                    print(f"  🗑️ Duplicate: {e1['event_title'][:40]}...")
                else:
                    to_remove.add(e2['id'])
                    print(f"  🗑️ Duplicate: {e2['event_title'][:40]}...")
    
    for eid in to_remove:
        requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=eq.{eid}", headers=HEADERS)
    
    print(f"  Removed {len(to_remove)} semantic duplicates")
    
    # STEP 4: Remove exact title duplicates on same date
    print("\nStep 4: Removing exact duplicates...")
    seen = {}
    exact_dups = 0
    
    for e in events:
        if e['id'] in to_remove:
            continue
        key = (e['event_title'].lower()[:50], e['event_date'])
        if key in seen:
            print(f"  🗑️ Exact dup: {e['event_title'][:40]}...")
            requests.delete(f"{SUPABASE_URL}/rest/v1/events?id=eq.{e['id']}", headers=HEADERS)
            exact_dups += 1
        else:
            seen[key] = e['id']
    
    print(f"  Removed {exact_dups} exact duplicates")
    
    # Final count
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=id&order=event_date",
        headers=HEADERS
    )
    final_count = len(response.json())
    
    print("\n" + "=" * 60)
    print(f"FINAL CLEANUP COMPLETE")
    print(f"Events remaining: {final_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()

