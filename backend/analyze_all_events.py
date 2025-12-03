"""Analyze all events in database to determine relevance."""
import sys
import os
from datetime import date, timedelta
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient
from agent.models import Event
from agent.url_validator import URLValidator
from agent.url_content_analyzer import URLContentAnalyzer
from agent.date_validator import DateValidator
from agent.duplicate_detector import DuplicateDetector

def analyze_event(event: Event, all_events: List[Event], event_data: dict) -> Dict:
    """Analyze a single event and return analysis results."""
    analysis = {
        "id": event_data.get("id", "N/A"),
        "title": event.event_title,
        "date": event.event_date,
        "url": event.url,
        "category": event.category,
        "summary": event.summary,
        "issues": [],
        "warnings": [],
        "is_valid": True,
        "should_remove": False,
        "should_update": False
    }
    
    # Check 1: Is it a program announcement?
    title_lower = event.event_title.lower()
    summary_lower = (event.summary or "").lower()
    
    program_indicators = [
        "compensation program", "housing program", "program for",
        "applications open", "can submit", "submitting applications",
        "program starts", "access to"
    ]
    
    if any(indicator in title_lower for indicator in program_indicators):
        analysis["issues"].append("❌ Program announcement (not an event)")
        analysis["is_valid"] = False
        analysis["should_remove"] = True
    
    if any(indicator in summary_lower for indicator in program_indicators):
        if not any(kw in summary_lower for kw in ["conference", "workshop", "seminar", "webinar", "forum", "event", "meeting"]):
            analysis["issues"].append("❌ Summary indicates program announcement")
            analysis["is_valid"] = False
            analysis["should_remove"] = True
    
    # Check 2: Is it news?
    news_indicators = ["news", "article", "blog", "report", "analysis"]
    if any(indicator in title_lower for indicator in news_indicators):
        if not any(kw in title_lower for kw in ["conference", "workshop", "seminar", "webinar", "forum", "event"]):
            analysis["issues"].append("❌ Appears to be news/article")
            analysis["is_valid"] = False
            analysis["should_remove"] = True
    
    # Check 3: Is URL a news article URL? (check URL path)
    url_lower = event.url.lower()
    news_path_indicators = ["/news/", "/article/", "/blog/", "/press-release/"]
    if any(indicator in url_lower for indicator in news_path_indicators):
        analysis["issues"].append("❌ URL is a news article URL")
        analysis["is_valid"] = False
        analysis["should_remove"] = True
    
    # Check 4: Is it a local/narrow event? (check title/summary for local indicators)
    local_indicators = [
        "засідання архітектурно", "містобудівної ради", "обласна рада", "міська рада",
        "районна рада", "територіальна громада", "municipal council meeting",
        "regional council meeting", "oblast", "район", "громада"
    ]
    title_lower = event.event_title.lower()
    summary_lower = (event.summary or "").lower()
    if any(indicator in title_lower for indicator in local_indicators) or \
       any(indicator in summary_lower for indicator in local_indicators):
        # Check if it's NOT a major event
        event_keywords = ["conference", "forum", "summit", "international", "національний", "міжнародний"]
        if not any(kw in title_lower for kw in event_keywords) and \
           not any(kw in summary_lower for kw in event_keywords):
            analysis["issues"].append("⚠️  Local/narrow event (may be too specific)")
            analysis["warnings"].append("Consider if this is relevant for the target audience")
    
    # Check 5: Is URL an aggregator/listing page?
    url_lower = event.url.lower()
    aggregator_indicators = ['/contact', '/about', '/home', '/events?', '/event-list', '/calendar']
    event_page_indicators = ['eventdetail', '/event/', '/events/']
    
    is_aggregator = any(ind in url_lower for ind in aggregator_indicators)
    is_event_page = any(ind in url_lower for ind in event_page_indicators)
    
    if is_aggregator and not is_event_page:
        analysis["issues"].append("⚠️  URL appears to be aggregator/listing page, not direct event page")
        analysis["should_update"] = True
        analysis["warnings"].append("Should find direct event URL")
    
    # Check 6: Is date in the past?
    today = date.today()
    if event.event_date < today:
        analysis["issues"].append("❌ Event date is in the past")
        analysis["is_valid"] = False
        analysis["should_remove"] = True
    
    # Check 7: Is date too far in the future (>6 months)?
    six_months = today + timedelta(days=180)
    if event.event_date > six_months:
        analysis["warnings"].append("⚠️  Event date is more than 6 months away")
    
    # Check 8: Check if URL content indicates past event
    date_validator = DateValidator()
    is_past, reason = date_validator.check_if_past_event(event.url, event.event_date)
    if is_past:
        analysis["issues"].append(f"❌ URL content indicates past event: {reason}")
        analysis["is_valid"] = False
        analysis["should_remove"] = True
    
    # Check 9: Is URL accessible? (skip for now to avoid network calls, just check format)
    url_lower = event.url.lower()
    if not event.url.startswith(('http://', 'https://')):
        analysis["issues"].append("❌ URL format is invalid")
        analysis["is_valid"] = False
        analysis["should_remove"] = True
    elif any(skip in url_lower for skip in ['/contact', '/about', '/home']):
        # Check if it's just a generic page (not an event page)
        if 'eventdetail' not in url_lower and '/event/' not in url_lower:
            analysis["warnings"].append("⚠️  URL appears to be a generic page (contact/about/home)")
    
    # Check 10: Is it a duplicate?
    duplicate_detector = DuplicateDetector()
    event_dict = event.to_dict()
    event_dict["event_date"] = event.event_date  # Ensure date is date object, not string
    other_events_data = []
    for e in all_events:
        if e.url != event.url:
            e_dict = e.to_dict()
            e_dict["event_date"] = e.event_date
            other_events_data.append(e_dict)
    
    # Check against each other event
    for other_event_dict in other_events_data:
        if duplicate_detector.is_duplicate(event_dict, other_event_dict):
            analysis["issues"].append("❌ Duplicate event")
            analysis["is_valid"] = False
            analysis["should_remove"] = True
            break
    
    # Check 11: Does it have required event indicators?
    event_indicators = ["conference", "workshop", "seminar", "webinar", "forum", "training", "meeting", "event", "symposium", "summit"]
    has_event_indicator = any(indicator in title_lower for indicator in event_indicators) or \
                         any(indicator in summary_lower for indicator in event_indicators)
    
    if not has_event_indicator and analysis["is_valid"]:
        analysis["warnings"].append("⚠️  No clear event indicator in title/summary")
    
    return analysis

def main():
    """Analyze all events in the database."""
    print("=" * 80)
    print("ANALYZING ALL EVENTS IN DATABASE")
    print("=" * 80)
    print()
    
    db_client = DatabaseClient()
    
    # Fetch all events
    print("Fetching all events from database...")
    # Get all events (including past ones for analysis)
    events_data = db_client.get_all_events(limit=2000)
    events = [Event(**e) for e in events_data]
    print(f"Found {len(events)} events\n")
    
    # Analyze each event
    analyses = []
    for event_data, event in zip(events_data, events):
        analysis = analyze_event(event, events, event_data)
        analyses.append(analysis)
    
    # Sort by validity (invalid first)
    analyses.sort(key=lambda x: (x["is_valid"], len(x["issues"])))
    
    # Print results
    valid_count = sum(1 for a in analyses if a["is_valid"])
    invalid_count = len(analyses) - valid_count
    
    print("=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total events: {len(analyses)}")
    print(f"✅ Valid events: {valid_count}")
    print(f"❌ Invalid events: {invalid_count}")
    print()
    
    # Print invalid events
    if invalid_count > 0:
        print("=" * 80)
        print("❌ INVALID EVENTS (SHOULD BE REMOVED)")
        print("=" * 80)
        for i, analysis in enumerate(analyses, 1):
            if not analysis["is_valid"]:
                print(f"\n{i}. {analysis['title']}")
                print(f"   Date: {analysis['date']}")
                print(f"   URL: {analysis['url']}")
                print(f"   Category: {analysis['category']}")
                if analysis['summary']:
                    print(f"   Summary: {analysis['summary'][:100]}...")
                print(f"   Issues:")
                for issue in analysis['issues']:
                    print(f"     {issue}")
        print()
    
    # Print events with warnings
    events_with_warnings = [a for a in analyses if a["warnings"]]
    if events_with_warnings:
        print("=" * 80)
        print("⚠️  EVENTS WITH WARNINGS (REVIEW NEEDED)")
        print("=" * 80)
        for i, analysis in enumerate(events_with_warnings, 1):
            print(f"\n{i}. {analysis['title']}")
            print(f"   Date: {analysis['date']}")
            print(f"   URL: {analysis['url']}")
            print(f"   Warnings:")
            for warning in analysis['warnings']:
                print(f"     {warning}")
        print()
    
    # Print valid events
    if valid_count > 0:
        print("=" * 80)
        print("✅ VALID EVENTS")
        print("=" * 80)
        for i, analysis in enumerate(analyses, 1):
            if analysis["is_valid"]:
                print(f"\n{i}. {analysis['title']}")
                print(f"   Date: {analysis['date']}")
                print(f"   URL: {analysis['url']}")
                print(f"   Category: {analysis['category']}")
                if analysis['warnings']:
                    print(f"   Warnings:")
                    for warning in analysis['warnings']:
                        print(f"     {warning}")
        print()
    
    # Summary of issues
    print("=" * 80)
    print("ISSUE BREAKDOWN")
    print("=" * 80)
    issue_counts = {}
    for analysis in analyses:
        for issue in analysis['issues']:
            issue_type = issue.split(':')[0] if ':' in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
    
    for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{issue_type}: {count}")
    print()
    
    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    should_remove = [a for a in analyses if a["should_remove"]]
    should_update = [a for a in analyses if a["should_update"]]
    
    if should_remove:
        print(f"\n❌ Remove {len(should_remove)} invalid events:")
        for analysis in should_remove:
            print(f"   - {analysis['title'][:60]}...")
    
    if should_update:
        print(f"\n⚠️  Update {len(should_update)} events (find better URLs):")
        for analysis in should_update:
            print(f"   - {analysis['title'][:60]}...")
    
    if not should_remove and not should_update:
        print("\n✅ All events appear to be valid!")
    
    print()

if __name__ == "__main__":
    main()

