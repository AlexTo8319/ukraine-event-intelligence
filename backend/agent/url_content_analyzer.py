"""Analyze URL content to extract event information and validate dates."""
import requests
from typing import Optional, Tuple, Dict
from datetime import date, datetime
from urllib.parse import urljoin
import re
from urllib.parse import urlparse, urljoin


class URLContentAnalyzer:
    """Analyzes URL content to extract event information and validate dates."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; EventIntelligenceBot/1.0)'
        })
    
    def extract_date_from_content(self, content: str) -> Optional[date]:
        """
        Extract EVENT date from page content.
        Prioritizes event dates over publication dates.
        """
        if not content:
            return None
        
        content_lower = content.lower()
        
        # CRITICAL: Look for event date markers first (these indicate the actual event date, not publication date)
        event_date_markers = [
            r'дата\s+та\s+час[:\s]+',  # "Дата та час:" (Ukrainian: Date and time)
            r'дата[:\s]+',  # "Дата:" (Ukrainian: Date)
            r'event\s+date[:\s]+',  # "Event date:"
            r'date[:\s]+',  # "Date:"
            r'when[:\s]+',  # "When:"
            r'коли[:\s]+',  # "Коли:" (Ukrainian: When)
            r'відбудеться[:\s]+',  # "відбудеться:" (Ukrainian: will take place)
            r'будет\s+проводиться[:\s]+',  # "будет проводиться:" (Russian: will be held)
        ]
        
        # Look for publication date indicators (these should be IGNORED)
        publication_indicators = [
            r'на\s+читання',  # "на читання" (reading time)
            r'reading\s+time',
            r'опубліковано',  # "опубліковано" (published)
            r'published',
            r'дата\s+публікації',  # "дата публікації" (publication date)
            r'publication\s+date',
        ]
        
        # First, try to find dates near event date markers (highest priority)
        for marker in event_date_markers:
            marker_pattern = re.compile(marker, re.IGNORECASE)
            for match in marker_pattern.finditer(content):
                # Extract text after the marker (up to 200 characters)
                start_pos = match.end()
                context = content[start_pos:start_pos + 200]
                
                # Look for date patterns in this context
                event_date = self._extract_date_from_text(context)
                if event_date:
                    return event_date
        
        # If no event date marker found, look for dates with time information (also indicates event date)
        time_patterns = [
            r'(\d{1,2})\s+(грудня|грудень|листопада|листопад|січня|січень|лютого|лютий|березня|березень|квітня|квітень|травня|травень|червня|червень|липня|липень|серпня|серпень|вересня|вересень|жовтня|жовтень)\s+(\d{4})\s+року,\s+об\s+(\d{1,2}):(\d{2})',  # "4 грудня 2025 року, об 11:00"
            r'(\d{1,2})\s+(december|november|january|february|march|april|may|june|july|august|september|october)\s+(\d{4}),?\s+at\s+(\d{1,2}):(\d{2})',  # "4 December 2025, at 11:00"
            r'(\d{1,2})\s+(грудня|грудень|листопада|листопад)\s+(\d{4})\s+року',  # "4 грудня 2025 року"
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    event_date = self._parse_date_match(match, content)
                    if event_date:
                        return event_date
                except (ValueError, IndexError):
                    continue
        
        # Finally, look for all date patterns but exclude those near publication indicators
        date_patterns = [
            r'(december|грудня|грудень|листопада|листопад|січня|січень|лютого|лютий|березня|березень|квітня|квітень|травня|травень|червня|червень|липня|липень|серпня|серпень|вересня|вересень|жовтня|жовтень)\s+(\d{1,2})[-\s]+(\d{1,2}),?\s+(\d{4})',  # December 1-5, 2025
            r'(\d{1,2})[-\s]+(\d{1,2})\s+(december|грудня|грудень|листопада|листопад)\s+(\d{4})',  # 1-5 December 2025
            r'(december|грудня|грудень|листопада|листопад|січня|січень|лютого|лютий|березня|березень|квітня|квітень|травня|травень|червня|червень|липня|липень|серпня|серпень|вересня|вересень|жовтня|жовтень)\s+(\d{1,2}),?\s+(\d{4})',  # December 1, 2025
            r'(\d{1,2})\s+(december|грудня|грудень|листопада|листопад|січня|січень|лютого|лютий|березня|березень|квітня|квітень|травня|травень|червня|червень|липня|липень|серпня|серпень|вересня|вересень|жовтня|жовтень)\s+(\d{4})',  # 1 December 2025
            r'(\d{4})-(\d{2})-(\d{2})',  # 2025-12-01
            r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+(грудня|грудень|листопада|листопад)',  # 01-05 ГРУДНЯ
        ]
        
        # Month names mapping
        month_map = {
            'january': 1, 'січня': 1, 'січень': 1,
            'february': 2, 'лютого': 2, 'лютий': 2,
            'march': 3, 'березня': 3, 'березень': 3,
            'april': 4, 'квітня': 4, 'квітень': 4,
            'may': 5, 'травня': 5, 'травень': 5,
            'june': 6, 'червня': 6, 'червень': 6,
            'july': 7, 'липня': 7, 'липень': 7,
            'august': 8, 'серпня': 8, 'серпень': 8,
            'september': 9, 'вересня': 9, 'вересень': 9,
            'october': 10, 'жовтня': 10, 'жовтень': 10,
            'november': 11, 'листопада': 11, 'листопад': 11,
            'december': 12, 'грудня': 12, 'грудень': 12,
        }
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Check if this date is near a publication indicator (skip it)
                match_start = match.start()
                match_end = match.end()
                context_before = content[max(0, match_start-100):match_start].lower()
                context_after = content[match_end:min(len(content), match_end+100)].lower()
                
                # Skip if near publication indicators
                is_publication_date = any(
                    re.search(indicator, context_before + context_after, re.IGNORECASE)
                    for indicator in publication_indicators
                )
                if is_publication_date:
                    continue
                
                try:
                    event_date = self._parse_date_match(match, content, month_map)
                    if event_date:
                        return event_date
                except (ValueError, IndexError, TypeError) as e:
                    # TypeError might be from missing month_map, try without it
                    try:
                        event_date = self._parse_date_match(match, content, month_map)
                        if event_date:
                            return event_date
                    except:
                        continue
                    continue
        
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """Extract date from text using various patterns."""
        if not text:
            return None
        
        # Month names mapping
        month_map = {
            'january': 1, 'січня': 1, 'січень': 1,
            'february': 2, 'лютого': 2, 'лютий': 2,
            'march': 3, 'березня': 3, 'березень': 3,
            'april': 4, 'квітня': 4, 'квітень': 4,
            'may': 5, 'травня': 5, 'травень': 5,
            'june': 6, 'червня': 6, 'червень': 6,
            'july': 7, 'липня': 7, 'липень': 7,
            'august': 8, 'серпня': 8, 'серпень': 8,
            'september': 9, 'вересня': 9, 'вересень': 9,
            'october': 10, 'жовтня': 10, 'жовтень': 10,
            'november': 11, 'листопада': 11, 'листопад': 11,
            'december': 12, 'грудня': 12, 'грудень': 12,
        }
        
        # Pattern: "4 грудня 2025 року, об 11:00" or "4 December 2025, at 11:00"
        time_pattern = r'(\d{1,2})\s+(' + '|'.join(month_map.keys()) + r')\s+(\d{4})'
        match = re.search(time_pattern, text, re.IGNORECASE)
        if match:
            try:
                day = int(match.group(1))
                month_name = match.group(2).lower()
                year = int(match.group(3))
                month = month_map.get(month_name)
                if month:
                    return date(year, month, day)
            except (ValueError, IndexError):
                pass
        
        # Pattern: YYYY-MM-DD
        iso_pattern = r'(\d{4})-(\d{2})-(\d{2})'
        match = re.search(iso_pattern, text)
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return date(year, month, day)
            except (ValueError, IndexError):
                pass
        
        return None
    
    def _parse_date_match(self, match, content: str, month_map: dict = None) -> Optional[date]:
        """Parse a date match into a date object."""
        if month_map is None:
            # Default month map if not provided
            month_map = {
                'january': 1, 'січня': 1, 'січень': 1,
                'february': 2, 'лютого': 2, 'лютий': 2,
                'march': 3, 'березня': 3, 'березень': 3,
                'april': 4, 'квітня': 4, 'квітень': 4,
                'may': 5, 'травня': 5, 'травень': 5,
                'june': 6, 'червня': 6, 'червень': 6,
                'july': 7, 'липня': 7, 'липень': 7,
                'august': 8, 'серпня': 8, 'серпень': 8,
                'september': 9, 'вересня': 9, 'вересень': 9,
                'october': 10, 'жовтня': 10, 'жовтень': 10,
                'november': 11, 'листопада': 11, 'листопад': 11,
                'december': 12, 'грудня': 12, 'грудень': 12,
            }
        
        try:
            groups = match.groups()
            match_text = match.group(0).lower()
            
            # Check if it's a month name pattern
            for month_name, month_num in month_map.items():
                if month_name in match_text:
                    # Pattern: "4 грудня 2025" or "December 4, 2025"
                    if len(groups) >= 3:
                        try:
                            # Format: "4 грудня 2025" -> groups[0]=day, groups[1]=month_name, groups[2]=year
                            if groups[0].isdigit() and groups[1].lower() in month_map and groups[2].isdigit():
                                day = int(groups[0])
                                month = month_map[groups[1].lower()]
                                year = int(groups[2])
                                return date(year, month, day)
                            # Format: "December 4, 2025" -> groups[0]=month_name, groups[1]=day, groups[2]=year
                            elif groups[0].lower() in month_map and groups[1].isdigit() and groups[2].isdigit():
                                month = month_map[groups[0].lower()]
                                day = int(groups[1])
                                year = int(groups[2])
                                return date(year, month, day)
                        except (ValueError, IndexError, KeyError):
                            pass
            
            # Pattern: YYYY-MM-DD
            if len(groups) == 3 and groups[0].isdigit() and len(groups[0]) == 4:
                try:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    return date(year, month, day)
                except (ValueError, IndexError):
                    pass
            
            return None
        except Exception:
            return None
        
        return None
    
    def find_event_url_in_content(self, content: str, event_title: str, base_url: str) -> Optional[str]:
        """Find the best matching event URL in content based on title."""
        if not content or not event_title:
            return None
        
        # Extract URLs from href attributes (most reliable)
        href_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        href_matches = re.findall(href_pattern, content, re.IGNORECASE | re.DOTALL)
        
        # Also extract plain URLs from text
        url_pattern = r'https?://[^\s<>"\'\)]+'
        text_urls = re.findall(url_pattern, content, re.IGNORECASE)
        
        # Combine and clean URLs
        clean_urls = []
        title_lower = event_title.lower()
        title_words = [w.lower() for w in event_title.split() if len(w) > 4]
        
        # Process href URLs (with link text for better matching)
        for href_url, link_text in href_matches:
            if not href_url:
                continue
            if not href_url.startswith(('http://', 'https://')):
                href_url = urljoin(base_url, href_url)
            if href_url.startswith(('http://', 'https://')):
                clean_urls.append((href_url, link_text))
        
        # Process text URLs
        for text_url in text_urls:
            text_url = text_url.rstrip('.,;:!?)')
            if text_url.startswith(('http://', 'https://')):
                clean_urls.append((text_url, ''))
        
        # Remove duplicates
        seen = set()
        unique_urls = []
        for url, text in clean_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append((url, text))
        
        # Score URLs based on title match
        scored_urls = []
        
        for url, link_text in unique_urls:
            url_lower = url.lower()
            link_text_lower = link_text.lower()
            score = 0
            
            # Skip non-event URLs
            if any(skip in url_lower for skip in ['/contact', '/about', '/home$', '/news/', '/article/', 'mailto:', 'tel:', '#']):
                if 'eventdetail' not in url_lower and '/event/' not in url_lower:
                    continue
            
            # Very high score for eventdetail (e.g., eventdetail/3264530)
            if 'eventdetail' in url_lower:
                score += 30
            
            # High score for /event/ or /events/ patterns
            if '/event/' in url_lower or '/events/' in url_lower:
                score += 15
            
            # Score based on title match in URL
            if title_words:
                url_matches = sum(1 for word in title_words if word in url_lower)
                score += url_matches * 5
                
                # Score based on link text match (very important)
                text_matches = sum(1 for word in title_words if word in link_text_lower)
                score += text_matches * 10  # Link text is very reliable
            
            # Check context around URL in content
            url_pos = content.lower().find(url_lower)
            if url_pos != -1:
                context = content[max(0, url_pos-300):min(len(content), url_pos+len(url)+300)].lower()
                context_matches = sum(1 for word in title_words if word in context)
                score += context_matches * 2
            
            # Boost for event keywords in URL
            if any(kw in url_lower for kw in ['conference', 'workshop', 'seminar', 'webinar', 'forum']):
                score += 5
            
            if score > 0:
                scored_urls.append((score, url))
        
        # Return highest scored URL
        if scored_urls:
            scored_urls.sort(reverse=True, key=lambda x: x[0])
            best_url = scored_urls[0][1]
            if scored_urls[0][0] >= 10:  # Only return if score is high enough
                return best_url
        
        return None
    
    def analyze_url(self, url: str, event_title: str = None, expected_date: date = None) -> Dict:
        """
        Analyze URL content to extract event information.
        
        Returns:
            Dict with: actual_url, extracted_date, is_valid, is_program_description, is_generic_page
        """
        # STRICT: Reject spam conference aggregator sites immediately
        url_lower = url.lower()
        spam_sites = [
            'conferencealerts.co.in', 'allconferencealert.net', 
            'internationalconferencealerts.com', 'conferencealert.com',
            'waset.org'
        ]
        if any(site in url_lower for site in spam_sites):
            return {"actual_url": url, "extracted_date": None, "is_valid": False, 
                    "error": "Spam conference aggregator site"}
        
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if response.status_code != 200:
                return {"actual_url": url, "extracted_date": None, "is_valid": False, "error": f"HTTP {response.status_code}"}
            
            content = response.text
            content_lower = content.lower()
            final_url = response.url  # Get final URL after redirects
            
            result = {
                "actual_url": final_url,
                "extracted_date": None,
                "is_valid": True,
                "content": content,
                "is_program_description": False,
                "is_generic_page": False
            }
            
            # Check if this is a generic landing page (not a specific event)
            generic_indicators = [
                r'^https?://[^/]+/?$',  # Root domain only
                r'^https?://[^/]+/home/?$',  # /home page
                r'^https?://[^/]+/program/[^/]+/?$',  # Program description page
            ]
            
            is_generic = False
            for pattern in generic_indicators:
                if re.match(pattern, final_url, re.IGNORECASE):
                    is_generic = True
                    break
            
            # Also check content for program description indicators
            program_indicators = [
                'програма підтримки', 'program support', 'program description',
                'мета програми', 'program goal', 'це програма', 'this program',
                'учасники програми', 'program participants'
            ]
            
            is_program = any(indicator in content_lower for indicator in program_indicators)
            
            # If it's a program description page and no specific event date found, mark it
            if is_program or (is_generic and '/program/' in final_url.lower()):
                result["is_program_description"] = True
                # Still try to extract date, but mark it as program description
            
            result["is_generic_page"] = is_generic
            
            # Extract date from content
            extracted_date = self.extract_date_from_content(content)
            if extracted_date:
                result["extracted_date"] = extracted_date
                
                # Check if extracted date is in the past (more than 1 year ago)
                current_year = date.today().year
                if extracted_date.year < current_year - 1:
                    result["is_valid"] = False
                    result["error"] = f"Extracted date {extracted_date} is in the past"
            
            # If we have event title, try to find better URL in content
            if event_title:
                better_url = self.find_event_url_in_content(content, event_title, final_url)
                if better_url and better_url != final_url:
                    result["actual_url"] = better_url
                    result["found_better_url"] = True
                    print(f"    Found better URL: {better_url[:60]}...")
            
            # Validate date if expected (be more lenient)
            if expected_date and extracted_date:
                # Allow 1 day difference (for multi-day events)
                date_diff = abs((extracted_date - expected_date).days)
                result["date_matches"] = date_diff <= 1
                
                # Only mark as invalid if:
                # 1. Extracted date is in the past (more than 1 year ago)
                # 2. Dates are years apart (more than 1 year difference)
                current_year = date.today().year
                if extracted_date.year < current_year - 1:
                    result["is_valid"] = False
                    result["error"] = f"Date mismatch: extracted date {extracted_date} is in past year"
                elif abs(extracted_date.year - expected_date.year) > 1:
                    result["is_valid"] = False
                    result["error"] = f"Date mismatch: dates are more than 1 year apart ({expected_date} vs {extracted_date})"
                # For smaller differences, keep it valid (might be multi-day events or timezone issues)
            elif expected_date:
                result["date_matches"] = None  # Couldn't extract date to compare
            
            return result
            
        except Exception as e:
            return {"actual_url": url, "extracted_date": None, "is_valid": False, "error": str(e)}

