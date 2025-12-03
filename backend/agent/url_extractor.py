"""Extract URLs from content, especially event registration links."""
import re
from typing import List, Set
from urllib.parse import urljoin, urlparse


class URLExtractor:
    """Extracts URLs from text content, especially event-related URLs."""
    
    def __init__(self):
        # Patterns for event-related URLs
        self.event_keywords = [
            r'event', r'conference', r'workshop', r'seminar', r'webinar',
            r'forum', r'meeting', r'register', r'registration', r'ticket',
            r'signup', r'rsvp', r'attend', r'join'
        ]
    
    def extract_urls_from_text(self, text: str, base_url: str = None) -> List[str]:
        """
        Extract all URLs from text content.
        
        Args:
            text: Text content to extract URLs from
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of extracted URLs
        """
        if not text:
            return []
        
        # URL pattern: http:// or https:// followed by valid URL characters
        url_pattern = r'https?://[^\s<>"\'\)]+|www\.[^\s<>"\'\)]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        # Clean and normalize URLs
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = url.rstrip('.,;:!?)')
            # Add https:// if starts with www.
            if url.startswith('www.'):
                url = 'https://' + url
            # Resolve relative URLs
            if base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # Remove duplicates
    
    def extract_event_urls(self, text: str, base_url: str = None) -> List[str]:
        """
        Extract URLs that are likely event-related (registration, event pages).
        
        Args:
            text: Text content to extract URLs from
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of event-related URLs
        """
        all_urls = self.extract_urls_from_text(text, base_url)
        
        event_urls = []
        text_lower = text.lower()
        
        for url in all_urls:
            url_lower = url.lower()
            
            # Skip non-event URLs
            skip_patterns = ['/contact', '/about', '/home$', '/news/', '/article/', 'mailto:', 'tel:', '#']
            if any(pattern in url_lower for pattern in skip_patterns):
                # But allow if it's clearly an event URL (e.g., eventdetail/123)
                if 'eventdetail' not in url_lower and '/event/' not in url_lower:
                    continue
            
            # Check if URL contains event-related keywords
            if any(keyword in url_lower for keyword in self.event_keywords):
                event_urls.append(url)
            # Check if URL has eventdetail pattern (high priority)
            elif 'eventdetail' in url_lower:
                event_urls.append(url)
            # Check if URL appears near event-related text
            else:
                url_pos = text_lower.find(url_lower)
                if url_pos != -1:
                    # Check context around URL (100 chars before and after for better matching)
                    context_start = max(0, url_pos - 100)
                    context_end = min(len(text_lower), url_pos + len(url) + 100)
                    context = text_lower[context_start:context_end]
                    
                    # Check for event-related words near URL
                    event_context_words = [
                        'register', 'registration', 'ticket', 'attend', 'join',
                        'conference', 'workshop', 'event', 'meeting', 'forum',
                        'webinar', 'seminar', 'summit'
                    ]
                    if any(word in context for word in event_context_words):
                        event_urls.append(url)
        
        return list(set(event_urls))  # Remove duplicates
    
    def extract_urls_from_html(self, html_content: str, base_url: str = None) -> List[str]:
        """
        Extract URLs from HTML content, especially from links.
        Prioritizes eventdetail URLs.
        
        Args:
            html_content: HTML content to extract URLs from
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of extracted URLs (eventdetail URLs first)
        """
        if not html_content:
            return []
        
        urls = []
        eventdetail_urls = []
        
        # Extract href attributes from <a> tags
        href_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
        href_urls = re.findall(href_pattern, html_content, re.IGNORECASE)
        
        for url in href_urls:
            # Clean URL
            url = url.strip()
            if not url or url.startswith('#'):
                continue
            # Resolve relative URLs
            if base_url and not url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                url = urljoin(base_url, url)
            if url.startswith(('http://', 'https://')):
                # Prioritize eventdetail URLs
                if 'eventdetail' in url.lower():
                    if url not in eventdetail_urls:
                        eventdetail_urls.append(url)
                else:
                    if url not in urls:
                        urls.append(url)
        
        # Also extract plain URLs from text
        text_urls = self.extract_urls_from_text(html_content, base_url)
        for url in text_urls:
            if 'eventdetail' in url.lower():
                if url not in eventdetail_urls:
                    eventdetail_urls.append(url)
            elif url not in urls:
                urls.append(url)
        
        # Return eventdetail URLs first, then others
        return eventdetail_urls + urls
    
    def find_best_event_url(self, content: str, listing_url: str, event_title: str = None) -> str:
        """
        Find the best event URL from content.
        Prioritizes direct event pages over listing pages.
        
        Args:
            content: Page content (text or HTML)
            listing_url: URL of the listing page
            event_title: Optional event title to help identify relevant URLs
            
        Returns:
            Best event URL found, or listing_url if none found
        """
        # Extract all URLs
        all_urls = self.extract_urls_from_html(content, listing_url)
        if not all_urls:
            all_urls = self.extract_urls_from_text(content, listing_url)
        
        if not all_urls:
            return listing_url
        
        # Prioritize event-related URLs
        event_urls = self.extract_event_urls(content, listing_url)
        
        if event_urls:
            # If we have event title, try to match URLs that contain title keywords
            if event_title:
                title_words = event_title.lower().split()
                for url in event_urls:
                    url_lower = url.lower()
                    # Check if URL contains significant words from title
                    matching_words = sum(1 for word in title_words if len(word) > 4 and word in url_lower)
                    if matching_words >= 2:  # At least 2 significant words match
                        return url
            # Return first event URL
            return event_urls[0]
        
        # If no event URLs found, return listing URL
        return listing_url

