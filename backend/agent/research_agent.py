"""Main research agent that orchestrates the research workflow."""
import sys
import os
from typing import List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.search import SearchAgent
from agent.llm_processor import LLMProcessor
from agent.models import Event
from agent.duplicate_detector import DuplicateDetector
from agent.url_validator import URLValidator
from agent.translator import Translator
from database.client import DatabaseClient


class ResearchAgent:
    """Main agent that orchestrates the research workflow."""
    
    def __init__(self):
        self.search_agent = SearchAgent()
        self.llm_processor = LLMProcessor()
        self.db_client = DatabaseClient()
        self.duplicate_detector = DuplicateDetector(title_similarity_threshold=0.85, date_tolerance_days=0)
        self.url_validator = URLValidator(timeout=5, max_redirects=5)
        self.translator = Translator()
    
    def run(self) -> dict:
        """
        Execute the complete research workflow.
        
        Returns:
            Dictionary with execution statistics
        """
        print(f"[{datetime.now()}] Starting research agent...")
        
        stats = {
            "queries_searched": 0,
            "search_results": 0,
            "events_extracted": 0,
            "duplicates_filtered": 0,
            "invalid_urls_filtered": 0,
            "events_saved": 0,
            "tavily_credits_used": 0,  # Estimated: ~10 credits per query with advanced search
            "errors": []
        }
        
        try:
            # Get search queries
            queries = self.search_agent.get_search_queries()
            print(f"[{datetime.now()}] Generated {len(queries)} search queries")
            
            all_search_results = []
            
            # Execute searches
            for i, query in enumerate(queries, 1):
                print(f"[{datetime.now()}] Searching query {i}/{len(queries)}: {query[:50]}...")
                try:
                    results = self.search_agent.search(query, max_results=10)
                    all_search_results.extend(results)
                    stats["queries_searched"] += 1
                    stats["search_results"] += len(results)
                    # Estimate Tavily credits: ~10 credits per query with advanced search depth
                    stats["tavily_credits_used"] += 10
                except Exception as e:
                    error_msg = f"Error searching query '{query}': {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    stats["errors"].append(error_msg)
            
            print(f"[{datetime.now()}] Collected {len(all_search_results)} total search results")
            
            # Remove duplicates based on URL
            unique_results = {}
            for result in all_search_results:
                url = result.get("url", "")
                if url and url not in unique_results:
                    unique_results[url] = result
            
            print(f"[{datetime.now()}] Found {len(unique_results)} unique URLs")
            
            # Process with LLM in batches
            batch_size = 20
            all_events = []
            unique_results_list = list(unique_results.values())
            
            for i in range(0, len(unique_results_list), batch_size):
                batch = unique_results_list[i:i + batch_size]
                print(f"[{datetime.now()}] Processing batch {i//batch_size + 1}/{(len(unique_results_list) + batch_size - 1)//batch_size}")
                
                try:
                    events = self.llm_processor.extract_events(batch)
                    all_events.extend(events)
                    stats["events_extracted"] += len(events)
                except Exception as e:
                    error_msg = f"Error processing batch: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    stats["errors"].append(error_msg)
            
            print(f"[{datetime.now()}] Extracted {len(all_events)} valid events")
            
            # Relevance check for new events (balanced - reject clearly irrelevant, keep urban/recovery)
            print(f"[{datetime.now()}] Running relevance checks...")
            validated_events = []
            for event in all_events:
                # Quick relevance check (don't fetch URLs for all events - too slow)
                title_lower = event.event_title.lower()
                summary_lower = (event.summary or "").lower()
                combined = f"{title_lower} {summary_lower}"
                
                # Check for clearly irrelevant topics - these are NOT about urban planning/recovery
                clearly_irrelevant = [
                    'teacher education', 'pedagogy', 'teaching methods',
                    'spanish language', 'latin american studies', 'language studies',
                    'biotechnology', 'biodiversity', 'biology',
                    'artificial intelligence', 'software engineering', 'machine learning',
                    'multilingual education', 'big data',
                    'medical research', 'healthcare',
                    'benefit concert', 'film for ukraine',  # Charity events, not urban planning
                    'blockchain', 'cryptocurrency', 'crypto', 'bitcoin', 'ethereum',
                    'fintech', 'defi', 'nft', 'web3'  # Crypto/finance tech not relevant
                ]
                is_clearly_irrelevant = any(kw in combined for kw in clearly_irrelevant)
                
                # Check for urban/recovery keywords (VERY EXPANDED)
                urban_keywords = ['urban', 'city', 'planning', 'recovery', 'housing', 'reconstruction', 'municipal', 
                                 'local government', 'decentralization', 'forum', 'conference', 'sumy', 'digital',
                                 'capacity', 'building', 'green', 'sustainable', 'resilience', 'infrastructure',
                                 'workshop', 'seminar', 'webinar', 'meeting', 'ukraine', 'ukrainian', 'europe',
                                 'partnership', 'cooperation', 'investment', 'finance', 'project', 'program',
                                 'energy', 'efficiency', 'waste', 'management', 'smart', 'affordable',
                                 'rebuild', 'відбудова', 'місто', 'громада', 'розвиток']
                has_urban = any(kw in combined for kw in urban_keywords)
                
                # Check for event types (forums, conferences, etc.) - these are usually relevant
                event_types = ['forum', 'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'summit']
                has_event_type = any(et in title_lower for et in event_types)
                
                # Check for location keywords - might be relevant
                location_keywords = ['ukraine', 'ukrainian', 'sumy', 'kyiv', 'lviv', 'kharkiv', 'odessa', 'europe']
                has_location = any(loc in combined for loc in location_keywords)
                
                # Reject if clearly irrelevant AND has no urban keywords
                # (event type and location alone are not enough for irrelevant topics)
                if is_clearly_irrelevant and not has_urban:
                    print(f"  ⚠️  Rejected clearly irrelevant: {event.event_title[:50]}...")
                    stats["invalid_urls_filtered"] += 1
                    continue
                
                # Keep everything else (forums, conferences, digital events, Ukraine-related, etc.)
                validated_events.append(event)
            
            print(f"[{datetime.now()}] After relevance check: {len(validated_events)} events")
            all_events = validated_events
            
            # FORCE TRANSLATION of all event fields to English
            print(f"[{datetime.now()}] Translating events to English...")
            translation_count = 0
            for event in all_events:
                try:
                    # Translate title
                    if self.translator.is_ukrainian(event.event_title):
                        old_title = event.event_title[:30]
                        event.event_title = self.translator.translate(event.event_title, "event title")
                        print(f"  ✅ Title: {old_title}... → {event.event_title[:30]}...")
                        translation_count += 1
                    
                    # Translate organizer
                    if event.organizer and self.translator.is_ukrainian(event.organizer):
                        event.organizer = self.translator.translate(event.organizer, "organizer name")
                    
                    # Translate summary
                    if event.summary and self.translator.is_ukrainian(event.summary):
                        event.summary = self.translator.translate(event.summary, "event description")
                except Exception as e:
                    print(f"  ⚠️ Translation error for '{event.event_title[:30]}...': {str(e)[:50]}")
            
            print(f"[{datetime.now()}] Translated {translation_count} events")
            
            # Get existing events for duplicate checking (check all events, not just upcoming)
            print(f"[{datetime.now()}] Fetching existing events for duplicate detection...")
            existing_events = self.db_client.get_all_events(limit=1000)  # Get full event data including URL
            existing_events_dicts = [
                {
                    "event_title": e.get("event_title", ""),
                    "event_date": e.get("event_date", ""),
                    "url": e.get("url", "")  # Include URL for duplicate checking
                }
                for e in existing_events
            ]
            print(f"[{datetime.now()}] Found {len(existing_events_dicts)} existing events for duplicate check")
            
            # Convert events to dicts for duplicate checking
            new_events_dicts = [event.to_dict() for event in all_events]
            
            # Check for duplicates
            print(f"[{datetime.now()}] Checking for duplicates...")
            duplicate_result = self.duplicate_detector.find_duplicates(new_events_dicts, existing_events_dicts)
            unique_events_dicts = duplicate_result["unique"]
            duplicates_count = len(duplicate_result["duplicates"])
            
            print(f"[{datetime.now()}] Found {duplicates_count} duplicates, {len(unique_events_dicts)} unique events")
            
            if duplicates_count > 0:
                stats["duplicates_filtered"] = duplicates_count
            
            # Validate URLs before saving
            print(f"[{datetime.now()}] Validating URLs...")
            urls_to_validate = []
            for event_dict in unique_events_dicts:
                urls_to_validate.append(event_dict.get("url"))
                if event_dict.get("registration_url"):
                    urls_to_validate.append(event_dict.get("registration_url"))
            
            url_validation_results = self.url_validator.validate_urls(
                urls_to_validate,
                check_accessibility=True
            )
            
            # Filter out events with invalid URLs
            valid_events = []
            invalid_urls_count = 0
            for event_dict in unique_events_dicts:
                url = event_dict.get("url")
                reg_url = event_dict.get("registration_url")
                
                # Check main URL
                url_valid, url_error = url_validation_results.get(url, (False, "Not checked"))
                if not url_valid:
                    print(f"[WARNING] Invalid URL for '{event_dict.get('event_title', '')[:50]}...': {url_error}")
                    invalid_urls_count += 1
                    continue
                
                # Check registration URL if provided
                if reg_url and reg_url != url:
                    reg_url_valid, reg_url_error = url_validation_results.get(reg_url, (False, "Not checked"))
                    if not reg_url_valid:
                        print(f"[WARNING] Invalid registration URL, using main URL: {reg_url_error}")
                        event_dict["registration_url"] = url  # Fallback to main URL
                
                valid_events.append(event_dict)
            
            if invalid_urls_count > 0:
                stats["invalid_urls_filtered"] = invalid_urls_count
                print(f"[{datetime.now()}] Filtered out {invalid_urls_count} events with invalid URLs")
            
            print(f"[{datetime.now()}] Saving {len(valid_events)} valid, unique events to database...")
            
            # FINAL TRANSLATION SAFETY NET - right before save
            print(f"[{datetime.now()}] Final translation check before save...")
            for event_dict in valid_events:
                try:
                    # Force translate any remaining Ukrainian
                    if self.translator.is_ukrainian(event_dict.get('event_title', '')):
                        old_title = event_dict['event_title'][:30]
                        event_dict['event_title'] = self.translator.translate(event_dict['event_title'], "event title")
                        print(f"  🔄 Force-translated: {old_title}... → {event_dict['event_title'][:30]}...")
                    
                    if self.translator.is_ukrainian(event_dict.get('organizer', '')):
                        event_dict['organizer'] = self.translator.translate(event_dict['organizer'], "organizer name")
                    
                    if self.translator.is_ukrainian(event_dict.get('summary', '')):
                        event_dict['summary'] = self.translator.translate(event_dict['summary'], "event description")
                except Exception as e:
                    print(f"  ⚠️ Force translation error: {str(e)[:50]}")
            
            # Save to database
            for event_dict in valid_events:
                try:
                    self.db_client.upsert_event(event_dict)
                    stats["events_saved"] += 1
                except Exception as e:
                    error_msg = f"Error saving event '{event_dict.get('event_title', 'Unknown')}': {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    stats["errors"].append(error_msg)
            
            print(f"[{datetime.now()}] Saved {stats['events_saved']} events to database")
            
            # Run smart corrector to verify and fix any remaining issues
            print(f"[{datetime.now()}] Running smart event corrector...")
            try:
                from smart_event_corrector import SmartEventCorrector
                corrector = SmartEventCorrector()
                
                # Fetch all events from DB for correction
                all_db_events = self.db_client.get_all_events(limit=1000)
                corrections_made = 0
                removals_made = 0
                
                for event in all_db_events:
                    result = corrector.verify_and_correct_event(event)
                    
                    if result["action"] == "update" and result["corrections"]:
                        # Apply corrections
                        try:
                            self.db_client.client.table("events").update(result["corrections"]).eq("id", event["id"]).execute()
                            corrections_made += 1
                        except:
                            pass
                    elif result["action"] == "remove":
                        # Remove unfixable events
                        try:
                            self.db_client.delete_event(event["id"])
                            removals_made += 1
                        except:
                            pass
                
                if corrections_made > 0:
                    print(f"[{datetime.now()}] Smart corrector: {corrections_made} events corrected")
                if removals_made > 0:
                    print(f"[{datetime.now()}] Smart corrector: {removals_made} unfixable events removed")
                    
            except Exception as e:
                print(f"[{datetime.now()}] Smart corrector error (non-fatal): {str(e)}")
            
            print(f"[{datetime.now()}] Research agent completed successfully!")
            
        except Exception as e:
            error_msg = f"Fatal error in research agent: {str(e)}"
            print(f"[FATAL ERROR] {error_msg}")
            stats["errors"].append(error_msg)
        
        return stats


def main():
    """Entry point for the research agent."""
    agent = ResearchAgent()
    stats = agent.run()
    
    # Print summary
    print("\n" + "="*50)
    print("EXECUTION SUMMARY")
    print("="*50)
    print(f"Queries searched: {stats['queries_searched']}")
    print(f"Search results: {stats['search_results']}")
    print(f"Events extracted: {stats['events_extracted']}")
    if stats.get('duplicates_filtered', 0) > 0:
        print(f"Duplicates filtered: {stats['duplicates_filtered']}")
    if stats.get('invalid_urls_filtered', 0) > 0:
        print(f"Invalid URLs filtered: {stats['invalid_urls_filtered']}")
    print(f"Events saved: {stats['events_saved']}")
    if stats['errors']:
        print(f"Errors: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
    print("="*50)


if __name__ == "__main__":
    main()

