"""Follow URLs from aggregator/listing pages to find direct event pages."""
import requests
from typing import Optional, List, Dict
from urllib.parse import urljoin, urlparse
import re
import time


class URLFollower:
    """Follows URLs from aggregator pages to find direct event pages."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; EventIntelligenceBot/1.0)'
        })
    
    def is_aggregator_page(self, url: str, content: str) -> bool:
        """Check if URL is an aggregator/listing page."""
        url_lower = url.lower()
        content_lower = content.lower() if content else ""
        
        # Aggregator indicators
        aggregator_patterns = [
            r'/events?[/-]?$',  # /events, /event, /events/
            r'/home$',  # /home
            r'/calendar',  # /calendar
            r'/upcoming',  # /upcoming
            r'eventdetail',  # eventdetail in URL
        ]
        
        # Check URL
        for pattern in aggregator_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # Check content for multiple events
        if content:
            # Look for multiple event links or event listings
            event_link_count = len(re.findall(r'href=["\']([^"\']*event[^"\']*)["\']', content_lower))
            if event_link_count > 3:  # Multiple event links suggests aggregator
                return True
        
        return False
    
    def extract_event_links_from_page(self, url: str, event_title: str = None) -> List[str]:
        """
        Extract direct event links from an aggregator page.
        
        Args:
            url: Aggregator page URL
            event_title: Optional event title to match against
            
        Returns:
            List of direct event URLs found, sorted by relevance
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if response.status_code != 200:
                return []
            
            content = response.text
            content_lower = content.lower()
            
            # Extract all links with their context
            href_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
            link_matches = re.findall(href_pattern, content, re.IGNORECASE | re.DOTALL)
            
            event_urls = []
            title_words = []
            if event_title:
                title_words = [w.lower() for w in event_title.split() if len(w) > 4]
            
            scored_urls = []
            
            for link, link_text in link_matches:
                # Resolve relative URLs
                if not link.startswith(('http://', 'https://')):
                    link = urljoin(url, link)
                
                link_lower = link.lower()
                link_text_lower = link_text.lower()
                
                # Skip certain types of links (but allow if they contain event keywords or eventdetail)
                skip_patterns = ['/contact', '/about', '/home$', '/news/', '/article/', 'mailto:', 'tel:', '#']
                should_skip = any(skip in link_lower for skip in skip_patterns)
                # Don't skip if it's clearly an event page (eventdetail, /event/, etc.)
                is_clear_event = 'eventdetail' in link_lower or '/event/' in link_lower or '/events/' in link_lower
                if should_skip and not is_clear_event and not any(kw in link_lower for kw in ['conference', 'workshop', 'seminar', 'webinar', 'forum']):
                    continue
                
                # Check if link looks like an event page
                event_indicators = ['/event/', '/events/', 'eventdetail', 'conference', 'workshop', 'seminar', 'webinar', 'forum']
                aggregator_indicators = ['/events?$', '/home$', '/calendar$', '/upcoming$']
                
                is_event_page = any(ind in link_lower for ind in event_indicators)
                is_aggregator = any(re.search(ind, link_lower) for ind in aggregator_indicators)
                
                # Also consider links that have event-related text even if URL doesn't
                has_event_text = any(kw in link_text_lower for kw in ['conference', 'workshop', 'seminar', 'webinar', 'forum', 'event', 'meeting'])
                
                if (is_event_page or has_event_text) and not is_aggregator:
                    score = 0
                    
                    # Score based on title match
                    if title_words:
                        # Check URL
                        url_matches = sum(1 for word in title_words if word in link_lower)
                        # Check link text (more important for matching)
                        text_matches = sum(1 for word in title_words if word in link_text_lower)
                        # Check surrounding context (50 chars around link)
                        link_pos = content_lower.find(link_lower)
                        if link_pos != -1:
                            context = content_lower[max(0, link_pos-50):min(len(content_lower), link_pos+len(link)+50)]
                            context_matches = sum(1 for word in title_words if word in context)
                            score = url_matches * 3 + text_matches * 2 + context_matches
                        else:
                            score = url_matches * 3 + text_matches * 2
                    else:
                        score = 1  # Default score if no title
                    
                    # Boost score for event-related keywords in URL
                    if any(kw in link_lower for kw in ['conference', 'workshop', 'seminar', 'webinar', 'forum']):
                        score += 3
                    
                    # Boost for eventdetail, /event/, /events/ patterns (highest priority)
                    if 'eventdetail' in link_lower:
                        score += 10  # eventdetail is a strong indicator
                    elif '/event/' in link_lower or '/events/' in link_lower:
                        score += 5
                    
                    # Boost if URL contains numeric ID (like eventdetail/3264530)
                    if re.search(r'\d{4,}', link_lower):  # 4+ digit number suggests event ID
                        score += 3
                    
                    scored_urls.append((score, link))
            
            # Sort by score (highest first) and return URLs
            scored_urls.sort(reverse=True, key=lambda x: x[0])
            return [url for score, url in scored_urls if score > 0]
            
        except Exception as e:
            print(f"  Error following URL {url}: {str(e)}")
            return []
    
    def find_direct_event_url(self, url: str, event_title: str = None, page_content: str = None, max_depth: int = 2) -> Optional[str]:
        """
        Find direct event URL from an aggregator/listing page.
        Can follow links up to max_depth levels deep.
        
        For listing pages (/events, /event-list, /calendar), this will:
        1. Extract all event links from the listing page
        2. Follow each link to the second level to get event details
        3. Return the best matching event detail URL
        
        Args:
            url: Potential aggregator/listing page URL
            event_title: Event title to match
            page_content: Optional pre-fetched page content
            max_depth: Maximum depth to follow links (default: 2, increased to 3 for listing pages)
            
        Returns:
            Direct event URL if found, None otherwise
        """
        # Check if URL is a generic page that should ALWAYS be followed
        url_lower = url.lower()
        generic_pages = ['/home', '/contact', '/about', '/events?', '/event-list', '/calendar']
        is_generic = any(page in url_lower for page in generic_pages)
        
        # If we have content, check if it's an aggregator
        if page_content:
            if not self.is_aggregator_page(url, page_content) and not is_generic:
                return None  # Not an aggregator, return as-is
        
        # If it's a generic page, ALWAYS try to find better URL
        if is_generic or not page_content:
            # Try to extract event links
            event_links = self.extract_event_links_from_page(url, event_title)
            
            if event_links:
                # If we found eventdetail URLs, return the best one immediately
                eventdetail_urls = [u for u in event_links if 'eventdetail' in u.lower()]
                if eventdetail_urls:
                    return eventdetail_urls[0]
                
                # If max_depth > 1, try following links deeper to extract event details
                if max_depth > 1 and event_links:
                    # For listing pages, try following multiple links to find the best match
                    # This allows us to go to second level and extract actual event details
                    for link in event_links[:5]:  # Try top 5 links
                        try:
                            response = self.session.get(link, timeout=self.timeout, allow_redirects=True)
                            if response.status_code == 200:
                                content = response.text
                                
                                # Check if this link is still an aggregator (needs deeper following)
                                if self.is_aggregator_page(link, content):
                                    # Follow one more level deep
                                    deeper_links = self.extract_event_links_from_page(link, event_title)
                                    if deeper_links:
                                        # Prioritize eventdetail URLs
                                        eventdetail_deeper = [u for u in deeper_links if 'eventdetail' in u.lower()]
                                        if eventdetail_deeper:
                                            return eventdetail_deeper[0]
                                        # If max_depth allows, return the best deeper link
                                        if max_depth > 2:
                                            return deeper_links[0]
                                
                                # If this link is already an event detail page, check if it matches the title
                                elif 'eventdetail' in link.lower() or '/event/' in link.lower():
                                    # This looks like an event detail page - check if it matches
                                    if event_title:
                                        # Check if title appears in content
                                        title_words = [w.lower() for w in event_title.split() if len(w) > 4]
                                        content_lower = content.lower()
                                        matches = sum(1 for word in title_words if word in content_lower[:2000])
                                        if matches >= 1:  # At least one keyword match
                                            return link
                                    else:
                                        # No title to match, return this eventdetail URL
                                        return link
                        except Exception:
                            continue  # Try next link if this one fails
                    
                    # If we didn't find a perfect match, return the best link from first level
                    return event_links[0]
                
                # Return the best match (first in list)
                return event_links[0]
        
        return None

