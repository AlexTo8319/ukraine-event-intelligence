"""Detailed check of events to identify issues that should have been fixed."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.models import Event

def check_event_issues():
    """Check all events for known issues."""
    db_client = DatabaseClient()
    events_data = db_client.get_all_events(limit=2000)
    events = [Event(**e) for e in events_data]
    
    print("=" * 80)
    print("DETAILED EVENT ISSUE CHECK")
    print("=" * 80)
    print(f"Total events in database: {len(events)}\n")
    
    issues_found = {
        "program_announcements": [],
        "wrong_urls": [],
        "holidays_observances": [],
        "duplicates": [],
        "news_articles": []
    }
    
    # Check each event
    for event in events:
        title_lower = event.event_title.lower()
        summary_lower = (event.summary or "").lower()
        url_lower = event.url.lower()
        
        # 1. Check for program announcements
        program_keywords = [
            "compensation program", "housing program", "program for",
            "applications open", "can submit", "submitting applications",
            "program starts", "launch of", "housing vouchers"
        ]
        
        if any(kw in title_lower for kw in program_keywords):
            issues_found["program_announcements"].append({
                "title": event.event_title,
                "date": event.event_date,
                "url": event.url,
                "reason": "Title contains program announcement keywords"
            })
        
        if any(kw in summary_lower for kw in ["can submit applications", "applications open", "apply for"]):
            if not any(ev in summary_lower for ev in ["conference", "workshop", "seminar", "webinar", "forum", "event"]):
                issues_found["program_announcements"].append({
                    "title": event.event_title,
                    "date": event.event_date,
                    "url": event.url,
                    "reason": "Summary indicates program/application process, not event"
                })
        
        # 2. Check for wrong URLs (aggregator/generic pages)
        generic_pages = ["/contact", "/about", "/home"]
        event_page_indicators = ["eventdetail", "/event/", "/events/"]
        
        has_generic = any(page in url_lower for page in generic_pages)
        has_event_page = any(ind in url_lower for ind in event_page_indicators)
        
        if has_generic and not has_event_page:
            issues_found["wrong_urls"].append({
                "title": event.event_title,
                "date": event.event_date,
                "url": event.url,
                "reason": "URL is generic page (contact/about/home) without eventdetail"
            })
        
        # 3. Check for holidays/observances
        holiday_keywords = ["day of", "день", "national day", "professional holiday"]
        event_keywords = ["conference", "workshop", "seminar", "webinar", "forum", "meeting", "event"]
        
        if any(hk in title_lower for hk in holiday_keywords):
            if not any(ek in title_lower for ek in event_keywords):
                issues_found["holidays_observances"].append({
                    "title": event.event_title,
                    "date": event.event_date,
                    "url": event.url,
                    "reason": "Appears to be a holiday/observance, not an event"
                })
        
        # 4. Check for news articles
        news_keywords = ["/news/", "/article/", "/blog/"]
        if any(nk in url_lower for nk in news_keywords):
            issues_found["news_articles"].append({
                "title": event.event_title,
                "date": event.event_date,
                "url": event.url,
                "reason": "URL is a news article"
            })
    
    # 5. Check for duplicates
    seen_titles = {}
    for event in events:
        title_normalized = event.event_title.lower().strip()
        if title_normalized in seen_titles:
            issues_found["duplicates"].append({
                "title": event.event_title,
                "date": event.event_date,
                "url": event.url,
                "duplicate_of": seen_titles[title_normalized]["title"],
                "duplicate_url": seen_titles[title_normalized]["url"]
            })
        else:
            seen_titles[title_normalized] = {
                "title": event.event_title,
                "url": event.url,
                "date": event.event_date
            }
    
    # Print results
    print("=" * 80)
    print("ISSUES FOUND")
    print("=" * 80)
    
    if issues_found["program_announcements"]:
        print(f"\n❌ PROGRAM ANNOUNCEMENTS (NOT EVENTS): {len(issues_found['program_announcements'])}")
        for issue in issues_found["program_announcements"]:
            print(f"  • {issue['title']}")
            print(f"    Date: {issue['date']}")
            print(f"    URL: {issue['url']}")
            print(f"    Reason: {issue['reason']}\n")
    
    if issues_found["wrong_urls"]:
        print(f"\n⚠️  WRONG URLS (GENERIC PAGES): {len(issues_found['wrong_urls'])}")
        for issue in issues_found["wrong_urls"]:
            print(f"  • {issue['title']}")
            print(f"    Date: {issue['date']}")
            print(f"    URL: {issue['url']}")
            print(f"    Reason: {issue['reason']}\n")
    
    if issues_found["holidays_observances"]:
        print(f"\n⚠️  HOLIDAYS/OBSERVANCES (NOT EVENTS): {len(issues_found['holidays_observances'])}")
        for issue in issues_found["holidays_observances"]:
            print(f"  • {issue['title']}")
            print(f"    Date: {issue['date']}")
            print(f"    URL: {issue['url']}")
            print(f"    Reason: {issue['reason']}\n")
    
    if issues_found["duplicates"]:
        print(f"\n❌ DUPLICATES: {len(issues_found['duplicates'])}")
        for issue in issues_found["duplicates"]:
            print(f"  • {issue['title']}")
            print(f"    Date: {issue['date']}")
            print(f"    URL: {issue['url']}")
            print(f"    Duplicate of: {issue['duplicate_of']}")
            print(f"    Original URL: {issue['duplicate_url']}\n")
    
    if issues_found["news_articles"]:
        print(f"\n❌ NEWS ARTICLES: {len(issues_found['news_articles'])}")
        for issue in issues_found["news_articles"]:
            print(f"  • {issue['title']}")
            print(f"    Date: {issue['date']}")
            print(f"    URL: {issue['url']}\n")
    
    total_issues = sum(len(v) for v in issues_found.values())
    print("=" * 80)
    print(f"TOTAL ISSUES FOUND: {total_issues}")
    print("=" * 80)
    
    return issues_found

if __name__ == "__main__":
    check_event_issues()



