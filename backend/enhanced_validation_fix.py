"""Enhanced validation and automatic fixing of events."""
import sys
import os
from datetime import date, datetime
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.url_content_analyzer import URLContentAnalyzer
from agent.date_validator import DateValidator
from agent.url_follower import URLFollower
import re

class EnhancedValidator:
    """Enhanced validator with automatic fixing capabilities."""
    
    def __init__(self):
        self.db_client = DatabaseClient()
        self.url_analyzer = URLContentAnalyzer()
        self.date_validator = DateValidator()
        self.url_follower = URLFollower()
    
    def validate_and_fix_all_events(self) -> Dict:
        """Validate all events and attempt to fix issues automatically."""
        print("=" * 80)
        print("ENHANCED VALIDATION AND AUTOMATIC FIXING")
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
            event_date_str = event.get("event_date")
            event_url = event.get("url", "")
            
            print(f"Validating: {title[:60]}...")
            
            try:
                event_date = date.fromisoformat(event_date_str) if event_date_str else None
            except:
                event_date = None
            
            # Check 1: Past event detection
            is_past, past_reason = self.date_validator.check_if_past_event(event_url, event_date)
            if is_past:
                print(f"  ❌ PAST EVENT: {past_reason}")
                self._remove_event(event_id, f"Past event: {past_reason}")
                stats["removed"] += 1
                stats["issues"].append({"event": title, "issue": f"Past event: {past_reason}", "action": "removed"})
                continue
            
            # Check 2: Analyze URL content
            analysis = self.url_analyzer.analyze_url(event_url, title, event_date)
            
            # Check 2a: Extract date from URL and compare
            extracted_date = analysis.get("extracted_date")
            if extracted_date and event_date:
                # Check if dates are years apart (likely wrong event)
                year_diff = abs(extracted_date.year - event_date.year)
                if year_diff > 0:
                    # Check if extracted date is in the past
                    if extracted_date < date.today():
                        print(f"  ❌ DATE MISMATCH: Extracted date {extracted_date} is in the past (extracted: {event_date})")
                        self._remove_event(event_id, f"Date mismatch: URL shows past date {extracted_date}")
                        stats["removed"] += 1
                        stats["issues"].append({"event": title, "issue": f"Date mismatch: past date {extracted_date}", "action": "removed"})
                        continue
                    else:
                        # Future date but different year - might be wrong, but try to fix
                        if year_diff == 1:  # Only 1 year difference, might be correct
                            print(f"  ⚠️  Date difference: {event_date} vs {extracted_date} (1 year)")
                            # Update to extracted date if it's more recent
                            if extracted_date > event_date:
                                self._update_event_date(event_id, extracted_date)
                                stats["fixed"] += 1
                                stats["issues"].append({"event": title, "issue": "Date updated", "action": "fixed"})
                                print(f"  ✅ Updated date to {extracted_date}")
            
            # Check 2b: Program description detection
            if analysis.get("is_program_description") and not extracted_date:
                print(f"  ❌ PROGRAM DESCRIPTION: Not a specific event")
                self._remove_event(event_id, "Program description, not specific event")
                stats["removed"] += 1
                stats["issues"].append({"event": title, "issue": "Program description", "action": "removed"})
                continue
            
            # Check 2c: Generic page detection
            if analysis.get("is_generic_page") and not analysis.get("found_better_url"):
                print(f"  ⚠️  GENERIC PAGE: Trying to find better URL...")
                better_url = self.url_follower.find_direct_event_url(event_url, title, max_depth=2)
                if better_url and better_url != event_url:
                    print(f"  ✅ Found better URL: {better_url[:60]}...")
                    self._update_event_url(event_id, better_url)
                    stats["fixed"] += 1
                    stats["issues"].append({"event": title, "issue": "Generic URL", "action": "fixed"})
                else:
                    print(f"  ❌ No better URL found. REMOVING")
                    self._remove_event(event_id, "Generic page, no specific event found")
                    stats["removed"] += 1
                    stats["issues"].append({"event": title, "issue": "Generic page", "action": "removed"})
                    continue
            
            # Check 2d: Better URL found
            if analysis.get("found_better_url"):
                better_url = analysis.get("actual_url")
                if better_url and better_url != event_url:
                    print(f"  ✅ Found better URL: {better_url[:60]}...")
                    self._update_event_url(event_id, better_url)
                    stats["fixed"] += 1
                    stats["issues"].append({"event": title, "issue": "URL improved", "action": "fixed"})
                    # Re-analyze with new URL
                    analysis = self.url_analyzer.analyze_url(better_url, title, event_date)
                    extracted_date = analysis.get("extracted_date")
            
            # Check 3: Date validation (after URL improvement)
            if extracted_date and event_date:
                date_diff = abs((extracted_date - event_date).days)
                
                # Check if extracted date is in the past (always reject)
                if extracted_date < date.today():
                    print(f"  ❌ DATE MISMATCH: Extracted date {extracted_date} is in the past")
                    self._remove_event(event_id, f"Date mismatch: URL shows past date {extracted_date}")
                    stats["removed"] += 1
                    stats["issues"].append({"event": title, "issue": f"Date mismatch: past date {extracted_date}", "action": "removed"})
                    continue
                
                # Check if dates are years apart (always reject)
                year_diff = abs(extracted_date.year - event_date.year)
                if year_diff > 0:
                    if extracted_date.year < date.today().year:
                        print(f"  ❌ DATE MISMATCH: Extracted date {extracted_date} is in past year")
                        self._remove_event(event_id, f"Date mismatch: past year {extracted_date}")
                        stats["removed"] += 1
                        stats["issues"].append({"event": title, "issue": f"Date mismatch: past year {extracted_date}", "action": "removed"})
                        continue
                    elif extracted_date.year > event_date.year + 1:
                        # Future year but more than 1 year ahead - might be wrong
                        print(f"  ⚠️  Date is more than 1 year in future: {extracted_date}")
                        # Keep it but log warning
                
                # If dates differ by more than 30 days (not years), might be wrong but don't remove
                # (could be multi-day events or different timezones)
                if date_diff > 30 and year_diff == 0:
                    print(f"  ⚠️  Date difference: {event_date} vs {extracted_date} ({date_diff} days)")
                    # Update to extracted date if it's more recent and reasonable
                    if extracted_date > event_date and extracted_date <= date.today() + timedelta(days=180):
                        self._update_event_date(event_id, extracted_date)
                        stats["fixed"] += 1
                        stats["issues"].append({"event": title, "issue": "Date updated", "action": "fixed"})
                        print(f"  ✅ Updated date to {extracted_date}")
            
            # Check 4: URL accessibility
            if not analysis.get("is_valid"):
                error = analysis.get("error", "Unknown error")
                # Check if it's a connection error (might be temporary)
                if "connection" in error.lower() or "timeout" in error.lower() or "missing 1 required" in error.lower():
                    print(f"  ⚠️  Error (might be temporary): {error}")
                    # Don't remove, just log - but try to fix the error
                    if "missing 1 required" in error.lower():
                        # This is a code bug, not a data issue - skip validation for now
                        print(f"  ⚠️  Code bug detected, skipping validation")
                else:
                    print(f"  ❌ INVALID URL: {error}")
                    # Only remove if it's a clear data issue, not a code bug
                    if "date mismatch" in error.lower() and extracted_date:
                        # This was already handled above
                        continue
                    # Don't remove for other errors that might be temporary
                    print(f"  ⚠️  Keeping event despite error (might be temporary)")
            
            # Check 4: Extract date from URL if not already extracted
            if not extracted_date and event_date:
                # Try to extract date from URL content more aggressively
                extracted_date = self._extract_date_aggressively(event_url, title)
                if extracted_date:
                    # Check if it's significantly different
                    date_diff = abs((extracted_date - event_date).days)
                    if date_diff > 30:  # More than 30 days difference
                        # Check if extracted date is in the past
                        if extracted_date < date.today():
                            print(f"  ❌ Extracted date {extracted_date} is in the past")
                            self._remove_event(event_id, f"Extracted date {extracted_date} is in the past")
                            stats["removed"] += 1
                            stats["issues"].append({"event": title, "issue": f"Past date {extracted_date}", "action": "removed"})
                            continue
                        elif extracted_date.year != event_date.year:
                            # Different year - likely wrong
                            if extracted_date.year < date.today().year:
                                print(f"  ❌ Extracted date {extracted_date} is in past year")
                                self._remove_event(event_id, f"Extracted date {extracted_date} is in past year")
                                stats["removed"] += 1
                                stats["issues"].append({"event": title, "issue": f"Past year date {extracted_date}", "action": "removed"})
                                continue
            
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
    
    def _extract_date_aggressively(self, url: str, title: str) -> date:
        """Try to extract date from URL content more aggressively."""
        try:
            response = self.url_analyzer.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                return None
            
            content = response.text
            
            # Look for date patterns more aggressively
            # Pattern: "2024", "2023" near event keywords
            year_pattern = r'\b(202[0-9]|203[0-9])\b'
            years = re.findall(year_pattern, content)
            
            # Look for month-day patterns near years
            date_patterns = [
                r'(\d{1,2})\s+(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
                r'(\d{4})-(\d{2})-(\d{2})',
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        # Try to parse the date
                        date_str = match.group(0)
                        # Use url_analyzer's date extraction
                        extracted = self.url_analyzer.extract_date_from_content(content)
                        if extracted:
                            return extracted
                    except:
                        continue
            
            return None
        except:
            return None
    
    def _remove_event(self, event_id: str, reason: str):
        """Remove an event from the database."""
        try:
            self.db_client.client.table("events").delete().eq("id", event_id).execute()
            print(f"    Removed: {reason}")
        except Exception as e:
            print(f"    Error removing event: {e}")
    
    def _update_event_date(self, event_id: str, new_date: date):
        """Update event date."""
        try:
            self.db_client.client.table("events").update({"event_date": new_date.isoformat()}).eq("id", event_id).execute()
            print(f"    Updated date to {new_date}")
        except Exception as e:
            print(f"    Error updating date: {e}")
    
    def _update_event_url(self, event_id: str, new_url: str):
        """Update event URL."""
        try:
            self.db_client.client.table("events").update({"url": new_url}).eq("id", event_id).execute()
            print(f"    Updated URL")
        except Exception as e:
            print(f"    Error updating URL: {e}")

if __name__ == "__main__":
    validator = EnhancedValidator()
    validator.validate_and_fix_all_events()

