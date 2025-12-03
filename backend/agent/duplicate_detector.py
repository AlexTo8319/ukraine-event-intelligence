"""Duplicate event detection using fuzzy matching."""
from typing import List, Dict, Optional
from datetime import date, timedelta
from difflib import SequenceMatcher
import re

# Common Ukrainian-English event title mappings for semantic duplicate detection
SEMANTIC_EQUIVALENTS = {
    "енергоефективності": ["energy efficiency", "energy saving"],
    "енергоменеджер": ["energy manager", "energy management"],
    "відбудова": ["recovery", "reconstruction", "rebuild"],
    "форум": ["forum"],
    "конференція": ["conference"],
    "семінар": ["seminar", "workshop"],
    "тиждень": ["week"],
    "деокуповані": ["de-occupied", "liberated"],
    "громад": ["communities", "community"],
    "містобудування": ["urban planning", "urban development", "city planning"],
    "житло": ["housing"],
    "будівництво": ["construction", "building"],
}


class DuplicateDetector:
    """Detects duplicate events using fuzzy matching on title and date."""
    
    def __init__(self, title_similarity_threshold: float = 0.60, date_tolerance_days: int = 0):
        """
        Initialize duplicate detector.
        
        Args:
            title_similarity_threshold: Minimum similarity ratio (0-1) to consider titles similar (default: 0.60 for aggressive duplicate detection)
            date_tolerance_days: Maximum days difference to consider same event (default: 0 = exact match)
        """
        self.title_similarity_threshold = title_similarity_threshold
        self.date_tolerance_days = date_tolerance_days
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison (lowercase, remove extra spaces, normalize spelling)."""
        if not title:
            return ""
        # Convert to lowercase
        title = title.lower()
        # Normalize common spelling variations
        title = title.replace('kreator', 'creator')  # Ukrainian transliteration
        title = title.replace('-bud', ' bud')  # Normalize separators
        # Remove extra whitespace
        title = " ".join(title.split())
        # Remove common words that don't affect uniqueness
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "year"}
        words = [w for w in title.split() if w not in stop_words]
        return " ".join(words)
    
    def title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def is_semantic_duplicate(self, title1: str, title2: str) -> bool:
        """
        Check if two titles are semantic duplicates (same event in different languages).
        Detects when Ukrainian title matches English equivalent.
        """
        t1_lower = title1.lower()
        t2_lower = title2.lower()
        
        # Check if one has Ukrainian chars and other doesn't
        ukr_chars = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'
        t1_has_ukr = any(c in t1_lower for c in ukr_chars)
        t2_has_ukr = any(c in t2_lower for c in ukr_chars)
        
        # Both same language - use regular similarity
        if t1_has_ukr == t2_has_ukr:
            return False
        
        # One Ukrainian, one English - check semantic equivalents
        ukr_title = t1_lower if t1_has_ukr else t2_lower
        eng_title = t2_lower if t1_has_ukr else t1_lower
        
        matches = 0
        total_checks = 0
        
        for ukr_word, eng_equivalents in SEMANTIC_EQUIVALENTS.items():
            if ukr_word in ukr_title:
                total_checks += 1
                if any(eng in eng_title for eng in eng_equivalents):
                    matches += 1
        
        # Consider semantic duplicate if at least 2 semantic matches
        return matches >= 2
    
    def dates_match(self, date1: date, date2: date) -> bool:
        """Check if two dates are within tolerance."""
        if date1 == date2:
            return True
        
        if self.date_tolerance_days > 0:
            diff = abs((date1 - date2).days)
            return diff <= self.date_tolerance_days
        
        return False
    
    def is_duplicate(self, event1: Dict, event2: Dict) -> bool:
        """
        Check if two events are duplicates.
        
        Args:
            event1: First event dict (must have 'event_title' and 'event_date')
            event2: Second event dict (must have 'event_title' and 'event_date')
            
        Returns:
            True if events are considered duplicates
        """
        title1 = event1.get("event_title", "")
        title2 = event2.get("event_title", "")
        
        # Parse dates
        date1 = event1.get("event_date")
        date2 = event2.get("event_date")
        
        if isinstance(date1, str):
            date1 = date.fromisoformat(date1)
        if isinstance(date2, str):
            date2 = date.fromisoformat(date2)
        
        if not date1 or not date2:
            return False
        
        # Check date match first (faster)
        if not self.dates_match(date1, date2):
            return False
        
        # Check title similarity (text-based)
        similarity = self.title_similarity(title1, title2)
        if similarity >= self.title_similarity_threshold:
            return True
        
        # Check semantic similarity (Ukrainian/English equivalent)
        if self.is_semantic_duplicate(title1, title2):
            return True
        
        return False
    
    def find_duplicates(self, new_events: List[Dict], existing_events: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Find duplicates between new events and existing events, AND within new events.
        
        Args:
            new_events: List of new event dicts to check
            existing_events: List of existing event dicts from database
            
        Returns:
            Dict with 'duplicates' (list of duplicate new events) and 'unique' (list of unique new events)
        """
        duplicates = []
        unique = []
        seen_urls = set()  # Track URLs we've already accepted
        
        # Also get URLs from existing events
        existing_urls = {e.get("url", "") for e in existing_events if e.get("url")}
        
        for new_event in new_events:
            new_url = new_event.get("url", "")
            is_dup = False
            
            # Check 1: Exact URL match with existing events
            if new_url in existing_urls:
                is_dup = True
                duplicates.append(new_event)
                continue
            
            # Check 2: Exact URL match with already-accepted new events
            if new_url in seen_urls:
                is_dup = True
                duplicates.append(new_event)
                continue
            
            # Check 3: Title/date similarity with existing events
            for existing_event in existing_events:
                if self.is_duplicate(new_event, existing_event):
                    is_dup = True
                    duplicates.append(new_event)
                    break
            
            if is_dup:
                continue
            
            # Check 4: Title/date similarity with already-accepted new events
            for accepted_event in unique:
                if self.is_duplicate(new_event, accepted_event):
                    is_dup = True
                    duplicates.append(new_event)
                    break
            
            if not is_dup:
                unique.append(new_event)
                seen_urls.add(new_url)
        
        return {
            "duplicates": duplicates,
            "unique": unique
        }



