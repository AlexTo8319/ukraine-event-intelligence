"""
Smart Event Verification & Correction System v2.0

ENHANCED CAPABILITIES:
✅ Multi-query Tavily search for better URL finding
✅ Crawl 3+ levels deep from listing pages
✅ Date extraction with confidence scoring
✅ Social media fallback (search for alternative sources)
✅ Verify and correct information before removing
✅ Alternative URL support for inaccessible pages

WORKFLOW:
Event → Check URL → Is Working?
    ├── YES → Is Specific Event Page?
    │         ├── YES → Verify Date → KEEP/UPDATE
    │         └── NO  → Crawl Deep → Tavily Re-search
    └── NO  → Multi-Query Tavily Search
              ├── Found → Verify & UPDATE
              └── Not Found → REMOVE
"""
import os
import sys
import requests
import re
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Ukrainian character set for detection
UKR_CHARS = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'

def is_ukrainian(text: str) -> bool:
    """Check if text contains Ukrainian characters."""
    return any(c in (text or '').lower() for c in UKR_CHARS)

def translate_text(client, text: str, context: str = "text") -> str:
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
    except:
        return text


class SmartEventCorrector:
    """
    Intelligent event verification and correction system v2.0
    """
    
    def __init__(self, tavily_api_key: str = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,uk;q=0.8'
        })
        self.timeout = 15
        
        # Initialize Tavily
        self.tavily = None
        if TAVILY_AVAILABLE:
            api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
            if api_key:
                self.tavily = TavilyClient(api_key=api_key)
        
        # Month mappings
        self.month_map = {
            'january': 1, 'jan': 1, 'січня': 1, 'січень': 1,
            'february': 2, 'feb': 2, 'лютого': 2, 'лютий': 2,
            'march': 3, 'mar': 3, 'березня': 3, 'березень': 3,
            'april': 4, 'apr': 4, 'квітня': 4, 'квітень': 4,
            'may': 5, 'травня': 5, 'травень': 5,
            'june': 6, 'jun': 6, 'червня': 6, 'червень': 6,
            'july': 7, 'jul': 7, 'липня': 7, 'липень': 7,
            'august': 8, 'aug': 8, 'серпня': 8, 'серпень': 8,
            'september': 9, 'sep': 9, 'вересня': 9, 'вересень': 9,
            'october': 10, 'oct': 10, 'жовтня': 10, 'жовтень': 10,
            'november': 11, 'nov': 11, 'листопада': 11, 'листопад': 11,
            'december': 12, 'dec': 12, 'грудня': 12, 'грудень': 12,
        }
        
        # Spam sites to reject
        self.spam_sites = [
            'conferencealerts.co.in', 'allconferencealert.net',
            'internationalconferencealerts.com', 'conferencealert.com',
            'waset.org', 'conferenceseries.com', 'researchera.org',
        ]
    
    def verify_and_correct_event(self, event: Dict) -> Dict:
        """Main entry point: Verify and correct an event."""
        result = {
            "event_id": event.get("id"),
            "event_title": event.get("event_title", ""),
            "action": "keep",
            "corrections": {},
            "issues": [],
            "verification_details": []
        }
        
        url = event.get("url", "")
        title = event.get("event_title", "")
        stored_date = event.get("event_date", "")
        organizer = event.get("organizer", "")
        
        # Parse stored date
        try:
            stored_date_obj = datetime.strptime(stored_date, "%Y-%m-%d").date() if isinstance(stored_date, str) else stored_date
        except:
            stored_date_obj = None
        
        today = date.today()
        
        # STEP 1: Check URL accessibility
        result["verification_details"].append("Step 1: Checking URL...")
        url_result = self._check_url(url)
        
        # STEP 1b: If URL broken, try multi-query Tavily search
        if not url_result["accessible"]:
            result["issues"].append(f"URL issue: {url_result['error']}")
            
            # Check if it's a social media URL
            is_social = any(s in url.lower() for s in ['facebook.com', 'instagram.com', 'linkedin.com'])
            
            if is_social:
                result["verification_details"].append("Step 1b: Social media URL, searching for alternative...")
                new_url = self._multi_query_search(title, stored_date, organizer, exclude_social=True)
            else:
                result["verification_details"].append("Step 1b: URL broken, searching for alternative...")
                new_url = self._multi_query_search(title, stored_date, organizer)
            
            if new_url:
                result["corrections"]["url"] = new_url
                result["verification_details"].append(f"Found alternative: {new_url[:60]}...")
                url = new_url
                url_result = self._check_url(new_url)
            else:
                result["verification_details"].append("Could not find alternative URL")
                # Don't immediately remove - check if date is future
                if stored_date_obj and stored_date_obj >= today:
                    result["action"] = "keep"  # Keep future events even with bad URLs
                    result["issues"].append("URL not accessible but date is future - keeping")
                else:
                    result["action"] = "remove"
                return result
        
        # STEP 2: Check if URL is listing/generic page
        if url_result["accessible"] and url_result.get("content"):
            result["verification_details"].append("Step 2: Checking page type...")
            
            if self._is_listing_page(url, url_result["content"]):
                result["issues"].append("URL is listing page")
                result["verification_details"].append("Step 2b: Crawling for specific event URL...")
                
                # Try deep crawling (up to 3 levels)
                specific_url = self._deep_crawl_for_event(url, title, url_result["content"], max_depth=3)
                
                if specific_url and specific_url != url:
                    result["corrections"]["url"] = specific_url
                    result["verification_details"].append(f"Found via crawling: {specific_url[:60]}...")
                    url = specific_url
                    url_result = self._check_url(specific_url)
                else:
                    # Try multi-query Tavily search
                    result["verification_details"].append("Step 2c: Crawling failed, trying Tavily...")
                    new_url = self._multi_query_search(title, stored_date, organizer)
                    
                    if new_url and new_url != event.get("url"):
                        # Verify the new URL is better
                        new_result = self._check_url(new_url)
                        if new_result["accessible"] and not self._is_listing_page(new_url, new_result.get("content", "")):
                            result["corrections"]["url"] = new_url
                            result["verification_details"].append(f"Found via search: {new_url[:60]}...")
                            url = new_url
                            url_result = new_result
        
        # STEP 3: Verify/correct date with confidence scoring
        result["verification_details"].append("Step 3: Verifying date...")
        
        if url_result["accessible"] and url_result.get("content"):
            date_result = self._extract_date_with_confidence(url_result["content"], title)
            
            if date_result["date"]:
                extracted_date = date_result["date"]
                confidence = date_result["confidence"]
                result["verification_details"].append(
                    f"Extracted: {extracted_date} (confidence: {confidence:.0%}, source: {date_result['source']})"
                )
                
                if stored_date_obj:
                    date_diff = abs((extracted_date - stored_date_obj).days)
                    
                    if date_diff == 0:
                        result["verification_details"].append("✓ Date verified")
                    elif date_diff <= 7:
                        result["verification_details"].append(f"Date close ({date_diff} days) - likely multi-day event")
                    else:
                        result["issues"].append(f"Date mismatch: stored {stored_date_obj}, extracted {extracted_date}")
                        
                        # Decide correction based on confidence and which is future
                        if confidence >= 0.7:
                            if extracted_date >= today and stored_date_obj < today:
                                result["corrections"]["event_date"] = extracted_date.isoformat()
                                result["verification_details"].append(f"Correcting date to: {extracted_date}")
                            elif extracted_date < today and stored_date_obj >= today:
                                # High confidence extracted date is past, stored is future
                                result["issues"].append("Event appears to have already happened")
                                result["action"] = "remove"
                            elif extracted_date < today and stored_date_obj < today:
                                # Both past - keep as past event
                                result["verification_details"].append("Both dates past - keeping as historical")
            else:
                result["issues"].append("Could not extract date")
        
        # STEP 4: Check for past event indicators
        if url_result["accessible"] and url_result.get("content"):
            past_found = self._check_past_indicators(url_result["content"])
            if past_found:
                result["issues"].append(f"Past indicators: {past_found}")
        
        # STEP 5: Final decision
        result["verification_details"].append("Step 5: Final decision...")
        
        if result["action"] != "remove":
            if result["corrections"]:
                result["action"] = "update"
            elif not url_result["accessible"]:
                # Keep future events even with bad URLs
                if stored_date_obj and stored_date_obj >= today:
                    result["action"] = "keep"
                else:
                    result["action"] = "remove"
            else:
                result["action"] = "keep"
        
        return result
    
    def _check_url(self, url: str) -> Dict:
        """Check URL accessibility."""
        result = {"accessible": False, "status_code": None, "content": None, "error": None}
        
        # Check for spam sites
        if any(spam in url.lower() for spam in self.spam_sites):
            result["error"] = "Spam site"
            return result
        
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            result["status_code"] = response.status_code
            
            if response.status_code == 200:
                result["accessible"] = True
                result["content"] = response.text
            elif response.status_code == 400:
                result["error"] = "HTTP 400 (login required)"
            elif response.status_code == 403:
                result["error"] = "HTTP 403 (forbidden)"
            elif response.status_code == 404:
                result["error"] = "HTTP 404 (not found)"
            else:
                result["error"] = f"HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection error"
        except Exception as e:
            result["error"] = str(e)[:50]
        
        return result
    
    def _is_listing_page(self, url: str, content: str) -> bool:
        """Check if URL is a listing page."""
        url_lower = url.lower()
        
        # URL patterns indicating listings
        listing_patterns = [r'/$', r'/category/', r'/news/?$', r'/events/?$', r'/calendar']
        for pattern in listing_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # Content check - multiple event links
        if content:
            event_links = len(re.findall(r'href=["\'][^"\']*(?:event|conference|forum)[^"\']*["\']', content.lower()))
            if event_links > 5:
                return True
        
        return False
    
    def _deep_crawl_for_event(self, listing_url: str, event_title: str, content: str, max_depth: int = 3) -> Optional[str]:
        """Crawl up to max_depth levels to find specific event URL."""
        if not content:
            return None
        
        title_words = [w.lower() for w in event_title.split() if len(w) > 3]
        
        # Extract and score links
        href_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        links = re.findall(href_pattern, content, re.IGNORECASE | re.DOTALL)
        
        scored_links = []
        for href, link_text in links:
            if not href.startswith(('http://', 'https://')):
                href = urljoin(listing_url, href)
            
            href_lower = href.lower()
            link_text_lower = link_text.lower()
            
            # Skip bad links
            if any(skip in href_lower for skip in ['mailto:', 'tel:', '#', 'javascript:']):
                continue
            if any(spam in href_lower for spam in self.spam_sites):
                continue
            
            score = 0
            for word in title_words:
                if word in href_lower:
                    score += 3
                if word in link_text_lower:
                    score += 5
            
            # Boost for event patterns
            if 'eventdetail' in href_lower:
                score += 20
            elif '/event/' in href_lower:
                score += 15
            elif re.search(r'/\d{5,}', href_lower):
                score += 10
            
            if score > 0:
                scored_links.append((score, href))
        
        scored_links.sort(reverse=True, key=lambda x: x[0])
        
        # Try top candidates
        for score, candidate_url in scored_links[:5]:
            if candidate_url.rstrip('/') == listing_url.rstrip('/'):
                continue
            
            try:
                response = self.session.get(candidate_url, timeout=self.timeout)
                if response.status_code == 200:
                    if not self._is_listing_page(candidate_url, response.text):
                        # Check title match
                        matches = sum(1 for w in title_words if w in response.text.lower()[:5000])
                        if matches >= len(title_words) * 0.3:
                            return candidate_url
                    elif max_depth > 1:
                        # Go deeper
                        deeper = self._deep_crawl_for_event(candidate_url, event_title, response.text, max_depth - 1)
                        if deeper:
                            return deeper
            except:
                continue
        
        return None
    
    def _multi_query_search(self, title: str, event_date: str, organizer: str = None, exclude_social: bool = False) -> Optional[str]:
        """Use multiple Tavily queries to find the best URL."""
        if not self.tavily:
            return None
        
        # Generate multiple search queries
        queries = [
            f'"{title}" event registration 2025',
            f'"{title}" conference official site',
        ]
        
        if organizer and organizer not in ['Unknown', 'Various', 'N/A']:
            queries.append(f'{organizer} "{title}" 2025')
        
        # Add date-specific query
        if event_date:
            try:
                d = datetime.strptime(event_date, "%Y-%m-%d")
                month_name = d.strftime("%B")
                queries.append(f'"{title}" {month_name} 2025')
            except:
                pass
        
        title_words = [w.lower() for w in title.split() if len(w) > 3]
        best_url = None
        best_score = 0
        
        for query in queries[:3]:  # Limit to 3 queries to save API calls
            try:
                response = self.tavily.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                    include_answer=False
                )
                
                for result in response.get("results", []):
                    url = result.get("url", "")
                    content = result.get("content", "").lower()
                    
                    # Skip spam and social media if requested
                    if any(spam in url.lower() for spam in self.spam_sites):
                        continue
                    if exclude_social and any(s in url.lower() for s in ['facebook.com', 'instagram.com']):
                        continue
                    
                    # Score URL
                    score = sum(1 for w in title_words if w in content)
                    
                    # Boost for event-related URLs
                    if '/event' in url.lower():
                        score += 3
                    if 'registration' in url.lower() or 'register' in url.lower():
                        score += 2
                    
                    if score > best_score:
                        # Verify URL is accessible
                        check = self._check_url(url)
                        if check["accessible"]:
                            best_score = score
                            best_url = url
                            
            except Exception as e:
                continue
        
        return best_url
    
    def _extract_date_with_confidence(self, content: str, title: str) -> Dict:
        """Extract date with confidence scoring."""
        if not content:
            return {"date": None, "confidence": 0, "source": None}
        
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Date patterns with confidence
        date_sources = []
        
        # HIGH CONFIDENCE: Dates near event markers
        event_markers = [
            (r'дата\s+(?:та\s+час\s*)?[:\s]+', 0.95, 'date_marker_uk'),
            (r'event\s+date[:\s]+', 0.95, 'date_marker_en'),
            (r'when[:\s]+', 0.90, 'when_marker'),
            (r'коли[:\s]+', 0.90, 'when_marker_uk'),
        ]
        
        for marker_pattern, confidence, source in event_markers:
            for match in re.finditer(marker_pattern, content_lower):
                context = content[match.end():match.end() + 200]
                extracted = self._extract_date_from_text(context)
                if extracted:
                    date_sources.append({"date": extracted, "confidence": confidence, "source": source})
        
        # MEDIUM CONFIDENCE: Dates with time
        time_pattern = r'(\d{1,2})\s+(' + '|'.join(self.month_map.keys()) + r')\s+(\d{4})\s*(?:року)?\s*,?\s*(?:об?|at)\s*\d{1,2}'
        for match in re.finditer(time_pattern, content_lower):
            extracted = self._parse_date_match(match)
            if extracted:
                date_sources.append({"date": extracted, "confidence": 0.85, "source": "date_with_time"})
        
        # MEDIUM: Dates near title words
        for word in title_lower.split():
            if len(word) > 4:
                word_pos = content_lower.find(word)
                if word_pos != -1:
                    context = content_lower[max(0, word_pos-100):word_pos+200]
                    extracted = self._extract_date_from_text(context)
                    if extracted:
                        date_sources.append({"date": extracted, "confidence": 0.70, "source": "near_title"})
                        break
        
        # LOW CONFIDENCE: Any date on page
        general_pattern = r'(\d{1,2})\s+(' + '|'.join(self.month_map.keys()) + r')\s+(\d{4})'
        for match in re.finditer(general_pattern, content_lower):
            extracted = self._parse_date_match(match)
            if extracted and extracted.year >= 2024:
                date_sources.append({"date": extracted, "confidence": 0.40, "source": "general"})
        
        # Return highest confidence
        if date_sources:
            date_sources.sort(key=lambda x: x["confidence"], reverse=True)
            return date_sources[0]
        
        return {"date": None, "confidence": 0, "source": None}
    
    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """Extract date from text."""
        if not text:
            return None
        
        patterns = [
            (r'(\d{1,2})\s+(' + '|'.join(self.month_map.keys()) + r')\s+(\d{4})', 'dmy'),
            (r'(' + '|'.join(self.month_map.keys()) + r')\s+(\d{1,2})\s*,?\s*(\d{4})', 'mdy'),
            (r'(\d{4})-(\d{2})-(\d{2})', 'iso'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return self._parse_date_match(match, fmt)
        
        return None
    
    def _parse_date_match(self, match, fmt: str = 'dmy') -> Optional[date]:
        """Parse a regex match into a date."""
        try:
            groups = match.groups()
            
            if fmt == 'iso':
                return date(int(groups[0]), int(groups[1]), int(groups[2]))
            elif fmt == 'dmy':
                day = int(groups[0])
                month = self.month_map.get(groups[1].lower())
                year = int(groups[2])
            elif fmt == 'mdy':
                month = self.month_map.get(groups[0].lower())
                day = int(groups[1])
                year = int(groups[2])
            else:
                return None
            
            if month and 1 <= day <= 31 and 2024 <= year <= 2027:
                return date(year, month, day)
        except:
            pass
        return None
    
    def _check_past_indicators(self, content: str) -> List[str]:
        """Check for past event indicators."""
        if not content:
            return []
        
        indicators = ['відбулося', 'was held', 'took place', 'has ended', 'completed', 'завершено']
        return [ind for ind in indicators if ind in content.lower()]


def correct_all_events():
    """Main function to verify and correct all events."""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    print("=" * 100)
    print("SMART EVENT VERIFICATION & CORRECTION SYSTEM v2.0")
    print("=" * 100)
    print()
    print("Features:")
    print("  ✅ Multi-query Tavily search for better URL finding")
    print("  ✅ Deep crawling (3 levels) for specific event URLs")
    print("  ✅ Date extraction with confidence scoring")
    print("  ✅ Social media fallback (finds alternative sources)")
    print("  ✅ Keeps future events even with URL issues")
    print()
    
    # Fetch events
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=*&order=event_date",
        headers=headers
    )
    events = response.json()
    print(f"📥 Found {len(events)} events to verify")
    print()
    
    corrector = SmartEventCorrector()
    results = {"keep": [], "update": [], "remove": []}
    
    for i, event in enumerate(events, 1):
        print(f"\n{'='*100}")
        print(f"[{i}/{len(events)}] {event['event_title'][:50]}...")
        print(f"         Date: {event['event_date']} | URL: {event['url'][:50]}...")
        print("-" * 100)
        
        result = corrector.verify_and_correct_event(event)
        
        for detail in result["verification_details"]:
            print(f"  {detail}")
        
        if result["issues"]:
            print(f"\n  ⚠️ Issues: {result['issues']}")
        if result["corrections"]:
            print(f"  🔧 Corrections: {list(result['corrections'].keys())}")
        print(f"\n  📋 Action: {result['action'].upper()}")
        
        results[result["action"]].append(result)
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"✅ KEEP:   {len(results['keep'])}")
    print(f"🔧 UPDATE: {len(results['update'])}")
    print(f"❌ REMOVE: {len(results['remove'])}")
    
    # Apply updates
    if results["update"]:
        print("\n" + "-" * 50)
        print("APPLYING UPDATES...")
        for r in results["update"]:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{r['event_id']}",
                headers=headers,
                json=r["corrections"]
            )
            status = "✅" if response.status_code in [200, 204] else "❌"
            print(f"  {status} {r['event_title'][:40]}... ({list(r['corrections'].keys())})")
    
    # Apply removals
    if results["remove"]:
        print("\n" + "-" * 50)
        print("REMOVING UNFIXABLE EVENTS...")
        for r in results["remove"]:
            response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{r['event_id']}",
                headers=headers
            )
            status = "✅" if response.status_code in [200, 204] else "❌"
            print(f"  {status} {r['event_title'][:40]}...")
    
    # TRANSLATION STEP
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and OPENAI_AVAILABLE:
        print("\n" + "-" * 50)
        print("TRANSLATING UKRAINIAN CONTENT...")
        
        # Refresh events after corrections
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/events?select=*&order=event_date",
            headers=headers
        )
        events = response.json()
        
        openai_client = OpenAI(api_key=openai_key)
        translated_count = 0
        
        for event in events:
            updates = {}
            
            if is_ukrainian(event.get('event_title', '')):
                updates['event_title'] = translate_text(openai_client, event['event_title'], "event title")
                print(f"  ✅ Translated: {event['event_title'][:30]}... → {updates['event_title'][:30]}...")
            
            if is_ukrainian(event.get('organizer', '')):
                updates['organizer'] = translate_text(openai_client, event['organizer'], "organization name")
            
            if is_ukrainian(event.get('summary', '')):
                updates['summary'] = translate_text(openai_client, event['summary'], "event description")
            
            if updates:
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/events?id=eq.{event['id']}",
                    headers=headers,
                    json=updates
                )
                translated_count += 1
        
        print(f"  Translated {translated_count} events")
    else:
        print("\n⚠️ Skipping translation (OPENAI_API_KEY not set)")
    
    print("\n" + "=" * 100)
    print("CORRECTION COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    correct_all_events()
