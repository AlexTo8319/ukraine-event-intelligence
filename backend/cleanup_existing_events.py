"""Clean up existing events using new filters (duplicates, news, URL validation)."""
import sys
import os
from typing import List, Dict
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.duplicate_detector import DuplicateDetector
from agent.url_validator import URLValidator
from agent.translator import Translator
from agent.date_validator import DateValidator


def cleanup_events():
    """Clean up existing events in the database."""
    print("=" * 60)
    print("CLEANING UP EXISTING EVENTS")
    print("=" * 60)
    print()
    
    try:
        db_client = DatabaseClient()
        duplicate_detector = DuplicateDetector(title_similarity_threshold=0.85, date_tolerance_days=0)
        url_validator = URLValidator(timeout=5, max_redirects=5)
        translator = Translator()
        date_validator = DateValidator()
        
        print("✅ Connected to database")
        print()
        
        # Get all events
        print("Fetching all events from database...")
        all_events = db_client.get_events(limit=1000)
        print(f"Found {len(all_events)} events")
        print()
        
        stats = {
            "total_events": len(all_events),
            "duplicates_removed": 0,
            "invalid_urls_removed": 0,
            "news_removed": 0,
            "past_events_removed": 0,
            "local_events_removed": 0,
            "news_urls_removed": 0,
            "translated": 0,
            "valid_events": 0,
            "errors": []
        }
        
        # Step 1: Remove duplicates (improved - also check by URL similarity)
        print("Step 1: Checking for duplicates...")
        seen_events = []
        duplicates_to_remove = []
        seen_urls = set()
        
        for event in all_events:
            is_duplicate = False
            event_url = event.get("url", "").lower().strip()
            
            # Check for exact URL duplicates
            if event_url in seen_urls:
                is_duplicate = True
                duplicates_to_remove.append(event)
                stats["duplicates_removed"] += 1
                print(f"  ⚠️  Duplicate URL: {event.get('event_title', '')[:60]}...")
            else:
                # Check for title+date duplicates
                for seen_event in seen_events:
                    if duplicate_detector.is_duplicate(
                        {
                            "event_title": event.get("event_title", ""),
                            "event_date": event.get("event_date", "")
                        },
                        {
                            "event_title": seen_event.get("event_title", ""),
                            "event_date": seen_event.get("event_date", "")
                        }
                    ):
                        is_duplicate = True
                        duplicates_to_remove.append(event)
                        stats["duplicates_removed"] += 1
                        print(f"  ⚠️  Duplicate title+date: {event.get('event_title', '')[:60]}...")
                        break
            
            if not is_duplicate:
                seen_events.append(event)
                if event_url:
                    seen_urls.add(event_url)
        
        print(f"  Found {stats['duplicates_removed']} duplicates")
        print()
        
        # Step 2: Check for past events (keep them, just log)
        # NOTE: Past events are NOT deleted - they are kept and hidden in the UI
        print("Step 2: Checking past events (kept for archive, not deleted)...")
        today = date.today()
        six_months_later = today + timedelta(days=180)
        
        past_events_count = 0
        future_events_to_remove = []
        for event in seen_events:
            event_date_str = event.get("event_date")
            if event_date_str:
                if isinstance(event_date_str, str):
                    try:
                        event_date = date.fromisoformat(event_date_str)
                    except:
                        continue
                else:
                    event_date = event_date_str
                
                # Only remove events that are TOO FAR in the future (likely errors)
                if event_date > six_months_later:
                    future_events_to_remove.append(event)
                    stats["past_events_removed"] += 1
                    print(f"  ⚠️  Too far future event (removing): {event.get('event_title', '')[:60]}... (date: {event_date})")
                elif event_date < today:
                    # Past events are KEPT for archive - just log them
                    past_events_count += 1
        
        print(f"  Found {past_events_count} past events (kept for archive)")
        print(f"  Found {len(future_events_to_remove)} too-far-future events (removing)")
        print()
        
        # Only remove events too far in the future, NOT past events
        events_to_check = [e for e in seen_events if e not in future_events_to_remove]
        
        # Step 3: Filter out news articles (improved detection)
        print("Step 3: Filtering out news articles...")
        news_to_remove = []
        
        for event in events_to_check:
            title = event.get("event_title", "").lower()
            summary = event.get("summary", "").lower() if event.get("summary") else ""
            url = event.get("url", "").lower()
            
            # Check for news indicators
            news_indicators = ["news", "article", "blog", "report", "analysis", "opinion", "announcement"]
            event_indicators = ["conference", "workshop", "seminar", "webinar", "forum", "training", "meeting", "event", "symposium", "summit"]
            
            # Check if it's a program/announcement launch (not an event)
            launch_phrases = ["starting", "launch", "beginning", "new program", "new housing", "compensation program"]
            if any(phrase in title or phrase in summary for phrase in launch_phrases):
                # Only remove if it doesn't have clear event indicators
                if not any(indicator in title for indicator in event_indicators):
                    news_to_remove.append(event)
                    stats["news_removed"] += 1
                    print(f"  ⚠️  Program announcement (not event): {event.get('event_title', '')[:60]}...")
                    continue
            
            # If title has news indicators but no event indicators, likely news
            has_news = any(indicator in title for indicator in news_indicators)
            has_event = any(indicator in title for indicator in event_indicators)
            
            if has_news and not has_event:
                news_to_remove.append(event)
                stats["news_removed"] += 1
                print(f"  ⚠️  News article: {event.get('event_title', '')[:60]}...")
                continue
            
            # Check summary for news-like content
            if summary:
                if any(phrase in summary for phrase in ["news article", "blog post", "reports that", "according to news", "starting december", "starting january"]):
                    # But allow if it's clearly an event
                    if not any(indicator in title for indicator in event_indicators):
                        news_to_remove.append(event)
                        stats["news_removed"] += 1
                        print(f"  ⚠️  News article (summary): {event.get('event_title', '')[:60]}...")
                        continue
            
            # Check URL for news sites
            news_domains = ["korrespondent.net", "freeradio.com.ua", "mindev.gov.ua/news"]
            if any(domain in url for domain in news_domains):
                # Only remove if it doesn't have clear event indicators
                if not any(indicator in title for indicator in event_indicators):
                    news_to_remove.append(event)
                    stats["news_removed"] += 1
                    print(f"  ⚠️  News site (not event page): {event.get('event_title', '')[:60]}...")
                    continue
        
        print(f"  Found {stats['news_removed']} news articles")
        print()
        
        # Remove news from events to check
        events_to_validate = [e for e in events_to_check if e not in news_to_remove]
        
        # Step 3.5: Filter out local/narrow events
        print("Step 3.5: Filtering out local/narrow events...")
        local_events_to_remove = []
        
        for event in events_to_validate:
            title = event.get("event_title", "").lower()
            
            # Check for local indicators
            local_indicators = [
                "засідання архітектурно", "засідання містобудівної ради",
                "council meeting", "обласна рада"
            ]
            major_indicators = ["conference", "forum", "summit", "конференція", "форум"]
            
            has_local = any(indicator in title for indicator in local_indicators)
            has_major = any(indicator in title for indicator in major_indicators)
            
            # Exclude if local but not major
            if has_local and not has_major:
                local_events_to_remove.append(event)
                stats["local_events_removed"] += 1
                print(f"  ⚠️  Local event: {event.get('event_title', '')[:60]}...")
        
        print(f"  Found {stats['local_events_removed']} local events")
        print()
        
        # Remove local events
        events_to_validate = [e for e in events_to_validate if e not in local_events_to_remove]
        
        # Step 3.6: Filter out news article URLs
        print("Step 3.6: Filtering out events with news article URLs...")
        news_url_events = []
        
        for event in events_to_validate:
            url = event.get("url", "").lower()
            if "/news/" in url or "/article/" in url or "/blog/" in url:
                news_url_events.append(event)
                stats["news_urls_removed"] += 1
                print(f"  ⚠️  News article URL: {event.get('event_title', '')[:60]}...")
        
        print(f"  Found {stats['news_urls_removed']} events with news URLs")
        print()
        
        # Remove news URL events
        events_to_validate = [e for e in events_to_validate if e not in news_url_events]
        
        # Step 4: Check for past events (validate dates) - KEEP past events for archive
        # NOTE: Past events are NOT deleted - they are kept and hidden in the UI
        print("Step 4: Checking for past events in URLs (kept for archive, not deleted)...")
        past_events_logged = 0
        
        for event in events_to_validate:
            url = event.get("url", "")
            event_date_str = event.get("event_date", "")
            
            if url and event_date_str:
                try:
                    if isinstance(event_date_str, str):
                        event_date = date.fromisoformat(event_date_str)
                    else:
                        event_date = event_date_str
                    
                    # Just log past events, don't remove them
                    if event_date < today:
                        past_events_logged += 1
                except Exception as e:
                    # Skip if date parsing fails
                    pass
        
        print(f"  Found {past_events_logged} past events (kept for archive)")
        print()
        
        # Past events are NOT removed - they stay in the database for archive viewing
        
        # Step 5: Translate Ukrainian events to English
        print("Step 5: Translating Ukrainian events to English...")
        events_to_update = []
        
        for event in events_to_validate:
            needs_update = False
            updates = {}
            
            title = event.get("event_title", "")
            if translator.is_ukrainian(title):
                translated = translator.translate(title, "event title")
                if translated != title:
                    updates["event_title"] = translated
                    needs_update = True
                    stats["translated"] += 1
                    print(f"  ✅ Translated: {title[:40]}... → {translated[:40]}...")
            
            organizer = event.get("organizer", "")
            if organizer and translator.is_ukrainian(organizer):
                translated = translator.translate(organizer, "organizer name")
                if translated != organizer:
                    updates["organizer"] = translated
                    needs_update = True
            
            summary = event.get("summary", "")
            if summary and translator.is_ukrainian(summary):
                translated = translator.translate(summary, "event description")
                if translated != summary:
                    updates["summary"] = translated
                    needs_update = True
            
            if needs_update:
                events_to_update.append((event, updates))
        
        print(f"  Translated {stats['translated']} events")
        print()
        
        # Step 6: Validate URLs
        print("Step 4: Validating URLs...")
        invalid_url_events = []
        
        # Collect URLs to validate
        urls_to_validate = []
        for event in events_to_validate:
            url = event.get("url")
            if url:
                urls_to_validate.append(url)
            reg_url = event.get("registration_url")
            if reg_url and reg_url != url:
                urls_to_validate.append(reg_url)
        
        print(f"  Validating {len(urls_to_validate)} URLs...")
        url_results = url_validator.validate_urls(urls_to_validate, check_accessibility=True)
        
        for event in events_to_validate:
            url = event.get("url")
            if url:
                is_valid, error = url_results.get(url, (False, "Not checked"))
                if not is_valid:
                    invalid_url_events.append(event)
                    stats["invalid_urls_removed"] += 1
                    print(f"  ⚠️  Invalid URL: {event.get('event_title', '')[:60]}... ({error})")
        
        print(f"  Found {stats['invalid_urls_removed']} events with invalid URLs")
        print()
        
        # Final valid events
        valid_events = [e for e in events_to_validate if e not in invalid_url_events]
        stats["valid_events"] = len(valid_events)
        
        # Step 7: Update translated events
        print("Step 7: Updating translated events in database...")
        updated_count = 0
        for event, updates in events_to_update:
            try:
                event_id = event.get("id")
                if event_id:
                    result = db_client.client.table("events").update(updates).eq("id", event_id).execute()
                    if result.data:
                        updated_count += 1
            except Exception as e:
                stats["errors"].append(f"Error updating event {event.get('event_title', 'Unknown')}: {str(e)}")
        
        print(f"  Updated {updated_count} events with translations")
        print()
        
        # Step 8: Delete invalid events (NOTE: past events are NOT deleted - kept for archive)
        print("Step 8: Removing invalid events from database...")
        events_to_delete = duplicates_to_remove + future_events_to_remove + news_to_remove + invalid_url_events + local_events_to_remove + news_url_events
        
        deleted_count = 0
        for event in events_to_delete:
            try:
                event_id = event.get("id")
                if event_id:
                    # Delete from database
                    result = db_client.client.table("events").delete().eq("id", event_id).execute()
                    if result.data:
                        deleted_count += 1
            except Exception as e:
                stats["errors"].append(f"Error deleting event {event.get('event_title', 'Unknown')}: {str(e)}")
        
        print(f"  Deleted {deleted_count} invalid events")
        print()
        
        # Print summary
        print("=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60)
        print(f"Total events processed: {stats['total_events']}")
        print(f"Duplicates removed: {stats['duplicates_removed']}")
        print(f"Past events removed: {stats['past_events_removed']}")
        print(f"News articles removed: {stats['news_removed']}")
        print(f"Local events removed: {stats['local_events_removed']}")
        print(f"News URL events removed: {stats['news_urls_removed']}")
        print(f"Invalid URLs removed: {stats['invalid_urls_removed']}")
        print(f"Events translated: {stats['translated']}")
        print(f"Valid events remaining: {stats['valid_events']}")
        print(f"Total removed: {deleted_count}")
        if stats['errors']:
            print(f"Errors: {len(stats['errors'])}")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
        print("=" * 60)
        print()
        print("✅ Cleanup complete!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(cleanup_events())

