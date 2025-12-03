"""Fix specific issues identified by user."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.url_content_analyzer import URLContentAnalyzer
from agent.date_validator import DateValidator

def fix_specific_issues():
    """Fix specific events with wrong dates or URLs."""
    print("=" * 80)
    print("FIXING SPECIFIC EVENT ISSUES")
    print("=" * 80)
    print()
    
    db_client = DatabaseClient()
    url_analyzer = URLContentAnalyzer()
    date_validator = DateValidator()
    
    # Get all events
    events = db_client.get_events(limit=1000)
    
    issues_to_fix = []
    
    # Issue 1 & 2: Resilience Conference "Synergy of Youth in Sumy Region"
    # Wrong date: Nov 29, should be Nov 21, or remove if not found
    for event in events:
        title = event.get("event_title", "")
        if "Synergy of Youth" in title or "Синергія молоді" in title:
            issues_to_fix.append({
                "event": event,
                "issue": "Wrong date (Nov 29 vs Nov 21) or event not found on URL",
                "action": "remove_or_fix_date"
            })
    
    # Issue 3: Ukraine Green Recovery Conference - Past event (2023)
    for event in events:
        title = event.get("event_title", "")
        if "Ukraine Green Recovery" in title or "green recovery" in title.lower():
            issues_to_fix.append({
                "event": event,
                "issue": "Past event (2023, not 2025)",
                "action": "remove"
            })
    
    # Issue 4: Rethinking Cities - Program description, not specific event
    for event in events:
        title = event.get("event_title", "")
        if "Rethinking Cities" in title:
            issues_to_fix.append({
                "event": event,
                "issue": "Program description, not specific event",
                "action": "remove"
            })
    
    # Issue 5: Civil Protection Forum - Generic URL
    for event in events:
        title = event.get("event_title", "")
        if "Civil Protection" in title or "Synergy for Safety" in title:
            issues_to_fix.append({
                "event": event,
                "issue": "Generic URL, no specific event found",
                "action": "remove"
            })
    
    # Issue 6: BuildMasterClass-2025 - Wrong dates (Nov 26-28, not Dec 4)
    for event in events:
        title = event.get("event_title", "")
        if "BuildMasterClass" in title or "БудМайстерКлас" in title:
            issues_to_fix.append({
                "event": event,
                "issue": "Wrong date (Dec 4 vs Nov 26-28)",
                "action": "fix_date_or_remove"
            })
    
    # Issue 7: International Conference on Teacher Education - Generic URL
    for event in events:
        title = event.get("event_title", "")
        if "Teacher Education" in title:
            issues_to_fix.append({
                "event": event,
                "issue": "Generic listing URL, should be eventdetail",
                "action": "fix_url_or_remove"
            })
    
    print(f"Found {len(issues_to_fix)} events to fix\n")
    
    removed = 0
    fixed = 0
    
    for item in issues_to_fix:
        event = item["event"]
        issue = item["issue"]
        action = item["action"]
        
        print(f"Event: {event.get('event_title', 'Unknown')[:60]}...")
        print(f"Issue: {issue}")
        print(f"Current date: {event.get('event_date')}")
        print(f"URL: {event.get('url', '')[:60]}...")
        
        if action == "remove":
            print("Action: REMOVING event")
            try:
                # Delete from database
                db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                removed += 1
                print("✅ Removed\n")
            except Exception as e:
                print(f"❌ Error removing: {e}\n")
        
        elif action == "remove_or_fix_date":
            print("Action: Checking URL for correct date...")
            event_url = event.get("url")
            if event_url:
                analysis = url_analyzer.analyze_url(event_url, event.get("event_title"))
                extracted_date = analysis.get("extracted_date")
                
                # Check if it's a past event
                is_past, reason = date_validator.check_if_past_event(event_url, event.get("event_date"))
                
                if is_past or not extracted_date:
                    print(f"  → Past event or no date found. REMOVING")
                    try:
                        db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                        removed += 1
                        print("✅ Removed\n")
                    except Exception as e:
                        print(f"❌ Error removing: {e}\n")
                elif extracted_date and extracted_date != date.fromisoformat(event.get("event_date")):
                    print(f"  → Found correct date: {extracted_date}. UPDATING")
                    try:
                        db_client.client.table("events").update({"event_date": extracted_date.isoformat()}).eq("id", event.get("id")).execute()
                        fixed += 1
                        print("✅ Fixed date\n")
                    except Exception as e:
                        print(f"❌ Error updating date: {e}\n")
                else:
                    print("  → Date seems correct, but event not found on page. REMOVING")
                    try:
                        db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                        removed += 1
                        print("✅ Removed\n")
                    except Exception as e:
                        print(f"❌ Error removing: {e}\n")
            else:
                print("  → No URL. REMOVING")
                try:
                    db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                    removed += 1
                    print("✅ Removed\n")
                except Exception as e:
                    print(f"❌ Error removing: {e}\n")
        
        elif action == "fix_date_or_remove":
            print("Action: Checking URL for correct date...")
            event_url = event.get("url")
            if event_url:
                analysis = url_analyzer.analyze_url(event_url, event.get("event_title"))
                extracted_date = analysis.get("extracted_date")
                
                if extracted_date and extracted_date != date.fromisoformat(event.get("event_date")):
                    print(f"  → Found correct date: {extracted_date}. UPDATING")
                    try:
                        db_client.client.table("events").update({"event_date": extracted_date.isoformat()}).eq("id", event.get("id")).execute()
                        fixed += 1
                        print("✅ Fixed date\n")
                    except Exception as e:
                        print(f"❌ Error updating date: {e}\n")
                else:
                    print("  → Could not extract correct date. REMOVING")
                    try:
                        db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                        removed += 1
                        print("✅ Removed\n")
                    except Exception as e:
                        print(f"❌ Error removing: {e}\n")
            else:
                print("  → No URL. REMOVING")
                try:
                    db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                    removed += 1
                    print("✅ Removed\n")
                except Exception as e:
                    print(f"❌ Error removing: {e}\n")
        
        elif action == "fix_url_or_remove":
            print("Action: Looking for specific event URL...")
            event_url = event.get("url")
            if event_url and "eventdetail" not in event_url.lower():
                # Try to find eventdetail URL
                analysis = url_analyzer.analyze_url(event_url, event.get("event_title"))
                better_url = analysis.get("actual_url")
                
                if better_url and "eventdetail" in better_url.lower() and better_url != event_url:
                    print(f"  → Found eventdetail URL: {better_url[:60]}...")
                    # Update the event URL
                    try:
                        db_client.client.table("events").update({"url": better_url}).eq("id", event.get("id")).execute()
                        fixed += 1
                        print("✅ Fixed URL\n")
                    except Exception as e:
                        print(f"❌ Error updating URL: {e}\n")
                else:
                    print("  → Could not find specific event URL. REMOVING")
                    try:
                        db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                        removed += 1
                        print("✅ Removed\n")
                    except Exception as e:
                        print(f"❌ Error removing: {e}\n")
            else:
                print("  → Already has eventdetail URL or no URL. Checking if valid...")
                # Check if it's a past event
                is_past, reason = date_validator.check_if_past_event(event_url, event.get("event_date"))
                if is_past:
                    print(f"  → Past event ({reason}). REMOVING")
                    try:
                        db_client.client.table("events").delete().eq("id", event.get("id")).execute()
                        removed += 1
                        print("✅ Removed\n")
                    except Exception as e:
                        print(f"❌ Error removing: {e}\n")
                else:
                    print("  → Event seems valid\n")
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Events removed: {removed}")
    print(f"Events fixed: {fixed}")
    print(f"Total processed: {len(issues_to_fix)}")
    print()

if __name__ == "__main__":
    fix_specific_issues()

