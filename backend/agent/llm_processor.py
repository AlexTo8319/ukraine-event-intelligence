"""LLM processing for extracting and filtering event data."""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from datetime import date, timedelta
from .models import Event, EventCategory

load_dotenv()


class LLMProcessor:
    """Processes search results using LLM to extract structured event data."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Using gpt-4o-mini for cost efficiency
    
    def extract_events(self, search_results: List[Dict]) -> List[Event]:
        """
        Extract structured event data from search results.
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of validated Event objects
        """
        if not search_results:
            return []
        
        # Prepare context for LLM
        context = self._prepare_context(search_results)
        
        # Call LLM to extract events
        extracted_data = self._call_llm(context)
        
        # Parse and validate events
        events = []
        for item in extracted_data:
            try:
                event = self._parse_event(item)
                if event and self._is_valid_event(event):
                    events.append(event)
            except Exception as e:
                print(f"Error parsing event: {str(e)}")
                continue
        
        return events
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """Prepare search results as context for LLM."""
        context_parts = []
        for i, result in enumerate(search_results[:20], 1):  # Limit to 20 results
            context_parts.append(
                f"Result {i}:\n"
                f"Title: {result.get('title', 'N/A')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Content: {result.get('content', '')[:1000]}\n"  # Limit content length
            )
        return "\n\n".join(context_parts)
    
    def _call_llm(self, context: str) -> List[Dict]:
        """Call OpenAI API to extract event information."""
        today = date.today()
        four_weeks_later = today + timedelta(days=28)
        
        system_prompt = """You are an expert event extraction system for urban planning, post-war recovery, and housing policy events in Ukraine.

Your task is to:
1. Identify professional events (conferences, workshops, seminars, webinars) related to:
   - Urban planning and spatial planning
   - Post-war recovery and reconstruction
   - Housing policy and affordable housing
   - Municipal governance and capacity building

2. Filter out:
   - Student projects or academic assignments
   - Protests or political rallies (unless they are professional policy forums)
   - Past events (only events in the next 4 weeks)
   - Non-Ukraine related events (unless they are international events specifically about Ukraine)

3. Extract structured data for each valid event:
   - event_title: Clear, descriptive title
   - event_date: Date in YYYY-MM-DD format (must be between today and 4 weeks from now)
   - event_time: Time in HH:MM format (24-hour, e.g., "14:30" or "09:00"). Use null if time is not available
   - organizer: Name of organizing entity
   - url: The source URL where event information was found
   - registration_url: Direct link to event registration page (if available, otherwise use the source URL)
   - category: One of: "Legislation", "Housing", "Recovery", "General"
   - is_online: Boolean indicating if event is online/virtual
   - target_audience: Comma-separated list of target audiences (e.g., "Donors, Government Officials, Architects" or "Architects, Urban Planners")
   - summary: 1-2 sentence description of the event in English

Return ONLY a valid JSON array of event objects. If no valid events are found, return an empty array [].

Example format:
[
  {
    "event_title": "International Conference on Post-War Urban Recovery in Ukraine",
    "event_date": "2024-12-15",
    "event_time": "09:00",
    "organizer": "Ministry of Communities and Territories Development",
    "url": "https://example.com/event-info",
    "registration_url": "https://example.com/register",
    "category": "Recovery",
    "is_online": false,
    "target_audience": "Donors, Government Officials, Architects",
    "summary": "This conference brings together international experts to discuss sustainable reconstruction strategies for Ukrainian cities."
  }
]"""

        user_prompt = f"""Today's date is {today.isoformat()}. Extract events from the following search results that occur between {today.isoformat()} and {four_weeks_later.isoformat()}.

Search Results:
{context}

Extract all valid professional events and return as JSON array."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                # Extract JSON from code block
                lines = result_text.split("\n")
                result_text = "\n".join(lines[1:-1]) if len(lines) > 2 else result_text
            
            result_json = json.loads(result_text)
            
            # Handle both {"events": [...]} and [...] formats
            if isinstance(result_json, dict) and "events" in result_json:
                return result_json["events"]
            elif isinstance(result_json, list):
                return result_json
            else:
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {str(e)}")
            print(f"Response was: {result_text[:500]}")
            return []
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            return []
    
    def _parse_event(self, data: Dict) -> Optional[Event]:
        """Parse a dictionary into an Event object."""
        try:
            from datetime import time as dt_time
            
            # Normalize category
            category_str = data.get("category", "General")
            try:
                category = EventCategory(category_str)
            except ValueError:
                category = EventCategory.GENERAL
            
            # Parse date
            date_str = data.get("event_date")
            if isinstance(date_str, str):
                event_date = date.fromisoformat(date_str)
            else:
                return None
            
            # Parse time
            event_time = None
            time_str = data.get("event_time")
            if time_str:
                if isinstance(time_str, str):
                    try:
                        # Handle HH:MM format
                        parts = time_str.split(":")
                        if len(parts) >= 2:
                            hour = int(parts[0])
                            minute = int(parts[1])
                            event_time = dt_time(hour, minute)
                    except (ValueError, IndexError):
                        pass
            
            # Get registration URL, fallback to source URL if not provided
            registration_url = data.get("registration_url", "").strip() or None
            if not registration_url:
                registration_url = data.get("url", "").strip() or None
            
            return Event(
                event_title=data.get("event_title", "").strip(),
                event_date=event_date,
                event_time=event_time,
                organizer=data.get("organizer", "").strip() or None,
                url=data.get("url", "").strip(),
                registration_url=registration_url,
                category=category,
                is_online=bool(data.get("is_online", False)),
                target_audience=data.get("target_audience", "").strip() or None,
                summary=data.get("summary", "").strip() or None
            )
        except Exception as e:
            print(f"Error parsing event data: {str(e)}")
            return None
    
    def _is_valid_event(self, event: Event) -> bool:
        """Validate that an event meets our criteria."""
        # Check date is in the future and within 4 weeks
        today = date.today()
        four_weeks_later = today + timedelta(days=28)
        
        if event.event_date < today:
            return False
        if event.event_date > four_weeks_later:
            return False
        
        # Check required fields
        if not event.event_title or len(event.event_title) < 5:
            return False
        
        if not event.url or not event.url.startswith(('http://', 'https://')):
            return False
        
        return True

