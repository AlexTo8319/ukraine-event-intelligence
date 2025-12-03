"""Validate event dates by checking URL content."""
import requests
from typing import Optional, Tuple
from datetime import date, datetime
import re
from urllib.parse import urlparse


class DateValidator:
    """Validates event dates by checking if URL content matches extracted date."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; EventIntelligenceBot/1.0)'
        })
    
    def extract_dates_from_text(self, text: str) -> list:
        """Extract dates from text content."""
        if not text:
            return []
        
        dates = []
        text_lower = text.lower()
        
        # Common date patterns
        # YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY, "December 5, 2025", etc.
        patterns = [
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # YYYY-MM-DD
            r'\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b',  # DD/MM/YYYY or DD.MM.YYYY
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})\b',
            r'\b(\d{1,2})\s+(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)\s+(\d{4})\b',  # Ukrainian
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    date_str = match.group(0)
                    # This is simplified - in production, use proper date parsing
                    dates.append(date_str)
                except:
                    pass
        
        return dates
    
    def check_if_past_event(self, url: str, extracted_date: date) -> Tuple[bool, Optional[str]]:
        """
        Check if URL content indicates the event is in the past.
        
        Args:
            url: Event URL to check
            extracted_date: Date extracted by LLM
            
        Returns:
            Tuple of (is_past: bool, reason: Optional[str])
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code != 200:
                return False, None  # Can't determine, assume valid
            
            content = response.text.lower()
            current_year = date.today().year
            
            # CRITICAL: Check for years in the past (e.g., 2023, 2024 when we're in 2025)
            # Look for date patterns with years
            year_patterns = [
                r'\b(202[0-4]|201[0-9])\b',  # Years 2020-2024 or 2010-2019
            ]
            
            for pattern in year_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    year = int(match.group(1))
                    # If we find a year that's significantly in the past (more than 1 year ago)
                    if year < current_year - 1:
                        # Check context - if it's near event-related keywords, it's likely a past event
                        match_pos = match.start()
                        context = content[max(0, match_pos - 100):match_pos + 100]
                        event_keywords = ['conference', 'event', 'forum', 'workshop', 'seminar', 'webinar', 
                                         'конференція', 'подія', 'форум', 'відбулося', 'було проведено']
                        if any(keyword in context for keyword in event_keywords):
                            return True, f"URL mentions past year {year} in event context"
            
            # Check for explicit past event indicators
            past_indicators = [
                "already happened", "was held", "took place", "occurred",
                "вже відбулося", "було проведено", "відбулося",
                "completed", "finished", "ended",
                "from.*to.*202[0-4]",  # "from X to Y 2023" pattern
            ]
            
            for indicator in past_indicators:
                if re.search(indicator, content, re.IGNORECASE):
                    # Check if it's talking about this specific event
                    # Look for date mentions near the indicator
                    matches = re.finditer(indicator, content, re.IGNORECASE)
                    for match in matches:
                        indicator_pos = match.start()
                        context = content[max(0, indicator_pos - 200):indicator_pos + 200]
                        
                        # Extract dates from context
                        dates_in_context = self.extract_dates_from_text(context)
                        
                        # If we find dates near the indicator, it's likely about a past event
                        if dates_in_context:
                            return True, f"URL content indicates past event: '{indicator}'"
            
            # Check if URL is a news article about a past event
            if "/news/" in url.lower() or "/article/" in url.lower():
                # News articles are usually about past events
                return True, "URL is a news article (likely about past event)"
            
            # Check for "From X to Y 2023" patterns (specific past event date ranges)
            date_range_pattern = r'from\s+(\d{1,2}\s+\w+\s+)?to\s+(\d{1,2}\s+\w+\s+)?(\d{4})'
            matches = re.finditer(date_range_pattern, content, re.IGNORECASE)
            for match in matches:
                year = int(match.group(3))
                if year < current_year:
                    return True, f"URL mentions past event date range ending in {year}"
            
            return False, None
            
        except Exception as e:
            # If we can't check, assume it's valid (don't reject on network errors)
            return False, None


