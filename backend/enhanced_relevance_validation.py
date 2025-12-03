"""Enhanced validation with title-content matching and relevance checking."""
import sys
import os
from datetime import date, timedelta
from typing import List, Dict, Tuple
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.url_content_analyzer import URLContentAnalyzer
from agent.date_validator import DateValidator
from agent.url_follower import URLFollower

class EnhancedRelevanceValidator:
    """Enhanced validator that checks title-content matching and relevance."""
    
    def __init__(self):
        self.db_client = DatabaseClient()
        self.url_analyzer = URLContentAnalyzer()
        self.date_validator = DateValidator()
        self.url_follower = URLFollower()
        
        # Urban planning and recovery related keywords (VERY EXPANDED - keep anything that could be related)
        self.urban_keywords = [
            'urban', 'city', 'cities', 'planning', 'spatial', 'municipal', 'local government',
            'recovery', 'reconstruction', 'housing', 'infrastructure', 'development',
            'урбаністика', 'місто', 'планування', 'відбудова', 'житло', 'інфраструктура',
            'municipality', 'governance', 'community', 'resilience', 'sustainability',
            'digital', 'forum', 'sumy', 'capacity', 'building', 'decentralization',
            'green', 'sustainable', 'waste', 'management', 'energy', 'efficiency',
            'reform', 'eurointegration', 'public', 'officials', 'smart', 'building',
            'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'event',
            'ukraine', 'ukrainian', 'europe', 'partnership', 'cooperation',
            'investment', 'finance', 'funding', 'project', 'program', 'programme'
        ]
        
        # Only clearly irrelevant topics (VERY LIMITED - only remove if clearly not related)
        self.irrelevant_keywords = [
            'teacher education', 'pedagogy', 'teaching methods',  # Education (not urban)
            'spanish', 'latin american', 'language studies', 'literature',  # Language studies
            'biology', 'biotechnology', 'medical research', 'healthcare'  # Science/medical
        ]
        # NOTE: Removed 'war', 'military', 'defense', 'conflict' - these might be about recovery
    
    def check_title_content_match(self, title: str, url: str) -> Tuple[bool, str]:
        """
        Check if event title matches URL content.
        
        Returns:
            (matches: bool, reason: str)
        """
        try:
            response = self.url_analyzer.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                return True, "Could not check (HTTP error)"  # Don't reject on network errors
            
            content = response.text.lower()
            title_lower = title.lower()
            
            # Extract page title from HTML
            import re
            page_title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            page_title = page_title_match.group(1).lower() if page_title_match else ""
            
            # Extract h1 heading
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
            h1_text = h1_match.group(1).lower() if h1_match else ""
            
            # Check page title and h1 first (most reliable)
            page_text = f"{page_title} {h1_text}"
            
            # CRITICAL: Check for topic mismatches first (most important)
            title_topic = self._extract_topic(title_lower)
            content_topic = self._extract_topic(page_text + " " + content[:2000])  # Check title, h1, and first 2000 chars
            
            if title_topic and content_topic and title_topic != content_topic:
                # Specific topic mismatch - definitely wrong
                return False, f"Title topic '{title_topic}' doesn't match URL content topic '{content_topic}'"
            
            # Check for specific mismatches in page title/h1
            if 'urban' in title_lower or 'city' in title_lower or 'planning' in title_lower or 'studies' in title_lower:
                # Title is about urban planning/studies
                irrelevant_topics = ['spanish', 'latin american', 'arabic', 'islamic', 'language studies', 'teacher', 'education', 'pedagogy']
                page_has_irrelevant = any(topic in page_text for topic in irrelevant_topics)
                page_has_urban = 'urban' in page_text or 'city' in page_text or 'planning' in page_text
                
                if page_has_irrelevant and not page_has_urban:
                    irrelevant_found = [t for t in irrelevant_topics if t in page_text][0]
                    return False, f"Title is about urban studies but page title is about {irrelevant_found}"
            
            # Extract key words from title (exclude common words)
            title_words = [w for w in title_lower.split() if len(w) > 4 and w not in ['conference', 'international', 'forum', 'workshop', 'seminar', 'webinar', 'event', 'meeting', 'ukraine', 'december', 'studies']]
            
            # Check if title keywords appear in page title/h1 (most important)
            matches_in_title = 0
            for word in title_words[:5]:
                if word in page_text:
                    matches_in_title += 1
            
            # Check if title keywords appear in content
            matches_in_content = 0
            for word in title_words[:5]:
                if word in content[:3000]:  # Check first 3000 chars
                    matches_in_content += 1
            
            # If page title/h1 has no matches and content has few matches, it's likely wrong
            if matches_in_title == 0 and matches_in_content < 1 and len(title_words) >= 2:
                return False, f"No title keywords found in page title/h1, only {matches_in_content}/{len(title_words)} in content"
            
            return True, "Title matches content"
            
        except Exception as e:
            return True, f"Could not check: {str(e)}"  # Don't reject on errors
    
    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text."""
        text_lower = text.lower()
        
        # Check for specific topics
        if any(kw in text_lower for kw in ['teacher', 'education', 'pedagogy', 'teaching']):
            return 'education'
        if any(kw in text_lower for kw in ['spanish', 'latin american', 'language studies']):
            return 'language_studies'
        if any(kw in text_lower for kw in ['urban', 'city', 'planning', 'municipal']):
            return 'urban_planning'
        if any(kw in text_lower for kw in ['war', 'military', 'defense', 'conflict']):
            return 'war_policy'
        if any(kw in text_lower for kw in ['biology', 'biotechnology', 'medical']):
            return 'science'
        
        return None
    
    def check_relevance(self, title: str, summary: str, url: str) -> Tuple[bool, str]:
        """
        Check if event is relevant to urban planning focus.
        ULTRA CONSERVATIVE - keep almost everything, only remove clearly irrelevant.
        
        Returns:
            (is_relevant: bool, reason: str)
        """
        title_lower = title.lower()
        summary_lower = (summary or "").lower()
        combined_text = f"{title_lower} {summary_lower}"
        
        # FIRST: Check for clearly irrelevant topics (BEFORE checking urban keywords)
        # But be lenient - only remove if it's VERY clearly ONLY about that topic
        clearly_irrelevant_only = ['teacher education', 'pedagogy', 'spanish language', 'latin american studies', 'language studies', 'biotechnology research']
        event_types = ['forum', 'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'summit']
        location_keywords = ['ukraine', 'ukrainian', 'sumy', 'kyiv', 'lviv', 'kharkiv', 'odessa', 'europe']
        
        # Check if it's clearly about an irrelevant topic
        is_clearly_irrelevant = any(kw in combined_text for kw in clearly_irrelevant_only)
        if is_clearly_irrelevant:
            # But keep it if it has urban keywords, event type, or location keywords
            has_urban_keyword = any(kw in combined_text for kw in self.urban_keywords)
            has_event_type = any(et in title_lower for et in event_types)
            has_location = any(loc in combined_text for loc in location_keywords)
            
            # Only reject if it's clearly irrelevant AND has no urban keywords AND no event type AND no location
            if not has_urban_keyword and not has_event_type and not has_location:
                return False, f"Event is about irrelevant topic (not relevant to urban planning)"
            else:
                return True, f"Has urban keywords, event type, or location - keeping despite irrelevant topic mention"
        
        # SECOND: Check if it has urban planning or recovery keywords
        has_urban_keyword = any(kw in combined_text for kw in self.urban_keywords)
        
        # If it has urban/recovery keywords, it's ALWAYS relevant
        if has_urban_keyword:
            return True, "Relevant to urban planning/recovery (has related keywords)"
        
        # THIRD: Check for forum/conference/meeting/workshop - these are usually relevant
        if any(et in title_lower for et in event_types):
            return True, "Event type (forum/conference/workshop) - keeping (likely relevant)"
        
        # FOURTH: Check for location keywords (Ukraine, cities, regions) - might be relevant
        if any(loc in combined_text for loc in location_keywords):
            return True, "Location-related (Ukraine/Europe) - keeping (might be relevant)"
        
        # DEFAULT: Keep the event (be very conservative)
        # Most events are probably relevant or at least worth keeping
        return True, "Keeping event (not clearly irrelevant)"
    
    def validate_and_fix_all_events(self) -> Dict:
        """Validate all events with enhanced checks."""
        print("=" * 80)
        print("ENHANCED RELEVANCE VALIDATION")
        print("=" * 80)
        print()
        
        events = self.db_client.get_events(limit=1000)
        print(f"Found {len(events)} events to validate\n")
        
        stats = {
            "total": len(events),
            "fixed": 0,
            "removed": 0,
            "issues": []
        }
        
        for event in events:
            event_id = event.get("id")
            title = event.get("event_title", "")
            summary = event.get("summary", "")
            event_url = event.get("url", "")
            
            print(f"Validating: {title[:60]}...")
            
            # Check 1: Title-Content Matching (VERY conservative - only remove CLEAR mismatches)
            # Only check for eventdetail URLs (most reliable)
            if 'eventdetail' in event_url.lower():
                matches, match_reason = self.check_title_content_match(title, event_url)
                if not matches:
                    # ONLY remove if it's a CLEAR topic mismatch (urban vs language studies, education, etc.)
                    title_lower = title.lower()
                    if "urban" in title_lower or "city" in title_lower or "planning" in title_lower:
                        # Title is about urban planning
                        if ("spanish" in match_reason.lower() or "latin american" in match_reason.lower() or 
                            "arabic" in match_reason.lower() or "islamic" in match_reason.lower() or 
                            "teacher" in match_reason.lower() or "education" in match_reason.lower()):
                            # Clear mismatch - remove
                            print(f"  ❌ TITLE MISMATCH: {match_reason}")
                            self._remove_event(event_id, f"Title mismatch: {match_reason}")
                            stats["removed"] += 1
                            stats["issues"].append({"event": title, "issue": f"Title mismatch: {match_reason}", "action": "removed"})
                            continue
                    # For other cases, keep the event (might be valid)
                    print(f"  ⚠️  Title-Content match warning: {match_reason} (keeping - might be valid)")
            else:
                # For listing pages, try to find specific event (with increased depth)
                print(f"  ⚠️  Listing page detected, trying to find specific event...")
                # Use max_depth=3 for listing pages to go deeper
                max_depth = 3 if any(ind in event_url.lower() for ind in ['/events', '/event-list', '/calendar']) else 2
                better_url = self.url_follower.find_direct_event_url(event_url, title, max_depth=max_depth)
                if better_url and better_url != event_url:
                    # Verify the better URL matches the title
                    matches_better, match_reason = self.check_title_content_match(title, better_url)
                    if matches_better or 'eventdetail' in better_url.lower():
                        print(f"  ✅ Found matching eventdetail URL: {better_url[:60]}...")
                        self._update_event_url(event_id, better_url)
                        stats["fixed"] += 1
                        stats["issues"].append({"event": title, "issue": "URL improved to eventdetail", "action": "fixed"})
                    else:
                        print(f"  ⚠️  Better URL found but doesn't match title: {match_reason}")
                        # Check if it's a topic mismatch
                        if "doesn't match URL content topic" in match_reason:
                            print(f"  ❌ Topic mismatch, removing event")
                            self._remove_event(event_id, f"Topic mismatch: {match_reason}")
                            stats["removed"] += 1
                            stats["issues"].append({"event": title, "issue": f"Topic mismatch: {match_reason}", "action": "removed"})
                            continue
                else:
                    print(f"  ⚠️  Could not find specific event URL")
            
            # Check 2: Relevance to Urban Planning (ULTRA conservative - keep almost everything)
            is_relevant, relevance_reason = self.check_relevance(title, summary, event_url)
            if not is_relevant:
                # ONLY remove if it's VERY clearly about an irrelevant topic
                # AND has NO urban/recovery keywords
                # AND is not a forum/conference/workshop
                # AND is not Ukraine/Europe related
                title_lower = title.lower()
                summary_lower = (summary or "").lower()
                has_urban = any(kw in title_lower or kw in summary_lower for kw in self.urban_keywords)
                is_event_type = any(et in title_lower for et in ['forum', 'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'summit'])
                is_location = any(loc in title_lower or loc in summary_lower for loc in ['ukraine', 'ukrainian', 'sumy', 'kyiv', 'lviv', 'kharkiv', 'odessa', 'europe'])
                
                # Only remove if it's clearly irrelevant AND no urban keywords AND not an event type AND not location-related
                if not has_urban and not is_event_type and not is_location:
                    print(f"  ❌ NOT RELEVANT: {relevance_reason}")
                    self._remove_event(event_id, f"Not relevant: {relevance_reason}")
                    stats["removed"] += 1
                    stats["issues"].append({"event": title, "issue": f"Not relevant: {relevance_reason}", "action": "removed"})
                    continue
                else:
                    # Keep it - might be relevant
                    print(f"  ⚠️  {relevance_reason} (keeping - has urban keywords, event type, or location)")
            else:
                print(f"  ✅ {relevance_reason}")
            
            # Check 3: Try to improve URL if it's a listing page
            if 'eventdetail' not in event_url.lower() and ('/events' in event_url.lower() or '/event-list' in event_url.lower() or '/calendar' in event_url.lower()):
                print(f"  ⚠️  Listing page detected, trying to find specific event (crawling deeper)...")
                # Use max_depth=3 for listing pages to go deeper and extract event details
                better_url = self.url_follower.find_direct_event_url(event_url, title, max_depth=3)
                if better_url and better_url != event_url:
                    # Verify the better URL matches the title
                    matches_better, _ = self.check_title_content_match(title, better_url)
                    if matches_better:
                        print(f"  ✅ Found matching eventdetail URL: {better_url[:60]}...")
                        self._update_event_url(event_id, better_url)
                        stats["fixed"] += 1
                        stats["issues"].append({"event": title, "issue": "URL improved to eventdetail", "action": "fixed"})
                    else:
                        print(f"  ⚠️  Better URL found but doesn't match title, keeping original")
                else:
                    print(f"  ⚠️  Could not find specific event URL")
            
            print(f"  ✅ Valid event\n")
        
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total events: {stats['total']}")
        print(f"Events fixed: {stats['fixed']}")
        print(f"Events removed: {stats['removed']}")
        print(f"Valid events remaining: {stats['total'] - stats['removed']}")
        print()
        
        if stats["issues"]:
            print("Issues found and resolved:")
            for issue in stats["issues"]:
                print(f"  - {issue['event'][:50]}...: {issue['issue']} → {issue['action']}")
        
        return stats
    
    def _remove_event(self, event_id: str, reason: str):
        """Remove an event from the database."""
        try:
            self.db_client.client.table("events").delete().eq("id", event_id).execute()
            print(f"    Removed: {reason}")
        except Exception as e:
            print(f"    Error removing event: {e}")
    
    def _update_event_url(self, event_id: str, new_url: str):
        """Update event URL."""
        try:
            self.db_client.client.table("events").update({"url": new_url}).eq("id", event_id).execute()
            print(f"    Updated URL")
        except Exception as e:
            print(f"    Error updating URL: {e}")

if __name__ == "__main__":
    validator = EnhancedRelevanceValidator()
    validator.validate_and_fix_all_events()

