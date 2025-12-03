"""Limited test research run to verify URL improvements."""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.search import SearchAgent
from agent.llm_processor import LLMProcessor
from agent.url_validator import URLValidator

def test_research():
    """Run a limited test research to verify URL extraction improvements."""
    print("=" * 60)
    print("TEST RESEARCH - VERIFYING URL IMPROVEMENTS")
    print("=" * 60)
    print()
    
    search_agent = SearchAgent()
    llm_processor = LLMProcessor()
    url_validator = URLValidator(timeout=5, max_redirects=5)
    
    # Test with just 2 queries
    test_queries = [
        "urban planning Ukraine events 2025 next 6 months",
        "Ukraine reconstruction events 2025 next 6 months"
    ]
    
    print(f"Testing with {len(test_queries)} queries...")
    print()
    
    all_results = []
    for i, query in enumerate(test_queries, 1):
        print(f"[{datetime.now()}] Query {i}/{len(test_queries)}: {query[:50]}...")
        try:
            results = search_agent.search(query, max_results=5)  # Limit to 5 results per query
            all_results.extend(results)
            print(f"  ✅ Found {len(results)} results")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print()
    print(f"Total results: {len(all_results)}")
    print()
    
    # Process with LLM (small batch)
    print("Processing with LLM...")
    try:
        events = llm_processor.extract_events(all_results[:10])  # Process first 10 results
        print(f"✅ Extracted {len(events)} events")
        print()
        
        # Check URL quality
        print("Checking URL quality...")
        generic_urls = 0
        eventdetail_urls = 0
        valid_urls = 0
        
        for event in events:
            url_lower = event.url.lower()
            
            # Check for generic pages
            if any(generic in url_lower for generic in ['/home', '/contact', '/about', '/events?']):
                generic_urls += 1
                print(f"  ⚠️  Generic URL: {event.event_title[:50]}... -> {event.url[:60]}...")
            
            # Check for eventdetail URLs
            if 'eventdetail' in url_lower:
                eventdetail_urls += 1
                print(f"  ✅ Eventdetail URL: {event.event_title[:50]}... -> {event.url[:60]}...")
            
            # Validate URL accessibility
            is_valid, error = url_validator.check_url_accessibility(event.url)
            if is_valid:
                valid_urls += 1
            else:
                print(f"  ❌ Invalid URL: {event.event_title[:50]}... -> {event.url[:60]}... ({error})")
        
        print()
        print("=" * 60)
        print("URL QUALITY SUMMARY")
        print("=" * 60)
        print(f"Total events: {len(events)}")
        print(f"Eventdetail URLs: {eventdetail_urls} ({eventdetail_urls/len(events)*100:.1f}%)")
        print(f"Generic URLs: {generic_urls} ({generic_urls/len(events)*100:.1f}%)")
        print(f"Valid/accessible URLs: {valid_urls}/{len(events)} ({valid_urls/len(events)*100:.1f}%)")
        print()
        
        if generic_urls == 0:
            print("✅ SUCCESS: No generic URLs found!")
        else:
            print(f"⚠️  WARNING: {generic_urls} generic URLs found (should be improved)")
        
        if eventdetail_urls > 0:
            print(f"✅ SUCCESS: {eventdetail_urls} eventdetail URLs found (best quality)")
        
        if valid_urls == len(events):
            print("✅ SUCCESS: All URLs are accessible!")
        else:
            print(f"⚠️  WARNING: {len(events) - valid_urls} URLs are not accessible")
        
    except Exception as e:
        print(f"❌ Error processing events: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_research()


