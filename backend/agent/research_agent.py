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
from database.client import DatabaseClient


class ResearchAgent:
    """Main agent that orchestrates the research workflow."""
    
    def __init__(self):
        self.search_agent = SearchAgent()
        self.llm_processor = LLMProcessor()
        self.db_client = DatabaseClient()
    
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
            "events_saved": 0,
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
            
            # Save to database
            for event in all_events:
                try:
                    event_dict = event.to_dict()
                    self.db_client.upsert_event(event_dict)
                    stats["events_saved"] += 1
                except Exception as e:
                    error_msg = f"Error saving event '{event.event_title}': {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    stats["errors"].append(error_msg)
            
            print(f"[{datetime.now()}] Saved {stats['events_saved']} events to database")
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
    print(f"Events saved: {stats['events_saved']}")
    if stats['errors']:
        print(f"Errors: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
    print("="*50)


if __name__ == "__main__":
    main()

