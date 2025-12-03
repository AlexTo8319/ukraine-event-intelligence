"""Supabase database client for event storage."""
import os
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Ukrainian/Cyrillic characters for detection (includes all Cyrillic that might appear)
_UKR_CHARS = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ'
# Also check for Cyrillic letters that look like Latin (а, е, і, о, р, с, у, х)
_CYRILLIC_LOOKALIKES = 'аеіорсухАЕІОРСУХ'

def _is_ukrainian(text: str) -> bool:
    """Check if text contains Ukrainian/Cyrillic characters."""
    if not text:
        return False
    # Check for obvious Ukrainian
    if any(c in text for c in _UKR_CHARS):
        return True
    # Check for Cyrillic lookalikes by comparing char codes
    for c in text:
        # Cyrillic range: 0x0400-0x04FF
        if 0x0400 <= ord(c) <= 0x04FF:
            return True
    return False

def _translate_text(text: str, context: str = "text") -> str:
    """Translate Ukrainian text to English using OpenAI."""
    if not text or not _is_ukrainian(text):
        return text
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(f"  ⚠️ OPENAI_API_KEY not set - cannot translate: {text[:30]}...")
        return text
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate this {context} from Ukrainian to English. Return ONLY the translation, no quotes or explanations."},
                {"role": "user", "content": text}
            ],
            max_tokens=300,
            temperature=0.3
        )
        result = resp.choices[0].message.content.strip().strip('"\'')
        print(f"  🔄 DB Translated: {text[:25]}... → {result[:25]}...")
        return result
    except Exception as e:
        print(f"  ⚠️ Translation error: {str(e)[:50]}")
        return text


import re

# Spam/invalid URL patterns
_SPAM_SITES = [
    'conferencealerts', 'allconferencealert', 'internationalconferencealerts',
    'waset.org', '10times.com', 'conferenceineurope', 'conferenceseries',
    'competitioncorner.net', 'wordreference.com', 'addtoany.com', 'espconferences.org'
]

_NEWS_SITES = [
    'kyivindependent.com', 'pravda.com.ua', 'ukrinform.ua', 'unian.ua',
    'korrespondent.net', 'thepeninsulaqatar.com', 'zygonjournal.org',
    'hmarochos.kiev.ua', 'misto.media', 'archi.ru'
]

_LISTING_PATTERNS = [
    '/all-events', '/category/', '/news/', '/events/', '/newsroom/',
    '/past-events', '/archive/', '/event-list', '/upcoming-events'
]

# Allowed cities for local events (UN-Habitat recovery focus)
_ALLOWED_CITIES = [
    'stryi', 'стрий', 'makariv', 'макарів', 'borodianka', 'бородянка',
    'drohobych', 'дрогобич', 'irpin', 'ірпінь', 'truskavets', 'трускавець',
    'opishnia', 'опішня', 'myrhorod', 'миргород',
    'kyiv', 'київ', 'lviv', 'львів', 'kharkiv', 'харків', 'odesa', 'одеса', 'dnipro', 'дніпро'
]

# Local cities to exclude (unless national/international event)
_LOCAL_CITIES_TO_EXCLUDE = [
    'khmelnytskyi', 'хмельниц', 'sumy', 'сум', 'chernihiv', 'черніг',
    'zhytomyr', 'житомир', 'rivne', 'рівн', 'lutsk', 'луцьк',
    'ternopil', 'терноп', 'ivano-frankivsk', 'івано-франків', 'uzhhorod', 'ужгород',
    'chernivtsi', 'чернівц', 'vinnytsia', 'вінниц', 'poltava', 'полтав',
    'kherson', 'херсон', 'zaporizhzhia', 'запоріж', 'mykolaiv', 'миколаїв',
    'kropyvnytskyi', 'кропивниц'
]

def _is_local_event(title: str, organizer: str) -> bool:
    """Check if event is a local event from excluded cities."""
    combined = f"{title} {organizer or ''}".lower()
    
    # Check if from excluded local city
    is_local = any(city in combined for city in _LOCAL_CITIES_TO_EXCLUDE)
    
    # Check if from allowed city
    is_allowed = any(city in combined for city in _ALLOWED_CITIES)
    
    # Check if national/international (always allowed)
    national_indicators = ['national', 'international', 'all-ukrainian', 'всеукраїн', 
                           'ukraine', 'україн', 'european', 'європ']
    is_national = any(ind in combined for ind in national_indicators)
    
    # Reject if local and not allowed and not national
    return is_local and not is_allowed and not is_national

def _has_past_year_in_title(title: str) -> bool:
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

def _is_valid_url(url: str) -> tuple:
    """
    Check if URL is valid for an event page.
    Returns (is_valid, reason)
    """
    if not url:
        return False, "No URL provided"
    
    url_lower = url.lower()
    
    # Check spam sites
    for spam in _SPAM_SITES:
        if spam in url_lower:
            return False, f"Spam site: {spam}"
    
    # Check news sites
    for news in _NEWS_SITES:
        if news in url_lower:
            return False, f"News site: {news}"
    
    # Check for date pattern in URL (news articles)
    if re.search(r'/\d{4}/\d{2}/\d{2}/', url):
        # Whitelist legitimate event domains
        whitelist = ['facebook.com', 'instagram.com', 'gov.ua', 'irf.ua', 'rada.gov.ua']
        if not any(w in url_lower for w in whitelist):
            return False, "News article URL (date pattern)"
    
    # Check listing patterns
    for pattern in _LISTING_PATTERNS:
        if pattern in url_lower:
            # Allow if has event ID
            if 'eventdetail' in url_lower or 'eventid' in url_lower:
                continue
            return False, f"Listing page: {pattern}"
    
    return True, "OK"


class DatabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.table_name = "events"
    
    def _force_translate(self, event_data: dict) -> dict:
        """MANDATORY translation of all Ukrainian text before saving."""
        # Translate title
        if _is_ukrainian(event_data.get('event_title', '')):
            event_data['event_title'] = _translate_text(event_data['event_title'], "event title")
        
        # Translate organizer
        if _is_ukrainian(event_data.get('organizer', '')):
            event_data['organizer'] = _translate_text(event_data['organizer'], "organization name")
        
        # Translate summary
        if _is_ukrainian(event_data.get('summary', '')):
            event_data['summary'] = _translate_text(event_data['summary'], "event description")
        
        return event_data
    
    def upsert_event(self, event_data: dict) -> dict:
        """
        Insert or update an event based on URL (unique identifier).
        ALWAYS validates URL and translates Ukrainian content before saving.
        
        Args:
            event_data: Dictionary containing event fields
            
        Returns:
            The inserted/updated event record, or None if URL is invalid
        """
        # MANDATORY: Validate URL before saving
        url = event_data.get('url', '')
        is_valid, reason = _is_valid_url(url)
        if not is_valid:
            print(f"  ❌ DB Rejected invalid URL: {reason} - {url[:50]}...")
            return None
        
        # MANDATORY: Check for local events from excluded cities
        title = event_data.get('event_title', '')
        organizer = event_data.get('organizer', '')
        if _is_local_event(title, organizer):
            print(f"  ❌ DB Rejected local event: {title[:40]}...")
            return None
        
        # MANDATORY: Check for past year in title (indicates past event)
        if _has_past_year_in_title(title):
            print(f"  ❌ DB Rejected past year in title: {title[:40]}...")
            return None
        
        # MANDATORY: Translate before saving
        event_data = self._force_translate(event_data)
        
        # Check if event with this URL already exists
        existing = self.client.table(self.table_name)\
            .select("id, url")\
            .eq("url", event_data["url"])\
            .execute()
        
        if existing.data:
            # Update existing event
            event_id = existing.data[0]["id"]
            result = self.client.table(self.table_name)\
                .update(event_data)\
                .eq("id", event_id)\
                .execute()
            return result.data[0] if result.data else None
        else:
            # Insert new event
            result = self.client.table(self.table_name)\
                .insert(event_data)\
                .execute()
            return result.data[0] if result.data else None
    
    def get_events(self, limit: int = 100, category: Optional[str] = None) -> List[dict]:
        """
        Retrieve events from database.
        
        Args:
            limit: Maximum number of events to return
            category: Optional category filter
            
        Returns:
            List of event records
        """
        query = self.client.table(self.table_name)\
            .select("*")\
            .order("event_date", desc=False)\
            .limit(limit)
        
        if category:
            query = query.eq("category", category)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_all_events(self, limit: int = 2000) -> List[dict]:
        """
        Retrieve all events from database (including past events).
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of all event records
        """
        query = self.client.table(self.table_name)\
            .select("*")\
            .order("event_date", desc=False)\
            .limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_upcoming_events(self, days: int = 180) -> List[dict]:  # Default: 6 months
        """
        Get events in the next N days.
        
        Args:
            days: Number of days to look ahead
        
        Returns:
            List of upcoming event records
        """
        from datetime import date, timedelta
        today = date.today()
        future_date = today + timedelta(days=days)
        
        result = self.client.table(self.table_name)\
            .select("*")\
            .gte("event_date", today.isoformat())\
            .lte("event_date", future_date.isoformat())\
            .order("event_date", desc=False)\
            .execute()
        
        return result.data if result.data else []
    
    def get_all_events_for_duplicate_check(self, limit: int = 500) -> List[dict]:
        """
        Get all events for duplicate checking (includes past events for comparison).
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            List of event records with title and date
        """
        result = self.client.table(self.table_name)\
            .select("event_title, event_date")\
            .order("event_date", desc=False)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []
    
    def delete_event(self, event_id: int) -> bool:
        """
        Delete an event by its ID.
        
        Args:
            event_id: The ID of the event to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            self.client.table(self.table_name)\
                .delete()\
                .eq("id", event_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    def delete_event_by_url(self, url: str) -> bool:
        """
        Delete an event by its URL.
        
        Args:
            url: The URL of the event to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.client.table(self.table_name)\
                .delete()\
                .eq("url", url)\
                .execute()
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    def delete_events_by_urls(self, urls: List[str]) -> int:
        """
        Delete multiple events by their URLs.
        
        Args:
            urls: List of URLs to delete
            
        Returns:
            Number of events deleted
        """
        deleted = 0
        for url in urls:
            if self.delete_event_by_url(url):
                deleted += 1
        return deleted

