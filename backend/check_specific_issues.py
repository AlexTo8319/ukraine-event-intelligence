"""Check specific issues mentioned by user."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.models import Event
from agent.url_content_analyzer import URLContentAnalyzer

def check_specific_issues():
    """Check specific issues mentioned by user."""
    db_client = DatabaseClient()
    events_data = db_client.get_all_events(limit=2000)
    events = [Event(**e) for e in events_data]
    
    print("=" * 80)
    print("CHECKING SPECIFIC ISSUES")
    print("=" * 80)
    
    # Find specific events
    conference_event = None
    state_event = None
    energy_forum = None
    
    for event in events:
        title_lower = event.event_title.lower()
        if "e-government" in title_lower or "smart cities" in title_lower:
            conference_event = event
        if "state of local self government" in title_lower:
            state_event = event
        if "енергоменеджерів" in title_lower or "energy managers forum" in title_lower:
            energy_forum = event
    
    print("\n1. International Conference on e-Government, Smart Cities, and Digital Societies")
    if conference_event:
        print(f"   Current URL: {conference_event.url}")
        print(f"   Date: {conference_event.event_date}")
        if "/contact" in conference_event.url.lower():
            print("   ❌ ISSUE: URL is /contact page")
        elif "eventdetail" in conference_event.url.lower():
            print("   ✅ URL contains eventdetail")
        else:
            print("   ⚠️  URL might not be direct event page")
    else:
        print("   ⚠️  Event not found")
    
    print("\n2. State of Local Self Government: Challenges and Prospects")
    if state_event:
        print(f"   Current URL: {state_event.url}")
        print(f"   Date: {state_event.event_date}")
        if "/home" in state_event.url.lower():
            print("   ❌ ISSUE: URL is /home page (generic)")
            # Try to find better URL
            print("   Attempting to find better URL...")
            url_analyzer = URLContentAnalyzer()
            analysis = url_analyzer.analyze_url(state_event.url, state_event.event_title, state_event.event_date)
            if analysis.get("found_better_url"):
                print(f"   ✅ Found better URL: {analysis['actual_url']}")
            else:
                print("   ⚠️  Could not find better URL in content")
    else:
        print("   ⚠️  Event not found")
    
    print("\n3. Energy Managers Forum (Форум енергоменеджерів)")
    if energy_forum:
        print(f"   Current URL: {energy_forum.url}")
        print(f"   Current Date: {energy_forum.event_date}")
        print(f"   Summary: {energy_forum.summary}")
        
        # Check if date should be Dec 1 (start of week)
        if energy_forum.event_date.day == 5:
            print("   ❌ ISSUE: Date is Dec 5, but should be Dec 1 (start of week)")
            # Try to extract date from URL content
            print("   Attempting to extract correct date from URL content...")
            url_analyzer = URLContentAnalyzer()
            analysis = url_analyzer.analyze_url(energy_forum.url, energy_forum.event_title, energy_forum.event_date)
            extracted_date = analysis.get("extracted_date")
            if extracted_date and extracted_date.day == 1:
                print(f"   ✅ Found correct date in URL content: {extracted_date}")
                print(f"   Should update from {energy_forum.event_date} to {extracted_date}")
            else:
                print("   ⚠️  Could not extract correct date from URL content")
        else:
            print("   ✅ Date appears correct")
    else:
        print("   ⚠️  Event not found")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_specific_issues()



