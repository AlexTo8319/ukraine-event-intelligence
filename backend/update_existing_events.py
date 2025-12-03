"""Update existing events with new search logic (URL following, translation, validation)."""
import sys
import os
from typing import List, Dict
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.llm_processor import LLMProcessor
from agent.url_follower import URLFollower
from agent.translator import Translator
from agent.date_validator import DateValidator
from agent.url_validator import URLValidator
from agent.url_content_analyzer import URLContentAnalyzer


def update_events():
    """Update existing events with new logic."""
    print("=" * 60)
    print("UPDATING EXISTING EVENTS WITH NEW LOGIC")
    print("=" * 60)
    print()
    
    try:
        db_client = DatabaseClient()
        llm_processor = LLMProcessor()
        url_follower = URLFollower()
        translator = Translator()
        date_validator = DateValidator()
        url_validator = URLValidator()
        url_analyzer = URLContentAnalyzer()
        
        print("✅ Connected to database and initialized processors")
        print()
        
        # Get all events
        print("Fetching all events from database...")
        all_events = db_client.get_events(limit=1000)
        print(f"Found {len(all_events)} events")
        print()
        
        stats = {
            "total_events": len(all_events),
            "updated_urls": 0,
            "translated": 0,
            "removed_past": 0,
            "removed_invalid_urls": 0,
            "removed_local": 0,
            "removed_news_urls": 0,
            "updated": 0,
            "errors": []
        }
        
        events_to_update = []
        events_to_remove = []
        
        for i, event in enumerate(all_events, 1):
            event_id = event.get("id")
            event_title = event.get("event_title", "")
            event_url = event.get("url", "")
            
            print(f"[{i}/{len(all_events)}] Processing: {event_title[:60]}...")
            
            updates = {}
            should_remove = False
            remove_reason = None
            
            # Step 1: Analyze URL content to find better URL and validate date
            if event_url:
                print(f"  Analyzing URL: {event_url[:60]}...")
                
                try:
                    analysis = url_analyzer.analyze_url(event_url, event_title, None)
                    
                    # Check if found better URL
                    if analysis.get("found_better_url"):
                        better_url = analysis["actual_url"]
                        updates["url"] = better_url
                        if not event.get("registration_url") or event.get("registration_url") == event_url:
                            updates["registration_url"] = better_url
                        stats["updated_urls"] += 1
                        print(f"  ✅ Found better URL in content: {better_url[:60]}...")
                    
                    # Check if URL is aggregator and try to follow
                    if not analysis.get("found_better_url"):
                        content = analysis.get("content", "")
                        if content and url_follower.is_aggregator_page(event_url, content):
                            print(f"  ⚠️  Aggregator page detected, following links...")
                            direct_url = url_follower.find_direct_event_url(event_url, event_title, content)
                            if direct_url and direct_url != event_url:
                                updates["url"] = direct_url
                                if not event.get("registration_url") or event.get("registration_url") == event_url:
                                    updates["registration_url"] = direct_url
                                stats["updated_urls"] += 1
                                print(f"  ✅ Found direct URL: {direct_url[:60]}...")
                    
                    # Extract and update date if found in URL content
                    extracted_date = analysis.get("extracted_date")
                    if extracted_date:
                        event_date_str = event.get("event_date", "")
                        if event_date_str:
                            try:
                                if isinstance(event_date_str, str):
                                    current_date = date.fromisoformat(event_date_str)
                                else:
                                    current_date = event_date_str
                                
                                date_diff = abs((extracted_date - current_date).days)
                                if date_diff > 1 and date_diff <= 7:  # Significant but reasonable difference
                                    updates["event_date"] = extracted_date.isoformat()
                                    print(f"  ✅ Updated date: {current_date} → {extracted_date}")
                            except:
                                pass
                                
                except Exception as e:
                    print(f"  ⚠️  Could not analyze URL: {str(e)[:50]}")
            
            # Step 2: Check if event is in past
            event_date_str = event.get("event_date")
            if event_date_str and event_url:
                try:
                    if isinstance(event_date_str, str):
                        event_date = date.fromisoformat(event_date_str)
                    else:
                        event_date = event_date_str
                    
                    is_past, reason = date_validator.check_if_past_event(event_url, event_date)
                    if is_past:
                        should_remove = True
                        remove_reason = f"Past event: {reason}"
                        stats["removed_past"] += 1
                        print(f"  ❌ {remove_reason}")
                except Exception as e:
                    pass
            
            # Step 3: Check if URL is news article
            if event_url and not should_remove:
                url_lower = event_url.lower()
                if "/news/" in url_lower or "/article/" in url_lower or "/blog/" in url_lower:
                    should_remove = True
                    remove_reason = "News article URL"
                    stats["removed_news_urls"] += 1
                    print(f"  ❌ {remove_reason}")
            
            # Step 4: Check if local event
            if not should_remove:
                title_lower = event_title.lower()
                local_indicators = [
                    "засідання архітектурно", "засідання містобудівної ради",
                    "council meeting", "обласна рада"
                ]
                major_indicators = ["conference", "forum", "summit", "конференція", "форум"]
                
                has_local = any(indicator in title_lower for indicator in local_indicators)
                has_major = any(indicator in title_lower for indicator in major_indicators)
                
                if has_local and not has_major:
                    should_remove = True
                    remove_reason = "Local/narrow event"
                    stats["removed_local"] += 1
                    print(f"  ❌ {remove_reason}")
            
            # Step 5: Validate URL accessibility
            if event_url and not should_remove:
                is_valid, error = url_validator.check_url_accessibility(event_url)
                if not is_valid:
                    should_remove = True
                    remove_reason = f"Invalid URL: {error}"
                    stats["removed_invalid_urls"] += 1
                    print(f"  ❌ {remove_reason}")
            
            # Step 6: Translate if needed
            if not should_remove:
                # Translate title
                if translator.is_ukrainian(event_title):
                    translated = translator.translate(event_title, "event title")
                    if translated != event_title:
                        updates["event_title"] = translated
                        stats["translated"] += 1
                        print(f"  ✅ Translated title: {translated[:50]}...")
                
                # Translate organizer
                organizer = event.get("organizer", "")
                if organizer and translator.is_ukrainian(organizer):
                    translated = translator.translate(organizer, "organizer name")
                    if translated != organizer:
                        updates["organizer"] = translated
                
                # Translate summary
                summary = event.get("summary", "")
                if summary and translator.is_ukrainian(summary):
                    translated = translator.translate(summary, "event description")
                    if translated != summary:
                        updates["summary"] = translated
            
            # Step 7: Mark for removal or update
            if should_remove:
                events_to_remove.append((event_id, remove_reason))
            elif updates:
                events_to_update.append((event_id, updates))
                stats["updated"] += 1
                print(f"  ✅ Will update with {len(updates)} changes")
            
            print()
        
        # Step 8: Remove invalid events
        print("=" * 60)
        print("REMOVING INVALID EVENTS")
        print("=" * 60)
        removed_count = 0
        for event_id, reason in events_to_remove:
            try:
                result = db_client.client.table("events").delete().eq("id", event_id).execute()
                if result.data:
                    removed_count += 1
                    print(f"✅ Removed: {reason}")
            except Exception as e:
                stats["errors"].append(f"Error removing event {event_id}: {str(e)}")
        
        print(f"\nRemoved {removed_count} events")
        print()
        
        # Step 9: Update valid events
        print("=" * 60)
        print("UPDATING EVENTS")
        print("=" * 60)
        updated_count = 0
        for event_id, updates in events_to_update:
            try:
                result = db_client.client.table("events").update(updates).eq("id", event_id).execute()
                if result.data:
                    updated_count += 1
                    print(f"✅ Updated event ID: {event_id}")
            except Exception as e:
                stats["errors"].append(f"Error updating event {event_id}: {str(e)}")
        
        print(f"\nUpdated {updated_count} events")
        print()
        
        # Print summary
        print("=" * 60)
        print("UPDATE SUMMARY")
        print("=" * 60)
        print(f"Total events processed: {stats['total_events']}")
        print(f"URLs improved: {stats['updated_urls']}")
        print(f"Events translated: {stats['translated']}")
        print(f"Events updated: {stats['updated']}")
        print(f"Past events removed: {stats['removed_past']}")
        print(f"News URL events removed: {stats['removed_news_urls']}")
        print(f"Local events removed: {stats['removed_local']}")
        print(f"Invalid URL events removed: {stats['removed_invalid_urls']}")
        print(f"Total removed: {removed_count}")
        if stats['errors']:
            print(f"Errors: {len(stats['errors'])}")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
        print("=" * 60)
        print()
        print("✅ Update complete!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(update_events())

