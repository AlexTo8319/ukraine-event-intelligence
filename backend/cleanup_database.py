#!/usr/bin/env python3
"""
Database Cleanup Script

This script removes:
1. Duplicate events (keeps the one with best URL)
2. Irrelevant events (biotechnology, AI, etc.)
3. Events with bad URLs (listing pages, news aggregators, homepages)

IMPORTANT: Requires SUPABASE_KEY to be a service role key (not anon key)
The anon key doesn't have delete permissions.

Usage:
    export SUPABASE_URL="your_url"
    export SUPABASE_KEY="your_service_role_key"  # NOT the anon key!
    python cleanup_database.py
"""

import os
import sys
import re
from datetime import date, datetime
from difflib import SequenceMatcher
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.client import DatabaseClient


def similar(a: str, b: str) -> float:
    """Calculate string similarity."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def score_url(url: str) -> int:
    """Score URL quality - higher is better."""
    score = 0
    url_lower = url.lower()
    
    # Prefer specific event pages
    if 'eventdetail' in url_lower:
        score += 50
    if '/event/' in url_lower:
        score += 30
    if 'conference' in url_lower or 'forum' in url_lower:
        score += 10
    
    # Penalize generic pages
    if url_lower.rstrip('/').endswith('/events'):
        score -= 40
    if 'calendar' in url_lower and 'eventid' not in url_lower:
        score -= 30
    if 'news' in url_lower or 'article' in url_lower:
        score -= 50
    if 'kyivindependent' in url_lower:
        score -= 60
    if 'toolkit' in url_lower and 'events' in url_lower:
        score -= 30
    if re.match(r'^https?://[^/]+/?$', url):  # Homepage
        score -= 50
    if re.search(r'/\d{4}/\d{1,2}/?$', url):  # Month archive
        score -= 40
    
    return score


def is_irrelevant_event(title: str, summary: str) -> tuple[bool, str]:
    """Check if event is clearly irrelevant to urban planning/recovery."""
    combined = f"{title.lower()} {(summary or '').lower()}"
    
    # Clearly irrelevant topics
    irrelevant_keywords = [
        'biotechnology', 'biodiversity', 'biology',
        'artificial intelligence', 'software engineering', 'machine learning',
        'teacher education', 'pedagogy', 'teaching methods',
        'spanish language', 'latin american studies', 'language studies',
        'multilingual education', 'big data',
        'medical research', 'healthcare',
        'benefit concert', 'film for ukraine'
    ]
    
    # Urban/recovery keywords
    urban_keywords = [
        'urban', 'city', 'planning', 'recovery', 'housing', 'reconstruction',
        'municipal', 'local government', 'decentralization', 'energy', 'efficiency',
        'waste', 'management', 'infrastructure', 'sustainable', 'green',
        'rebuild', 'affordable', 'smart building'
    ]
    
    has_irrelevant = any(kw in combined for kw in irrelevant_keywords)
    has_urban = any(kw in combined for kw in urban_keywords)
    
    if has_irrelevant and not has_urban:
        matched = [kw for kw in irrelevant_keywords if kw in combined]
        return True, f"Contains irrelevant topic: {matched[0]}"
    
    return False, ""


def is_bad_url(url: str) -> tuple[bool, str]:
    """Check if URL is a bad URL that should be removed."""
    url_lower = url.lower()
    
    # News aggregators
    news_aggregators = [
        'kyivindependent.com',
        'pravda.com.ua',
        'ukrinform.ua',
        'unian.ua',
        'korrespondent.net'
    ]
    if any(agg in url_lower for agg in news_aggregators):
        return True, "News aggregator"
    
    # Listing pages ending with /events
    if url_lower.rstrip('/').endswith('/events'):
        return True, "Listing page (/events)"
    
    # Generic homepages
    if re.match(r'^https?://[^/]+/?$', url):
        return True, "Homepage"
    
    # Month archive pages
    if re.search(r'/\d{4}/\d{1,2}/?$', url):
        return True, "Month archive"
    
    # Generic calendar pages
    if '/calendar.aspx' in url_lower or '/calendar/' in url_lower:
        if 'eventid' not in url_lower and 'eid=' not in url_lower:
            return True, "Generic calendar"
    
    return False, ""


def main():
    print("=" * 80)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 80)
    print()
    
    # Check for service role key
    key = os.getenv("SUPABASE_KEY", "")
    if "anon" in key.lower() or not key:
        print("⚠️  WARNING: You may be using the anon key, which cannot delete events.")
        print("   Please use the service role key from Supabase Dashboard.")
        print("   Dashboard > Settings > API > service_role key")
        print()
    
    db = DatabaseClient()
    events = db.get_upcoming_events(days=180)
    
    print(f"Total events in database: {len(events)}")
    print()
    
    # ========================================================================
    # STEP 1: Find duplicates
    # ========================================================================
    print("=" * 80)
    print("STEP 1: FINDING DUPLICATES")
    print("=" * 80)
    
    title_groups = defaultdict(list)
    for e in events:
        title = e.get('event_title', '')
        found_group = False
        for key in title_groups:
            if similar(title, key) > 0.85:
                title_groups[key].append(e)
                found_group = True
                break
        if not found_group:
            title_groups[title].append(e)
    
    duplicates_to_remove = []
    for title, group in title_groups.items():
        if len(group) > 1:
            # Sort by URL score (best first)
            group.sort(key=lambda x: score_url(x.get('url', '')), reverse=True)
            # Keep first, remove rest
            print(f"\n  Group: {title[:50]}...")
            print(f"    KEEP: {group[0].get('url', '')[:60]}")
            for e in group[1:]:
                duplicates_to_remove.append(e)
                print(f"    REMOVE: {e.get('url', '')[:60]}")
    
    print(f"\nDuplicates to remove: {len(duplicates_to_remove)}")
    
    # ========================================================================
    # STEP 2: Find irrelevant events
    # ========================================================================
    print()
    print("=" * 80)
    print("STEP 2: FINDING IRRELEVANT EVENTS")
    print("=" * 80)
    
    irrelevant_events = []
    for e in events:
        is_irrelevant, reason = is_irrelevant_event(
            e.get('event_title', ''),
            e.get('summary', '')
        )
        if is_irrelevant:
            irrelevant_events.append(e)
            print(f"  {e.get('event_title', '')[:50]}...")
            print(f"    Reason: {reason}")
    
    print(f"\nIrrelevant to remove: {len(irrelevant_events)}")
    
    # ========================================================================
    # STEP 3: Find bad URLs
    # ========================================================================
    print()
    print("=" * 80)
    print("STEP 3: FINDING BAD URLs")
    print("=" * 80)
    
    bad_url_events = []
    for e in events:
        is_bad, reason = is_bad_url(e.get('url', ''))
        if is_bad:
            bad_url_events.append(e)
            print(f"  {e.get('event_title', '')[:40]}...")
            print(f"    URL: {e.get('url', '')[:60]}")
            print(f"    Reason: {reason}")
    
    print(f"\nBad URL events: {len(bad_url_events)}")
    
    # ========================================================================
    # SUMMARY AND REMOVAL
    # ========================================================================
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Collect all URLs to remove (avoid duplicates)
    urls_to_remove = set()
    for e in duplicates_to_remove:
        urls_to_remove.add(e.get('url'))
    for e in irrelevant_events:
        urls_to_remove.add(e.get('url'))
    for e in bad_url_events:
        urls_to_remove.add(e.get('url'))
    
    print(f"Total unique events to remove: {len(urls_to_remove)}")
    print()
    
    if not urls_to_remove:
        print("✅ No events to remove. Database is clean!")
        return
    
    # Confirm removal
    print("Events to remove:")
    for url in sorted(urls_to_remove):
        print(f"  - {url[:70]}")
    print()
    
    confirm = input("Remove these events? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    # Remove events
    print()
    print("Removing events...")
    removed_count = 0
    failed_count = 0
    
    for url in urls_to_remove:
        try:
            result = db.client.table("events").delete().eq("url", url).execute()
            # Check if actually deleted
            check = db.client.table("events").select("url").eq("url", url).execute()
            if not check.data:
                removed_count += 1
                print(f"  ✅ Removed: {url[:60]}")
            else:
                failed_count += 1
                print(f"  ❌ Failed (still exists): {url[:60]}")
        except Exception as e:
            failed_count += 1
            print(f"  ❌ Error: {url[:40]} - {e}")
    
    print()
    print("=" * 80)
    print(f"RESULTS: Removed {removed_count}, Failed {failed_count}")
    print("=" * 80)
    
    if failed_count > 0:
        print()
        print("⚠️  Some deletions failed. This usually means you're using the anon key.")
        print("   Please use the service role key from Supabase Dashboard.")
        print("   Dashboard > Settings > API > service_role key")
    
    # Show remaining events
    remaining = db.get_upcoming_events(days=180)
    print(f"\nRemaining events: {len(remaining)}")


if __name__ == "__main__":
    main()



