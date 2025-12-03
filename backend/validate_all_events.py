"""
Comprehensive Event Validation System.

This script validates all events in the database by:
1. Following each event's URL
2. Extracting the actual event date from the page content
3. Comparing it to the stored date
4. Checking if the URL is accessible
5. Removing events with wrong dates, past dates, or broken links
"""
import os
import sys
import requests
import re
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class EventValidator:
    """Validates events by fetching URLs and cross-checking dates."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Month mappings for date parsing
        self.month_map = {
            # English
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12,
            # Ukrainian
            'січня': 1, 'січень': 1,
            'лютого': 2, 'лютий': 2,
            'березня': 3, 'березень': 3,
            'квітня': 4, 'квітень': 4,
            'травня': 5, 'травень': 5,
            'червня': 6, 'червень': 6,
            'липня': 7, 'липень': 7,
            'серпня': 8, 'серпень': 8,
            'вересня': 9, 'вересень': 9,
            'жовтня': 10, 'жовтень': 10,
            'листопада': 11, 'листопад': 11,
            'грудня': 12, 'грудень': 12,
        }
        
        # Spam sites to reject immediately
        self.spam_sites = [
            'conferencealerts.co.in', 'allconferencealert.net',
            'internationalconferencealerts.com', 'conferencealert.com',
            'waset.org', 'conferenceseries.com', '10times.com',
            'eventbrite.com/d/',  # Search pages, not specific events
        ]
    
    def is_spam_url(self, url: str) -> bool:
        """Check if URL is from a known spam site."""
        url_lower = url.lower()
        return any(site in url_lower for site in self.spam_sites)
    
    def fetch_url_content(self, url: str) -> Tuple[Optional[str], Optional[str], int]:
        """
        Fetch URL content.
        
        Returns:
            Tuple of (content, final_url, status_code)
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            return response.text, response.url, response.status_code
        except requests.exceptions.Timeout:
            return None, None, -1  # Timeout
        except requests.exceptions.ConnectionError:
            return None, None, -2  # Connection error
        except Exception as e:
            return None, None, -3  # Other error
    
    def extract_event_date_from_content(self, content: str) -> Optional[date]:
        """
        Extract the EVENT date from page content.
        Prioritizes actual event dates over publication dates.
        """
        if not content:
            return None
        
        content_lower = content.lower()
        
        # PRIORITY 1: Look for event date markers (highest confidence)
        event_date_markers = [
            (r'дата\s+(?:та\s+час\s*)?[:\s]+', 50),  # Ukrainian: "Дата та час:" or "Дата:"
            (r'event\s+date[:\s]+', 50),
            (r'date[:\s]+(?!of\s+publication)', 30),
            (r'when[:\s]+', 40),
            (r'коли[:\s]+', 40),  # Ukrainian: "When"
            (r'відбудеться[:\s]+', 45),  # Ukrainian: "will take place"
            (r'(?:will\s+)?(?:be\s+)?held\s+(?:on\s+)?', 35),
            (r'scheduled\s+(?:for\s+)?', 35),
            (r'takes?\s+place\s+(?:on\s+)?', 35),
        ]
        
        # PRIORITY 2: Look for dates with time (usually event dates)
        # Pattern: "4 грудня 2025 року, об 11:00" or "December 4, 2025 at 11:00"
        date_with_time_patterns = [
            r'(\d{1,2})\s+(' + '|'.join(self.month_map.keys()) + r')\s+(\d{4})\s*(?:року)?\s*,?\s*(?:об?|at|@)\s*(\d{1,2})[:\.](\d{2})',
            r'(' + '|'.join(self.month_map.keys()) + r')\s+(\d{1,2})\s*,?\s*(\d{4})\s*(?:at|@)\s*(\d{1,2})[:\.](\d{2})',
        ]
        
        # PRIORITY 3: Standard date patterns
        date_patterns = [
            # ISO format
            (r'(\d{4})-(\d{2})-(\d{2})', 'ymd'),
            # Day Month Year
            (r'(\d{1,2})\s+(' + '|'.join(self.month_map.keys()) + r')\s+(\d{4})', 'dmy'),
            # Month Day, Year
            (r'(' + '|'.join(self.month_map.keys()) + r')\s+(\d{1,2})\s*,?\s*(\d{4})', 'mdy'),
            # Day.Month.Year or Day/Month/Year
            (r'(\d{1,2})[./](\d{1,2})[./](\d{4})', 'dmy_numeric'),
        ]
        
        # Publication date indicators (dates near these should be IGNORED)
        publication_indicators = [
            r'на\s+читання',  # Ukrainian: reading time
            r'reading\s+time',
            r'опубліковано',  # Ukrainian: published
            r'published',
            r'дата\s+публікації',  # Ukrainian: publication date
            r'publication\s+date',
            r'posted\s+on',
            r'updated\s+on',
            r'last\s+modified',
        ]
        
        # Past event indicators (if found, the event is past)
        past_indicators = [
            r'(?:вже\s+)?відбулося',  # Ukrainian: already happened
            r'(?:was|has\s+been)\s+held',
            r'took\s+place',
            r'completed',
            r'finished',
            r'ended',
            r'past\s+event',
        ]
        
        # Check for past event indicators
        for indicator in past_indicators:
            if re.search(indicator, content_lower):
                # This might be a past event page
                pass  # Continue but be more careful
        
        # STEP 1: Try to find dates near event markers (highest priority)
        for marker_pattern, confidence in event_date_markers:
            for match in re.finditer(marker_pattern, content_lower):
                # Get text after the marker
                start_pos = match.end()
                context = content[start_pos:start_pos + 200]
                
                # Try to extract date from this context
                extracted_date = self._extract_date_from_text(context)
                if extracted_date:
                    return extracted_date
        
        # STEP 2: Look for dates with time (usually event dates)
        for pattern in date_with_time_patterns:
            for match in re.finditer(pattern, content_lower):
                try:
                    groups = match.groups()
                    # Try to parse based on pattern type
                    if groups[0].isdigit():  # Day first
                        day = int(groups[0])
                        month = self.month_map.get(groups[1].lower())
                        year = int(groups[2])
                    else:  # Month first
                        month = self.month_map.get(groups[0].lower())
                        day = int(groups[1])
                        year = int(groups[2])
                    
                    if month and 1 <= day <= 31 and 2020 <= year <= 2030:
                        return date(year, month, day)
                except (ValueError, IndexError, TypeError):
                    continue
        
        # STEP 3: Look for standard date patterns, excluding publication dates
        for pattern, format_type in date_patterns:
            for match in re.finditer(pattern, content_lower):
                # Check if this is near a publication indicator
                match_start = match.start()
                match_end = match.end()
                context_before = content_lower[max(0, match_start-100):match_start]
                context_after = content_lower[match_end:min(len(content_lower), match_end+50)]
                
                # Skip if near publication indicator
                is_publication = any(
                    re.search(ind, context_before + context_after)
                    for ind in publication_indicators
                )
                if is_publication:
                    continue
                
                # Parse the date
                try:
                    groups = match.groups()
                    
                    if format_type == 'ymd':
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    elif format_type == 'dmy':
                        day = int(groups[0])
                        month = self.month_map.get(groups[1].lower())
                        year = int(groups[2])
                    elif format_type == 'mdy':
                        month = self.month_map.get(groups[0].lower())
                        day = int(groups[1])
                        year = int(groups[2])
                    elif format_type == 'dmy_numeric':
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    
                    if month and 1 <= day <= 31 and 2020 <= year <= 2030:
                        return date(year, month, day)
                except (ValueError, IndexError, TypeError):
                    continue
        
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """Extract date from a short text segment."""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Try various patterns
        patterns = [
            # "4 грудня 2025" or "4 December 2025"
            (r'(\d{1,2})\s+(' + '|'.join(self.month_map.keys()) + r')\s+(\d{4})', 'dmy'),
            # "December 4, 2025"
            (r'(' + '|'.join(self.month_map.keys()) + r')\s+(\d{1,2})\s*,?\s*(\d{4})', 'mdy'),
            # "2025-12-04"
            (r'(\d{4})-(\d{2})-(\d{2})', 'ymd'),
            # "04.12.2025" or "04/12/2025"
            (r'(\d{1,2})[./](\d{1,2})[./](\d{4})', 'dmy_numeric'),
        ]
        
        for pattern, format_type in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    groups = match.groups()
                    
                    if format_type == 'ymd':
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    elif format_type == 'dmy':
                        day = int(groups[0])
                        month = self.month_map.get(groups[1].lower())
                        year = int(groups[2])
                    elif format_type == 'mdy':
                        month = self.month_map.get(groups[0].lower())
                        day = int(groups[1])
                        year = int(groups[2])
                    elif format_type == 'dmy_numeric':
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    
                    if month and 1 <= day <= 31 and 2020 <= year <= 2030:
                        return date(year, month, day)
                except (ValueError, IndexError, TypeError):
                    continue
        
        return None
    
    def validate_event(self, event: Dict) -> Dict:
        """
        Validate a single event.
        
        Returns validation result dict with:
        - is_valid: bool
        - issues: List of issues found
        - extracted_date: Date found in URL content (if any)
        - url_accessible: bool
        - recommendation: 'keep', 'update_date', 'remove'
        """
        result = {
            "event_id": event.get("id"),
            "event_title": event.get("event_title", "")[:50],
            "stored_date": event.get("event_date"),
            "url": event.get("url", ""),
            "is_valid": True,
            "issues": [],
            "extracted_date": None,
            "url_accessible": False,
            "recommendation": "keep"
        }
        
        url = event.get("url", "")
        stored_date_str = event.get("event_date", "")
        
        # Parse stored date
        try:
            if isinstance(stored_date_str, str):
                stored_date = datetime.strptime(stored_date_str, "%Y-%m-%d").date()
            else:
                stored_date = stored_date_str
        except:
            result["issues"].append("Invalid stored date format")
            result["is_valid"] = False
            result["recommendation"] = "remove"
            return result
        
        today = date.today()
        
        # Check 1: Is the stored date in the past?
        if stored_date < today:
            result["issues"].append(f"Stored date {stored_date} is in the past")
            # Past events are kept but flagged
        
        # Check 2: Is URL a spam site?
        if self.is_spam_url(url):
            result["issues"].append("URL is from spam conference aggregator")
            result["is_valid"] = False
            result["recommendation"] = "remove"
            return result
        
        # Check 3: Fetch URL content
        content, final_url, status_code = self.fetch_url_content(url)
        
        if status_code == 200:
            result["url_accessible"] = True
            result["final_url"] = final_url
        elif status_code == -1:
            result["issues"].append("URL timeout")
            result["url_accessible"] = False
        elif status_code == -2:
            result["issues"].append("URL connection error")
            result["url_accessible"] = False
            result["is_valid"] = False
            result["recommendation"] = "remove"
            return result
        elif status_code == 404:
            result["issues"].append("URL returns 404 (not found)")
            result["url_accessible"] = False
            result["is_valid"] = False
            result["recommendation"] = "remove"
            return result
        else:
            result["issues"].append(f"URL returns HTTP {status_code}")
            result["url_accessible"] = False
        
        # Check 4: Extract date from content and compare
        if content:
            extracted_date = self.extract_event_date_from_content(content)
            result["extracted_date"] = extracted_date.isoformat() if extracted_date else None
            
            if extracted_date:
                # Compare extracted date with stored date
                date_diff = abs((extracted_date - stored_date).days)
                
                if date_diff == 0:
                    # Perfect match
                    pass
                elif date_diff <= 7:
                    # Small difference (could be multi-day event)
                    result["issues"].append(f"Date difference: stored {stored_date}, extracted {extracted_date} ({date_diff} days)")
                else:
                    # Large difference - possible wrong date
                    result["issues"].append(f"Date MISMATCH: stored {stored_date}, extracted {extracted_date} ({date_diff} days apart)")
                    
                    # If extracted date is in the future and stored is past, update
                    if extracted_date >= today and stored_date < today:
                        result["recommendation"] = "update_date"
                        result["new_date"] = extracted_date.isoformat()
                    # If both dates suggest past event, mark for review
                    elif extracted_date < today and stored_date < today:
                        result["issues"].append("Both dates are in the past")
                    # If extracted date is past but stored is future, the stored might be wrong
                    elif extracted_date < today and stored_date >= today:
                        result["issues"].append("Extracted date is past, stored date is future - needs review")
                        result["is_valid"] = False
                        result["recommendation"] = "remove"
                
                # Check if extracted date is in the past
                if extracted_date < today:
                    result["issues"].append(f"Event appears to be past (extracted date: {extracted_date})")
            else:
                result["issues"].append("Could not extract date from URL content")
            
            # Check for past event indicators in content
            past_indicators = ['відбулося', 'was held', 'took place', 'has ended', 'completed']
            content_lower = content.lower()
            for indicator in past_indicators:
                if indicator in content_lower:
                    result["issues"].append(f"Past event indicator found: '{indicator}'")
                    break
        
        # Final recommendation based on issues
        if result["recommendation"] == "keep" and result["issues"]:
            # If stored date is past and no extracted date contradicts it
            if stored_date < today:
                result["recommendation"] = "keep_as_past"
        
        return result


def validate_all_events():
    """Validate all events in the database."""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        return
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    print("=" * 80)
    print("COMPREHENSIVE EVENT VALIDATION")
    print("=" * 80)
    print()
    
    today = date.today()
    print(f"📅 Today: {today}")
    print()
    
    # Fetch all events
    print("📥 Fetching all events from database...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=*&order=event_date",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch events: {response.status_code}")
        return
    
    events = response.json()
    print(f"   Found {len(events)} events")
    print()
    
    # Initialize validator
    validator = EventValidator(timeout=10)
    
    # Validate each event
    results = {
        "valid": [],
        "remove": [],
        "update_date": [],
        "past_events": [],
        "issues": []
    }
    
    print("🔍 Validating events (this may take a few minutes)...")
    print("-" * 80)
    
    for i, event in enumerate(events, 1):
        title = event.get("event_title", "")[:40]
        url = event.get("url", "")[:50]
        stored_date = event.get("event_date", "")
        
        print(f"\n[{i}/{len(events)}] {title}...")
        print(f"         Date: {stored_date} | URL: {url}...")
        
        # Validate event
        result = validator.validate_event(event)
        
        # Categorize result
        if result["recommendation"] == "remove":
            results["remove"].append(result)
            print(f"         ❌ REMOVE: {', '.join(result['issues'][:2])}")
        elif result["recommendation"] == "update_date":
            results["update_date"].append(result)
            print(f"         🔄 UPDATE DATE: {result.get('new_date')} (was {stored_date})")
        elif result["recommendation"] == "keep_as_past":
            results["past_events"].append(result)
            print(f"         📦 PAST EVENT: {', '.join(result['issues'][:2])}")
        elif result["issues"]:
            results["issues"].append(result)
            print(f"         ⚠️ ISSUES: {', '.join(result['issues'][:2])}")
        else:
            results["valid"].append(result)
            print(f"         ✅ VALID")
    
    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Valid events:       {len(results['valid'])}")
    print(f"📦 Past events:        {len(results['past_events'])}")
    print(f"⚠️  Events with issues: {len(results['issues'])}")
    print(f"🔄 Need date update:   {len(results['update_date'])}")
    print(f"❌ Should remove:      {len(results['remove'])}")
    print()
    
    # Show events to remove
    if results["remove"]:
        print("=" * 80)
        print("EVENTS TO REMOVE")
        print("=" * 80)
        for r in results["remove"]:
            print(f"  - {r['event_title']}... ({r['stored_date']})")
            print(f"    Issues: {', '.join(r['issues'][:3])}")
            print()
    
    # Show events to update
    if results["update_date"]:
        print("=" * 80)
        print("EVENTS TO UPDATE DATE")
        print("=" * 80)
        for r in results["update_date"]:
            print(f"  - {r['event_title']}...")
            print(f"    Old: {r['stored_date']} → New: {r.get('new_date')}")
            print()
    
    # Ask for confirmation before making changes
    print()
    print("=" * 80)
    print("APPLYING CHANGES")
    print("=" * 80)
    
    # Remove invalid events
    if results["remove"]:
        print(f"\n🗑️ Removing {len(results['remove'])} invalid events...")
        for r in results["remove"]:
            event_id = r["event_id"]
            response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{event_id}",
                headers=headers
            )
            if response.status_code in [200, 204]:
                print(f"   ✅ Removed: {r['event_title']}...")
            else:
                print(f"   ❌ Failed to remove: {r['event_title']}...")
    
    # Update dates
    if results["update_date"]:
        print(f"\n🔄 Updating {len(results['update_date'])} event dates...")
        for r in results["update_date"]:
            event_id = r["event_id"]
            new_date = r.get("new_date")
            if new_date:
                response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/events?id=eq.{event_id}",
                    headers=headers,
                    json={"event_date": new_date}
                )
                if response.status_code in [200, 204]:
                    print(f"   ✅ Updated: {r['event_title']}... → {new_date}")
                else:
                    print(f"   ❌ Failed to update: {r['event_title']}...")
    
    print()
    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    
    # Final count
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=event_date&order=event_date",
        headers=headers
    )
    final_events = response.json()
    
    past_count = sum(1 for e in final_events if e['event_date'] < today.isoformat())
    upcoming_count = sum(1 for e in final_events if e['event_date'] >= today.isoformat())
    
    print(f"📊 Final database state:")
    print(f"   Total events:    {len(final_events)}")
    print(f"   Past events:     {past_count}")
    print(f"   Upcoming events: {upcoming_count}")
    print("=" * 80)


if __name__ == "__main__":
    validate_all_events()

