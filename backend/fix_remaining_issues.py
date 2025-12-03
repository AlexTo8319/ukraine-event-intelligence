"""Fix remaining specific issues."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient

def fix_remaining_issues():
    """Fix remaining specific issues."""
    db_client = DatabaseClient()
    
    print("=" * 80)
    print("FIXING REMAINING ISSUES")
    print("=" * 80)
    
    # Get all events
    events_data = db_client.get_all_events(limit=2000)
    
    fixes_applied = []
    
    for event_data in events_data:
        event_id = event_data.get("id")
        title = event_data.get("event_title", "")
        url = event_data.get("url", "")
        event_date_str = event_data.get("event_date")
        
        if not event_id:
            continue
        
        title_lower = title.lower()
        url_lower = url.lower()
        
        # Fix 1: Conference on e-Government - should be eventdetail URL
        if "e-government" in title_lower or "smart cities" in title_lower:
            if "eventdetail" not in url_lower:
                # The correct URL should be eventdetail/3264530 based on user's feedback
                correct_url = "https://conferenceineurope.net/eventdetail/3264530"
                print(f"\n1. Fixing conference URL:")
                print(f"   Title: {title}")
                print(f"   Old URL: {url}")
                print(f"   New URL: {correct_url}")
                
                try:
                    db_client.client.table("events").update({
                        "url": correct_url,
                        "registration_url": correct_url
                    }).eq("id", event_id).execute()
                    fixes_applied.append("Conference URL updated")
                    print("   ✅ URL updated")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        
        # Fix 2: State of Local Self Government - remove if URL is generic
        if "state of local self government" in title_lower:
            if "/home" in url_lower:
                print(f"\n2. Removing event with generic URL:")
                print(f"   Title: {title}")
                print(f"   URL: {url}")
                
                try:
                    db_client.client.table("events").delete().eq("id", event_id).execute()
                    fixes_applied.append("Removed State of Local Self Government (generic URL)")
                    print("   ✅ Event removed")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        
        # Fix 3: Energy Managers Forum - fix date to Dec 1
        if "енергоменеджерів" in title_lower or "energy managers forum" in title_lower:
            if event_date_str:
                try:
                    current_date = date.fromisoformat(event_date_str) if isinstance(event_date_str, str) else event_date_str
                    if current_date.day == 5 and current_date.month == 12:
                        # Update to Dec 1 (start of week)
                        correct_date = date(2025, 12, 1)
                        print(f"\n3. Fixing Energy Managers Forum date:")
                        print(f"   Title: {title}")
                        print(f"   Old Date: {current_date}")
                        print(f"   New Date: {correct_date}")
                        
                        try:
                            db_client.client.table("events").update({
                                "event_date": correct_date.isoformat()
                            }).eq("id", event_id).execute()
                            fixes_applied.append("Energy Managers Forum date updated to Dec 1")
                            print("   ✅ Date updated")
                        except Exception as e:
                            print(f"   ❌ Error: {e}")
                except Exception as e:
                    print(f"   ⚠️  Could not parse date: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if fixes_applied:
        print(f"✅ Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"   • {fix}")
    else:
        print("✅ No fixes needed")
    print()

if __name__ == "__main__":
    fix_remaining_issues()



