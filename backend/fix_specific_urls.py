"""Fix specific URLs that are known to be wrong."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.url_follower import URLFollower

def fix_specific_urls():
    """Fix specific URLs that are known to be wrong."""
    print("=" * 80)
    print("FIXING SPECIFIC URLS")
    print("=" * 80)
    print()
    
    db = DatabaseClient()
    url_follower = URLFollower()
    
    events = db.get_events(limit=1000)
    
    # Fix 1: International Conference on Teacher Education
    for event in events:
        if 'Teacher Education' in event.get('event_title', ''):
            print(f"Fixing: {event.get('event_title')}")
            print(f"Current URL: {event.get('url')}")
            
            # The correct eventdetail URL should be found
            # Try to find it from the listing page
            listing_url = 'https://conferenceineurope.net/ukraine'
            better_url = url_follower.find_direct_event_url(listing_url, event.get('event_title'), max_depth=2)
            
            if better_url and 'eventdetail' in better_url.lower():
                print(f"Found better URL: {better_url}")
                db.client.table("events").update({"url": better_url}).eq("id", event.get("id")).execute()
                print("✅ Fixed URL\n")
            else:
                print("⚠️  Could not find better URL\n")
    
    # Fix 2: Urban studies Conferences - check if URL is wrong
    for event in events:
        if 'Urban studies Conferences' in event.get('event_title', ''):
            print(f"Checking: {event.get('event_title')}")
            current_url = event.get('url')
            print(f"Current URL: {current_url}")
            
            # Check if this is the wrong URL (Spanish/Latin American Studies)
            if '3287250' in current_url:
                print("❌ This is the wrong URL (Spanish/Latin American Studies)")
                print("Trying to find correct urban studies event...")
                
                # Try to find correct event from listing
                listing_url = 'https://allconferencealert.net/ukraine'
                better_url = url_follower.find_direct_event_url(listing_url, 'urban studies ukraine', max_depth=2)
                
                if better_url and better_url != current_url:
                    print(f"Found better URL: {better_url}")
                    db.client.table("events").update({"url": better_url}).eq("id", event.get("id")).execute()
                    print("✅ Fixed URL\n")
                else:
                    print("⚠️  Could not find correct URL, removing event")
                    db.client.table("events").delete().eq("id", event.get("id")).execute()
                    print("✅ Removed\n")
            else:
                print("✅ URL seems correct\n")
    
    # Fix 3: The Forum: Europe in a Time of War - should be removed (not relevant)
    for event in events:
        if 'Europe in a Time of War' in event.get('event_title', ''):
            print(f"Removing: {event.get('event_title')}")
            print("Reason: Not relevant to urban planning (war/policy focus)")
            db.client.table("events").delete().eq("id", event.get("id")).execute()
            print("✅ Removed\n")

if __name__ == "__main__":
    fix_specific_urls()


