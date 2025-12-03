"""Fix the event date for the Online Forum event."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.url_content_analyzer import URLContentAnalyzer

def fix_event_date():
    """Fix the event date for the Online Forum event."""
    print("=" * 60)
    print("FIXING EVENT DATE FOR ONLINE FORUM")
    print("=" * 60)
    print()
    
    db_client = DatabaseClient()
    url_analyzer = URLContentAnalyzer()
    
    # Get the event
    events = db_client.get_events(limit=1000)
    
    target_event = None
    for event in events:
        if "Information Rights" in event.get("event_title", "") or "інформаційних прав" in event.get("event_title", "").lower():
            target_event = event
            break
    
    if not target_event:
        print("❌ Event not found in database")
        return
    
    print(f"Found event: {target_event.get('event_title')}")
    print(f"Current date: {target_event.get('event_date')}")
    print()
    
    # Get the URL and analyze it
    event_url = target_event.get("url")
    if not event_url:
        print("❌ No URL found for event")
        return
    
    print(f"Analyzing URL: {event_url[:60]}...")
    analysis = url_analyzer.analyze_url(event_url, target_event.get("event_title"))
    
    extracted_date = analysis.get("extracted_date")
    if not extracted_date:
        print("❌ Could not extract date from URL content")
        return
    
    print(f"Extracted date from URL: {extracted_date}")
    print()
    
    # Check if date needs to be updated
    current_date_str = target_event.get("event_date")
    if current_date_str:
        try:
            current_date = date.fromisoformat(current_date_str)
            if current_date == extracted_date:
                print("✅ Date is already correct!")
                return
            else:
                print(f"⚠️  Date mismatch: Current={current_date}, Extracted={extracted_date}")
        except ValueError:
            print(f"⚠️  Could not parse current date: {current_date_str}")
    
    # Update the event
    print("Updating event date...")
    updated_event = target_event.copy()
    updated_event["event_date"] = extracted_date.isoformat()
    
    result = db_client.upsert_event(updated_event)
    
    if result:
        print(f"✅ Event date updated to: {extracted_date}")
        print(f"   Event ID: {result.get('id')}")
    else:
        print("❌ Failed to update event")

if __name__ == "__main__":
    fix_event_date()


