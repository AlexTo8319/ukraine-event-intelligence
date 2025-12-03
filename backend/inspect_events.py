"""Inspect events in database to identify potential issues."""
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient


def inspect_events():
    """Inspect events and show potential issues."""
    print("=" * 60)
    print("INSPECTING EVENTS IN DATABASE")
    print("=" * 60)
    print()
    
    try:
        db_client = DatabaseClient()
        all_events = db_client.get_events(limit=1000)
        
        print(f"Total events: {len(all_events)}")
        print()
        
        # Check for potential duplicates by title similarity
        print("Checking for potential duplicate titles...")
        titles = [e.get("event_title", "").lower().strip() for e in all_events]
        title_counts = Counter(titles)
        duplicates = {title: count for title, count in title_counts.items() if count > 1}
        
        if duplicates:
            print(f"  Found {len(duplicates)} titles appearing multiple times:")
            for title, count in list(duplicates.items())[:10]:
                print(f"    - '{title[:60]}...' ({count} times)")
        else:
            print("  No exact duplicate titles found")
        print()
        
        # Check for news-like titles
        print("Checking for news-like titles...")
        news_keywords = ["news", "article", "blog", "report", "analysis", "announcement"]
        event_keywords = ["conference", "workshop", "seminar", "webinar", "forum", "training", "meeting", "event"]
        
        news_like = []
        for event in all_events:
            title = event.get("event_title", "").lower()
            has_news = any(kw in title for kw in news_keywords)
            has_event = any(kw in title for kw in event_keywords)
            
            if has_news and not has_event:
                news_like.append(event)
        
        if news_like:
            print(f"  Found {len(news_like)} potentially news-like events:")
            for event in news_like[:10]:
                print(f"    - {event.get('event_title', '')[:70]}")
        else:
            print("  No news-like titles found")
        print()
        
        # Show sample events
        print("Sample events (first 10):")
        print("-" * 60)
        for i, event in enumerate(all_events[:10], 1):
            print(f"{i}. {event.get('event_title', 'N/A')}")
            print(f"   Date: {event.get('event_date', 'N/A')}")
            print(f"   URL: {event.get('url', 'N/A')[:60]}...")
            print(f"   Summary: {event.get('summary', 'N/A')[:60]}...")
            print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(inspect_events())



