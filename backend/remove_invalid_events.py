"""Remove invalid events from database based on detailed analysis."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.models import Event

def remove_invalid_events():
    """Remove events that are programs, holidays, news, or duplicates."""
    db_client = DatabaseClient()
    events_data = db_client.get_all_events(limit=2000)
    events = [Event(**e) for e in events_data]
    
    print("=" * 80)
    print("REMOVING INVALID EVENTS")
    print("=" * 80)
    print(f"Total events in database: {len(events)}\n")
    
    events_to_remove = []
    reasons = {}
    
    # Track seen titles for duplicate detection
    seen_titles = {}
    
    for event_data, event in zip(events_data, events):
        title_lower = event.event_title.lower()
        summary_lower = (event.summary or "").lower()
        url_lower = event.url.lower()
        event_id = event_data.get("id")
        
        if not event_id:
            continue
        
        reason = None
        
        # 1. Check for program announcements
        program_keywords = [
            "compensation program", "housing program", "program for",
            "applications open", "can submit", "submitting applications",
            "program starts", "launch of", "housing vouchers"
        ]
        
        if any(kw in title_lower for kw in program_keywords):
            reason = "Program announcement (not an event)"
        elif any(kw in summary_lower for kw in ["can submit applications", "applications open", "apply for"]):
            if not any(ev in summary_lower for ev in ["conference", "workshop", "seminar", "webinar", "forum", "event"]):
                reason = "Program/application process (not an event)"
        
        # 2. Check for holidays/observances
        if not reason:
            holiday_keywords = ["day of", "день", "national day", "professional holiday"]
            event_keywords = ["conference", "workshop", "seminar", "webinar", "forum", "meeting", "event"]
            
            if any(hk in title_lower for hk in holiday_keywords):
                if not any(ek in title_lower for ek in event_keywords):
                    reason = "Holiday/observance (not an event)"
        
        # 3. Check for news articles
        if not reason:
            news_keywords = ["/news/", "/article/", "/blog/"]
            if any(nk in url_lower for nk in news_keywords):
                reason = "News article URL"
        
        # 4. Check for duplicates
        if not reason:
            title_normalized = event.event_title.lower().strip()
            if title_normalized in seen_titles:
                reason = f"Duplicate of: {seen_titles[title_normalized]['title']}"
            else:
                seen_titles[title_normalized] = {
                    "title": event.event_title,
                    "url": event.url,
                    "id": event_id
                }
        
        if reason:
            events_to_remove.append(event_id)
            reasons[event_id] = {
                "title": event.event_title,
                "url": event.url,
                "reason": reason
            }
    
    # Remove events
    print(f"Found {len(events_to_remove)} events to remove:\n")
    
    for event_id, info in reasons.items():
        print(f"  ❌ {info['title']}")
        print(f"     URL: {info['url']}")
        print(f"     Reason: {info['reason']}\n")
    
    if events_to_remove:
        print(f"\nRemoving {len(events_to_remove)} events from database...")
        
        # Delete events one by one
        removed_count = 0
        for event_id in events_to_remove:
            try:
                result = db_client.client.table("events").delete().eq("id", event_id).execute()
                if result.data:
                    removed_count += 1
            except Exception as e:
                print(f"  ⚠️  Error removing event {event_id}: {e}")
        
        print(f"\n✅ Removed {removed_count} events from database")
        print(f"   Remaining events: {len(events) - removed_count}")
    else:
        print("\n✅ No invalid events found to remove")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    remove_invalid_events()



