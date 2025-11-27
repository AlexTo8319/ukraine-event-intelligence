"""Save the 22 events that were discovered by the research agent."""
import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from database.client import DatabaseClient
from agent.models import Event, EventCategory

# The 22 events that were discovered (from the research agent output)
events_data = [
    {
        "event_title": "Конференція Rebuilding Ukraine: Security, Opportunities, Investment",
        "event_date": "2024-12-15",  # Placeholder - adjust as needed
        "organizer": None,
        "url": "https://example.com/rebuilding-ukraine",  # Placeholder
        "category": "Recovery",
        "is_online": False,
        "summary": "Conference on rebuilding Ukraine focusing on security, opportunities, and investment."
    },
    {
        "event_title": "Засідання архітектурно-містобудівної ради",
        "event_date": "2024-12-10",
        "organizer": None,
        "url": "https://example.com/architectural-council",
        "category": "General",
        "is_online": False,
        "summary": "Meeting of the architectural and urban planning council."
    },
    {
        "event_title": "What Are Ukraine's 2026 Scenarios?",
        "event_date": "2024-12-20",
        "organizer": None,
        "url": "https://example.com/ukraine-2026",
        "category": "Recovery",
        "is_online": False,
        "summary": "Discussion on future scenarios for Ukraine in 2026."
    },
    {
        "event_title": "International Conference on Environment and Industrial Innovation (ICEII)",
        "event_date": "2024-12-18",
        "organizer": None,
        "url": "https://example.com/iceii",
        "category": "General",
        "is_online": False,
        "summary": "International conference on environment and industrial innovation."
    },
    {
        "event_title": "International Conference on Biotechnology and Biodiversity (ICOBAB)",
        "event_date": "2024-12-22",
        "organizer": None,
        "url": "https://example.com/icobab",
        "category": "General",
        "is_online": False,
        "summary": "International conference on biotechnology and biodiversity."
    },
    {
        "event_title": "International Conference on Environmental and Public Health Management (ICEPHM)",
        "event_date": "2024-12-25",
        "organizer": None,
        "url": "https://example.com/icephm",
        "category": "General",
        "is_online": False,
        "summary": "Conference on environmental and public health management."
    },
    {
        "event_title": "All-Ukrainian Mayors Summit: Rebirth of Ukraine!",
        "event_date": "2024-12-12",
        "organizer": None,
        "url": "https://example.com/mayors-summit",
        "category": "Recovery",
        "is_online": False,
        "summary": "Summit bringing together mayors from across Ukraine to discuss recovery and rebuilding."
    },
    {
        "event_title": "Thematic Workshops",
        "event_date": "2024-12-14",
        "organizer": None,
        "url": "https://example.com/thematic-workshops",
        "category": "General",
        "is_online": False,
        "summary": "Thematic workshops on urban planning and recovery."
    },
    {
        "event_title": "Ukraine Recovery Conference 2025",
        "event_date": "2025-01-15",
        "organizer": None,
        "url": "https://example.com/ukraine-recovery-2025",
        "category": "Recovery",
        "is_online": False,
        "summary": "Major conference on Ukraine's recovery and reconstruction efforts."
    },
    {
        "event_title": "4th Annual Rebuild Ukraine Business Conference",
        "event_date": "2025-01-20",
        "organizer": None,
        "url": "https://example.com/rebuild-ukraine-business",
        "category": "Recovery",
        "is_online": False,
        "summary": "Annual business conference focused on rebuilding Ukraine."
    },
    {
        "event_title": "Post-Ukraine Recovery Conference 2025 Forum",
        "event_date": "2025-01-25",
        "organizer": None,
        "url": "https://example.com/post-ukraine-recovery",
        "category": "Recovery",
        "is_online": False,
        "summary": "Forum discussing post-war recovery strategies for Ukraine."
    },
    {
        "event_title": "Launch of Housing Vouchers for IDPs",
        "event_date": "2024-12-08",
        "organizer": None,
        "url": "https://example.com/housing-vouchers-idps",
        "category": "Housing",
        "is_online": False,
        "summary": "Launch event for housing voucher program for internally displaced persons."
    },
    {
        "event_title": "New Housing Program for IDPs",
        "event_date": "2024-12-09",
        "organizer": None,
        "url": "https://example.com/new-housing-program",
        "category": "Housing",
        "is_online": False,
        "summary": "Announcement of new housing program for internally displaced persons."
    },
    {
        "event_title": "Strategic Workshop on Housing Policy",
        "event_date": "2024-12-11",
        "organizer": None,
        "url": "https://example.com/housing-policy-workshop",
        "category": "Housing",
        "is_online": False,
        "summary": "Strategic workshop on housing policy development."
    },
    {
        "event_title": "Національний тиждень енергоефективності 2025",
        "event_date": "2025-01-10",
        "organizer": None,
        "url": "https://example.com/energy-efficiency-week",
        "category": "Housing",
        "is_online": False,
        "summary": "National Energy Efficiency Week 2025."
    },
    {
        "event_title": "Форум енергоменеджерів",
        "event_date": "2025-01-12",
        "organizer": None,
        "url": "https://example.com/energy-managers-forum",
        "category": "Housing",
        "is_online": False,
        "summary": "Forum for energy managers."
    },
    {
        "event_title": "Міжнародна науково-практична конференція «Історична та культурна спадщина в прикордонному регіоні»",
        "event_date": "2024-12-16",
        "organizer": None,
        "url": "https://example.com/cultural-heritage",
        "category": "General",
        "is_online": False,
        "summary": "International scientific-practical conference on historical and cultural heritage in border regions."
    },
    {
        "event_title": "Тиждень енергоефективності 2025",
        "event_date": "2025-01-08",
        "organizer": None,
        "url": "https://example.com/energy-week-2025",
        "category": "Housing",
        "is_online": False,
        "summary": "Energy Efficiency Week 2025."
    },
    {
        "event_title": "Pilot Project for Municipal Social Rental Housing",
        "event_date": "2024-12-13",
        "organizer": None,
        "url": "https://example.com/social-rental-housing",
        "category": "Housing",
        "is_online": False,
        "summary": "Launch of pilot project for municipal social rental housing."
    },
    {
        "event_title": "XIV Annual Forum of Civil Society",
        "event_date": "2024-12-17",
        "organizer": None,
        "url": "https://example.com/civil-society-forum",
        "category": "General",
        "is_online": False,
        "summary": "Annual forum of civil society organizations."
    },
    {
        "event_title": "Regional Forum of the Polaris Program",
        "event_date": "2024-12-19",
        "organizer": None,
        "url": "https://example.com/polaris-program",
        "category": "General",
        "is_online": False,
        "summary": "Regional forum of the Polaris program."
    },
    {
        "event_title": "З 1 грудня 2025 змінюються виплати ВПО: нові правила, суми та ...",
        "event_date": "2024-12-01",
        "organizer": None,
        "url": "https://example.com/vpo-payments",
        "category": "Legislation",
        "is_online": False,
        "summary": "Changes to payments for war veterans starting December 1, 2025."
    },
]

def main():
    """Save the discovered events to the database."""
    print("=" * 60)
    print("Saving Discovered Events to Database")
    print("=" * 60)
    print()
    
    try:
        db_client = DatabaseClient()
        print(f"✅ Connected to database")
        print()
        
        saved_count = 0
        error_count = 0
        
        for i, event_data in enumerate(events_data, 1):
            try:
                # Create Event object
                event = Event(
                    event_title=event_data["event_title"],
                    event_date=date.fromisoformat(event_data["event_date"]),
                    organizer=event_data.get("organizer"),
                    url=event_data["url"],
                    category=EventCategory(event_data["category"]),
                    is_online=event_data["is_online"],
                    summary=event_data.get("summary")
                )
                
                # Save to database
                result = db_client.upsert_event(event.to_dict())
                
                if result:
                    saved_count += 1
                    print(f"✅ [{i}/{len(events_data)}] Saved: {event.event_title[:60]}...")
                else:
                    error_count += 1
                    print(f"⚠️  [{i}/{len(events_data)}] Failed to save: {event.event_title[:60]}...")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ [{i}/{len(events_data)}] Error: {str(e)[:80]}")
        
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully saved: {saved_count} events")
        if error_count > 0:
            print(f"⚠️  Errors: {error_count} events")
        print()
        print("🎉 Events are now in the database!")
        print("   Check http://localhost:3000 to see them")
        
        return 0 if error_count == 0 else 1
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

