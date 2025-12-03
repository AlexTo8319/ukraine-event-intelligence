"""LLM processing for extracting and filtering event data."""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from datetime import date, timedelta
from .models import Event, EventCategory
from .url_extractor import URLExtractor
from .translator import Translator
from .date_validator import DateValidator
from .url_follower import URLFollower
from .url_content_analyzer import URLContentAnalyzer

load_dotenv()


class LLMProcessor:
    """Processes search results using LLM to extract structured event data."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Using gpt-4o-mini for cost efficiency
        self.url_extractor = URLExtractor()
        self.translator = Translator()
        self.date_validator = DateValidator()
        self.url_follower = URLFollower()
        self.url_analyzer = URLContentAnalyzer()
    
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
                if event:
                    # Post-process: try to improve URL if it looks like a listing page
                    event = self._improve_event_url(event, search_results)
                    
                    # Validate date matches URL content (check if it's a past event)
                    is_past, reason = self.date_validator.check_if_past_event(event.url, event.event_date)
                    if is_past:
                        print(f"  ⚠️  Rejected past event: {event.event_title[:50]}... ({reason})")
                        continue
                    
                    # Additional validation: Analyze URL content
                    analysis = self.url_analyzer.analyze_url(event.url, event.event_title, event.event_date)
                    
                    # Reject if it's a program description (not a specific event)
                    if analysis.get("is_program_description") and not analysis.get("extracted_date"):
                        print(f"  ⚠️  Rejected program description (not specific event): {event.event_title[:50]}...")
                        continue
                    
                    # Reject if URL is invalid or shows past event
                    if not analysis.get("is_valid"):
                        error = analysis.get("error", "Unknown error")
                        print(f"  ⚠️  Rejected invalid URL: {event.event_title[:50]}... ({error})")
                        continue
                    
                    # Check if date mismatch is too large (years apart or in the past)
                    extracted_date = analysis.get("extracted_date")
                    if extracted_date and event.event_date:
                        # Only reject if extracted date is in the past (more than 1 year ago)
                        current_year = date.today().year
                        if extracted_date.year < current_year - 1:
                            print(f"  ⚠️  Rejected date mismatch (past year): {event.event_title[:50]}... (extracted: {event.event_date}, URL: {extracted_date})")
                            continue
                        # For future dates, allow small differences (might be multi-day events or timezone issues)
                        year_diff = abs(extracted_date.year - event.event_date.year)
                        if year_diff > 1:  # More than 1 year difference
                            print(f"  ⚠️  Date difference: {event.event_date} vs {extracted_date} (keeping - might be valid)")
                        # Don't reject for year differences of 1 or less
                    
                    # Additional validation: Check if URL is accessible
                    try:
                        response = self.url_follower.session.head(event.url, timeout=5, allow_redirects=True)
                        if response.status_code >= 400:
                            print(f"  ⚠️  Rejected event with inaccessible URL: {event.event_title[:50]}... (HTTP {response.status_code})")
                            continue
                    except:
                        # If we can't check, proceed (don't reject on network errors)
                        pass
                    
                    if self._is_valid_event(event):
                        events.append(event)
            except Exception as e:
                print(f"Error parsing event: {str(e)}")
                continue
        
        return events
    
    def _improve_event_url(self, event: Event, search_results: List[Dict]) -> Event:
        """
        Try to improve event URL using multiple strategies to find exact event URLs.
        Strategy 1: Extract URLs from search results (most reliable)
        Strategy 2: Follow aggregator pages
        Strategy 3: Analyze URL content to find better URLs and validate dates
        """
        event_url = event.url.lower()
        original_url = event.url
        
        # Strategy 1: Check search results for better URLs first (most reliable)
        event_title_lower = event.event_title.lower()
        title_words = [w for w in event_title_lower.split() if len(w) > 4]
        
        best_url = None
        best_score = 0
        
        for result in search_results:
            result_url = result.get('url', '')
            # Use raw_content first (HTML), fallback to content (text)
            content = result.get('raw_content', '') or result.get('content', '')
            
            if not content:
                continue
            
            # Extract ALL URLs from content (not just event-related)
            all_urls = self.url_extractor.extract_urls_from_html(content, result_url)
            if not all_urls:
                all_urls = self.url_extractor.extract_urls_from_text(content, result_url)
            
            # Score each URL
            for url in all_urls:
                url_lower = url.lower()
                score = 0
                
                # CRITICAL: Always prioritize eventdetail URLs
                if 'eventdetail' in url_lower:
                    score += 30  # Very high priority
                    # Don't skip eventdetail URLs even if they have /contact or /about in path
                    # (e.g., conferenceineurope.net/contact might link to eventdetail/3264530)
                
                # Skip non-event URLs (but allow eventdetail and /event/ patterns)
                if any(skip in url_lower for skip in ['/contact', '/about', '/home$', '/news/', '/article/', 'mailto:', 'tel:']):
                    if 'eventdetail' not in url_lower and '/event/' not in url_lower:
                        continue
                
                # High score for eventdetail pattern (already added above, but ensure it's prioritized)
                if 'eventdetail' in url_lower:
                    score += 20  # Additional boost (total +50 for eventdetail)
                
                # Score based on title match
                if title_words:
                    url_matches = sum(1 for word in title_words if word in url_lower)
                    score += url_matches * 5
                    
                    # Check context around URL in content
                    content_lower = content.lower()
                    url_pos = content_lower.find(url_lower)
                    if url_pos != -1:
                        context = content_lower[max(0, url_pos-200):min(len(content_lower), url_pos+len(url)+200)]
                        context_matches = sum(1 for word in title_words if word in context)
                        score += context_matches * 2
                
                # Boost for event keywords
                if any(kw in url_lower for kw in ['conference', 'workshop', 'seminar', 'webinar', 'forum', 'event']):
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_url = url
        
        # Strategy 2: If URL is aggregator or non-event page, follow it
        aggregator_indicators = [
            '/events', '/event-list', '/calendar', '/upcoming-events',
            '/home', '/events?', '/contact', '/about'
        ]
        is_aggregator = any(indicator in event_url for indicator in aggregator_indicators)
        
        # Also check if URL doesn't look like an event page
        event_page_indicators = ['eventdetail', '/event/', '/events/', 'conference', 'workshop', 'seminar', 'webinar', 'forum']
        looks_like_event_page = any(ind in event_url for ind in event_page_indicators)
        
        # If it's not an event page and not an aggregator, it might be wrong (like /contact)
        if not looks_like_event_page and not is_aggregator:
            # Check if it's a generic page that should be improved
            generic_pages = ['/contact', '/about', '/home']
            if any(page in event_url for page in generic_pages):
                is_aggregator = True  # Treat as aggregator to trigger URL following
        
        if is_aggregator and (not best_url or best_score < 10):
            print(f"  Following aggregator/listing page: {event.url[:60]}...")
            # Increase max_depth to 3 for listing pages to go deeper and extract event details
            max_depth = 3 if any(ind in event.url.lower() for ind in ['/events', '/event-list', '/calendar']) else 2
            direct_url = self.url_follower.find_direct_event_url(event.url, event.event_title, max_depth=max_depth)
            if direct_url and direct_url != event.url:
                # Score this URL too
                url_lower = direct_url.lower()
                score = 10 if 'eventdetail' in url_lower else 5
                if title_words:
                    score += sum(1 for word in title_words if word in url_lower) * 3
                
                if score > best_score:
                    best_url = direct_url
                    best_score = score
        
        # Strategy 3: Analyze URL content to find better URL and validate date
        if best_url or is_aggregator:
            url_to_analyze = best_url if best_url else event.url
            print(f"  Analyzing URL content: {url_to_analyze[:60]}...")
            analysis = self.url_analyzer.analyze_url(url_to_analyze, event.event_title, event.event_date)
            
            if analysis.get("found_better_url"):
                best_url = analysis["actual_url"]
                print(f"  Found better URL in content: {best_url[:60]}...")
            
            # Check if date in content matches extracted date
            extracted_date = analysis.get("extracted_date")
            if extracted_date and event.event_date:
                date_diff = abs((extracted_date - event.event_date).days)
                if date_diff > 1:  # More than 1 day difference
                    print(f"  ⚠️  Date mismatch: extracted {event.event_date}, URL shows {extracted_date}")
                    # Update date if URL content is more reliable (especially for week-long events)
                    if date_diff <= 7:  # Within a week, probably correct (week-long event)
                        # Prefer earlier date (start of week)
                        if extracted_date < event.event_date:
                            event.event_date = extracted_date
                            print(f"  ✅ Updated date to start of week: {extracted_date}")
                        elif date_diff <= 1:
                            # Very close, use URL date
                            event.event_date = extracted_date
                            print(f"  ✅ Updated date to match URL content: {extracted_date}")
        
        # Apply best URL found (lower threshold for eventdetail URLs)
        threshold = 3 if best_url and 'eventdetail' in best_url.lower() else 5
        if best_url and best_url != original_url and best_score >= threshold:
            print(f"  ✅ Improved URL: {original_url[:50]}... → {best_url[:60]}...")
            event.url = best_url
            if not event.registration_url or event.registration_url == original_url:
                event.registration_url = best_url
            return event
        
        return event  # No improvement found, keep original
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """Prepare search results as context for LLM, including extracted URLs."""
        context_parts = []
        for i, result in enumerate(search_results[:20], 1):  # Limit to 20 results
            listing_url = result.get('url', '')
            content = result.get('content', '')
            raw_content = result.get('raw_content', '')
            
            # Extract URLs from content (prioritize eventdetail URLs)
            extracted_urls = []
            all_urls = []
            
            if raw_content:
                # Extract ALL URLs first
                all_urls = self.url_extractor.extract_urls_from_html(raw_content, listing_url)
                # Then filter for event URLs
                extracted_urls = self.url_extractor.extract_event_urls(raw_content, listing_url)
            
            if not all_urls and content:
                all_urls = self.url_extractor.extract_urls_from_text(content, listing_url)
                extracted_urls = self.url_extractor.extract_event_urls(content, listing_url)
            
            # Prioritize eventdetail URLs
            eventdetail_urls = [url for url in all_urls if 'eventdetail' in url.lower()]
            if eventdetail_urls:
                extracted_urls = eventdetail_urls + [url for url in extracted_urls if 'eventdetail' not in url.lower()]
            
            # Build context
            context_text = f"Result {i}:\n"
            context_text += f"Title: {result.get('title', 'N/A')}\n"
            context_text += f"Listing URL: {listing_url}\n"
            
            # Add extracted URLs if found (highlight eventdetail URLs)
            if extracted_urls:
                urls_to_show = extracted_urls[:5]
                eventdetail_highlighted = [f"**{url}**" if 'eventdetail' in url.lower() else url for url in urls_to_show]
                context_text += f"Event URLs found in content (prioritize eventdetail URLs marked with **): {', '.join(eventdetail_highlighted)}\n"
            
            context_text += f"Content: {content[:1500]}\n"  # Increased limit to include more URLs
            
            context_parts.append(context_text)
        return "\n\n".join(context_parts)
    
    def _call_llm(self, context: str) -> List[Dict]:
        """Call OpenAI API to extract event information."""
        today = date.today()
        six_months_later = today + timedelta(days=180)  # 6 months
        
        system_prompt = """You are an expert event extraction system for urban planning, post-war recovery, and housing policy events in Ukraine.

CRITICAL: You MUST ONLY extract ACTUAL EVENTS (conferences, workshops, seminars, webinars, forums, training sessions).
You MUST REJECT news articles, blog posts, opinion pieces, announcements, policy updates, or any non-event content.

Your task is to:
1. Identify ONLY professional events (conferences, workshops, seminars, webinars, forums, training) related to:
   - Urban planning and spatial planning
   - Post-war recovery and reconstruction
   - Housing policy and affordable housing
   - Municipal governance and capacity building

IMPORTANT SCOPE FILTERING:
- EXCLUDE very local/regional events (e.g., regional council meetings, local municipality meetings)
- EXCLUDE events limited to a single oblast/region unless they are major conferences
- INCLUDE national and international events
- INCLUDE major regional conferences/forums (but not routine administrative meetings)
- EXCLUDE routine administrative meetings (рада, засідання ради, etc. unless it's a major forum)

2. STRICTLY FILTER OUT (DO NOT EXTRACT):
   - News articles or news stories (even if about events)
   - Blog posts or opinion pieces
   - Policy announcements or program launches (e.g., "Compensation Program", "Housing Program", "Starting December 1")
   - Program/initiative launches (NOT events, even if they have dates)
   - Research papers or publications
   - General information pages
   - Student projects or academic assignments
   - Protests or political rallies (unless they are professional policy forums)
   - Past events (only events in the next 6 months)
   - Non-Ukraine related events (unless they are international events specifically about Ukraine)
   - Pages that only mention events but don't describe actual upcoming events
   - Government program announcements (e.g., "IDPs can submit applications" = program, not event)

3. VALIDATION RULES:
   - Event MUST have a specific date in the future (within 6 months)
   - Event MUST be a scheduled gathering/meeting (not just a topic discussion)
   - Event MUST have clear indication it's an actual event (words like: conference, workshop, seminar, webinar, forum, training, meeting, event)
   - If content is primarily news/informational, REJECT it even if it mentions events
   - REJECT program/initiative launches (e.g., "Program starts", "Applications open", "Compensation Program")
   - REJECT if it's about submitting applications or accessing services (these are programs, not events)
   - For date ranges (e.g., "December 1-5" or "01-05 ГРУДНЯ"), use the START DATE (first date), not the end date

4. Extract structured data for each valid event:
   - event_title: Clear, descriptive title IN ENGLISH (translate from Ukrainian if needed)
   - event_date: Date in YYYY-MM-DD format (must be between today and 6 months from now). CRITICAL: 
     * **EXTRACT THE EVENT DATE, NOT THE ARTICLE PUBLICATION DATE**
     * Look for dates after "Дата та час:", "Date:", "Event date:", "When:" markers
     * IGNORE dates near "на читання", "reading time", "опубліковано", "published" (these are article dates)
     * Example: If you see "28 Листопада, 2025 на читання" → this is ARTICLE DATE, ignore it
     * Example: If you see "Дата та час: 4 грудня 2025 року, об 11:00" → this is EVENT DATE (Dec 4, 2025)
     * Prioritize dates with time information (e.g., "4 грудня 2025 року, об 11:00")
     * Verify the date matches the actual event date in the content
     * For date ranges (e.g., "December 1-5" or "01-05 ГРУДНЯ"), use the START DATE (December 1), NOT the end date
     * If the URL points to a past event, DO NOT extract it
     * If content shows a week-long event, use the first day of the week
   - event_time: Time in HH:MM format (24-hour, e.g., "14:30" or "09:00"). Use null if time is not available
   - organizer: Name of organizing entity IN ENGLISH
   - url: The DIRECT event page URL (NOT the listing page URL, NOT a news article URL). Verify the URL actually points to an event page, not a news article. If the URL is a news article about a past event, DO NOT extract it.
   - registration_url: Direct link to event registration page. If the content contains a registration link, use that. Otherwise, use the direct event URL. If neither is available, use the listing URL as fallback.
   - category: One of: "Legislation", "Housing", "Recovery", "General"
   - is_online: Boolean indicating if event is online/virtual
   - target_audience: Comma-separated list of target audiences (e.g., "Donors, Government Officials, Architects" or "Architects, Urban Planners")
   - summary: 1-2 sentence description of the event IN ENGLISH (translate from Ukrainian if needed)

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

        user_prompt = f"""Today's date is {today.isoformat()}. Extract ONLY actual events (conferences, workshops, seminars, webinars) from the following search results that occur between {today.isoformat()} and {six_months_later.isoformat()}.

CRITICAL EXTRACTION RULES:

0. URL PRIORITY (MOST IMPORTANT):
   - If "Event URLs found in content" shows URLs marked with ** (eventdetail URLs), USE THOSE FIRST
   - eventdetail URLs (e.g., eventdetail/3264530) are ALWAYS the correct event page
   - If eventdetail URL is available, use it instead of listing/aggregator URLs
   - Only use listing URLs if no eventdetail URL is found

1. DATE VALIDATION (CRITICAL - MOST IMPORTANT):
   - **ALWAYS extract the EVENT DATE, NOT the article/publication date**
   - Look for event date markers: "Дата та час:", "Date:", "Event date:", "When:", "коли:", "відбудеться:"
   - IGNORE dates near publication indicators: "на читання", "reading time", "опубліковано", "published", "дата публікації"
   - Prioritize dates that appear with time information (e.g., "4 грудня 2025 року, об 11:00" = Dec 4, 2025)
   - If you see "28 Листопада, 2025" near "на читання" (reading time) → this is the ARTICLE DATE, NOT the event date
   - If you see "4 грудня 2025 року, об 11:00" after "Дата та час:" → this is the EVENT DATE
   - Verify the event date in the content matches the URL content EXACTLY
   - If the URL points to a news article about a PAST event, DO NOT extract it
   - If the URL shows the event already happened, DO NOT extract it
   - If the content mentions "was held", "took place", "вже відбулося", "already happened" - REJECT
   - For webinars: Check the actual webinar date in the URL content, not just the search result
   - Only extract events with FUTURE dates that are CONFIRMED in the URL content
   - If date is unclear or conflicting, REJECT the event

2. URL VALIDATION:
   - If a search result shows a LISTING PAGE, look for the DIRECT EVENT URL in the content
   - The "url" field should be the DIRECT event page URL, NOT the listing page URL, NOT a news article URL
   - If the URL is a news article (contains "/news/" or is about a past event), DO NOT extract it
   - Look for URLs in the content that contain event-related keywords (event, conference, workshop, register, etc.)
   - If "Event URLs found in content" is provided, prioritize those URLs over the listing URL
   - Verify the URL actually describes an upcoming event, not a news report about a past event

3. SCOPE FILTERING:
   - EXCLUDE very local/regional events (e.g., "Засідання архітектурно-містобудівної ради" in a specific oblast)
   - EXCLUDE routine administrative meetings (рада, засідання ради) unless they are major forums
   - INCLUDE national and international events
   - INCLUDE major regional conferences (but not routine meetings)

4. TRANSLATION:
   - All titles, organizers, and summaries must be in ENGLISH
   - Translate from Ukrainian to English if needed
   - Keep translations professional and accurate

IMPORTANT:
- REJECT any news articles, blog posts, or informational content
- REJECT past events (even if mentioned in search results)
- REJECT very local/narrow events (single oblast routine meetings)
- ONLY extract content that describes an actual scheduled FUTURE event with a specific date
- If a result is primarily news/information about events (not the event itself), skip it
- Be conservative: if unsure whether something is an event or news, skip it
- ALWAYS extract the direct event URL, not the listing page URL or news article URL

Search Results:
{context}

Extract all valid professional events (not news articles) and return as JSON array. If no valid events found, return empty array []."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1  # Lower temperature to reduce hallucinations
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                # Extract JSON from code block
                lines = result_text.split("\n")
                result_text = "\n".join(lines[1:-1]) if len(lines) > 2 else result_text
            
            try:
                result_json = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from text if wrapped
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                else:
                    print(f"Failed to parse JSON from LLM response")
                    return []
            
            # Handle both {"events": [...]} and [...] formats
            if isinstance(result_json, dict):
                if "events" in result_json:
                    return result_json["events"]
                elif "data" in result_json:
                    return result_json["data"]
                else:
                    # If dict but no events key, might be malformed
                    print(f"Warning: LLM returned dict without 'events' key: {list(result_json.keys())}")
                    return []
            elif isinstance(result_json, list):
                return result_json
            else:
                print(f"Warning: LLM returned unexpected format: {type(result_json)}")
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
            
            # Get URLs
            event_url = data.get("url", "").strip() or None
            registration_url = data.get("registration_url", "").strip() or None
            
            # If registration_url is not provided, use event_url
            if not registration_url:
                registration_url = event_url
            
            # If event_url is a listing page, try to extract better URL from content
            # (This is a fallback - LLM should have already extracted the direct URL)
            if event_url and ("/events" in event_url.lower() or "/event" in event_url.lower()):
                # Might be a listing page, but we'll trust the LLM extraction
                pass
            
            # ALWAYS translate Ukrainian text to English
            event_title = data.get("event_title", "").strip()
            if event_title and self.translator.is_ukrainian(event_title):
                translated = self.translator.translate(event_title, "event title")
                if translated and translated != event_title:
                    print(f"  📝 Translated title: {event_title[:40]}... → {translated[:40]}...")
                    event_title = translated
            
            organizer = data.get("organizer", "").strip() or None
            if organizer and self.translator.is_ukrainian(organizer):
                translated = self.translator.translate(organizer, "organizer name")
                if translated:
                    organizer = translated
            
            summary = data.get("summary", "").strip() or None
            if summary and self.translator.is_ukrainian(summary):
                translated = self.translator.translate(summary, "event description")
                if translated:
                    summary = translated
            
            return Event(
                event_title=event_title,
                event_date=event_date,
                event_time=event_time,
                organizer=organizer,
                url=data.get("url", "").strip(),
                registration_url=registration_url,
                category=category,
                is_online=bool(data.get("is_online", False)),
                target_audience=data.get("target_audience", "").strip() or None,
                summary=summary
            )
        except Exception as e:
            print(f"Error parsing event data: {str(e)}")
            return None
    
    def _is_valid_event(self, event: Event) -> bool:
        """Validate that an event meets our criteria."""
        # Check date is in the future and within 6 months
        today = date.today()
        six_months_later = today + timedelta(days=180)
        
        if event.event_date < today:
            return False
        if event.event_date > six_months_later:
            return False
        
        # Check required fields
        if not event.event_title or len(event.event_title) < 5:
            return False
        
        # Check title doesn't look like news/article/program
        title_lower = event.event_title.lower()
        news_indicators = ["news", "article", "blog", "report", "analysis", "opinion", "announcement"]
        program_indicators = ["compensation program", "housing program", "program for", "applications open", "submitting applications", "can submit", "program starts"]
        event_indicators = ["conference", "workshop", "seminar", "webinar", "forum", "training", "meeting", "event", "symposium", "summit"]
        
        # Reject program announcements
        if any(indicator in title_lower for indicator in program_indicators):
            return False
        
        if any(indicator in title_lower for indicator in news_indicators):
            # But allow if it's clearly an event (e.g., "Conference News" is OK if it's actually a conference)
            if not any(indicator in title_lower for indicator in event_indicators):
                return False
        
        # Check URL doesn't point to news article
        url_lower = event.url.lower()
        if "/news/" in url_lower or "/article/" in url_lower or "/blog/" in url_lower:
            print(f"  ⚠️  Rejecting news URL pattern: {event.url[:60]}")
            return False
        
        # STRICT: Reject URLs with date patterns (news articles)
        # Pattern: /2025/09/17/ indicates publication date, not event
        import re
        date_in_url = re.search(r'/\d{4}/\d{2}/\d{2}/', event.url)
        if date_in_url:
            # Check if URL is from an allowed domain (some event pages have dates)
            allowed_date_urls = ['facebook.com', 'instagram.com', 'gov.ua', 'irf.ua']
            if not any(d in url_lower for d in allowed_date_urls):
                print(f"  ⚠️  Rejecting URL with date pattern (news article): {event.url[:60]}")
                return False
        
        # STRICT: Reject news aggregator sites
        news_aggregators = [
            'kyivindependent.com',
            'pravda.com.ua',
            'ukrinform.ua',
            'unian.ua',
            'korrespondent.net',
            'thepeninsulaqatar.com',
            'zygonjournal.org',
            'hmarochos.kiev.ua',  # News blog site
            'misto.media',  # News site
            'archi.ru',  # Architecture news, not events
        ]
        if any(agg in url_lower for agg in news_aggregators):
            print(f"  ⚠️  Rejecting news aggregator URL: {event.url[:60]}")
            return False
        
        # STRICT: Reject fake/spam conference aggregator sites (these generate fake events)
        spam_aggregators = [
            'conferencealerts.co.in',
            'allconferencealert.net',
            'internationalconferencealerts.com',
            'conferencealert.com',
            'conferencealerts.com',
            'waset.org',  # Known spam conference site
            'conferenceineurope.org',  # Spam aggregator site
            'conferenceseries.com',
            '10times.com',
            'eventbrite.com/d/',  # Search pages, not specific events
            'competitioncorner.net',  # Event listing aggregator
            'wordreference.com',  # Dictionary site, not events
            'addtoany.com',  # Share button links
            'espconferences.org',  # Spam conference site
        ]
        if any(agg in url_lower for agg in spam_aggregators):
            print(f"  ⚠️  Rejecting spam conference aggregator: {event.url[:60]}")
            return False
        
        # STRICT: Reject generic listing URLs from aggregators (not specific event pages)
        if '/ukraine-conferences' in url_lower or '/ukraine/' in url_lower:
            # Check if it's a listing page (not eventdetails)
            if 'eventdetail' not in url_lower and 'eventdetails' not in url_lower:
                print(f"  ⚠️  Rejecting generic listing URL: {event.url[:60]}")
                return False
        
        # STRICT: Reject listing pages that end with /events (not specific event pages)
        if url_lower.rstrip('/').endswith('/events'):
            print(f"  ⚠️  Rejecting listing page URL: {event.url[:60]}")
            return False
        
        # STRICT: Reject more listing page patterns
        listing_patterns = [
            '/all-events',
            '/category/',
            '/news/',
            '/naukovi-konferenciyi/',  # Scientific conferences listing
            '/upcoming-events',
            '/event-list',
            '/events/',  # If it ends with events/
            '/newsroom/',  # News sections
            '/past-events',  # Past event listings
            '/archive/',  # Archive pages
        ]
        for pattern in listing_patterns:
            if pattern in url_lower:
                # Allow if URL has specific event ID or eventdetail
                if 'eventdetail' in url_lower or re.search(r'/\d{5,}', url_lower):
                    break  # Has event ID, allow it
                print(f"  ⚠️  Rejecting listing page URL ({pattern}): {event.url[:60]}")
                return False
        
        # STRICT: Reject generic homepages
        import re
        # Match URLs that are just domain or domain/
        if re.match(r'^https?://[^/]+/?$', event.url):
            print(f"  ⚠️  Rejecting homepage URL: {event.url[:60]}")
            return False
        
        # Check if URL is a generic landing page or program description
        generic_patterns = [
            r'^https?://[^/]+/home/?$',  # /home page
            r'^https?://[^/]+/program/[^/]+/?$',  # Program description (e.g., /program/ls/)
        ]
        for pattern in generic_patterns:
            if re.match(pattern, event.url, re.IGNORECASE):
                return False  # Reject generic pages
        
        if not event.url or not event.url.startswith(('http://', 'https://')):
            return False
        
        # STRICT: Reject month archive pages (e.g., /2025/11)
        if re.search(r'/\d{4}/\d{1,2}/?$', event.url):
            print(f"  ⚠️  Rejecting month archive URL: {event.url[:60]}")
            return False
        
        # STRICT: Reject generic calendar pages
        if '/calendar.aspx' in url_lower or '/calendar/' in url_lower:
            if 'eventid' not in url_lower and 'eid=' not in url_lower:
                print(f"  ⚠️  Rejecting generic calendar URL: {event.url[:60]}")
                return False
        
        # Check for very local/narrow events (exclude routine regional meetings)
        # Exclude: засідання ради (council meetings), very specific oblast events
        local_indicators = [
            "засідання архітектурно", "засідання містобудівної ради",
            "council meeting", "рада", "обласна рада"
        ]
        # But allow if it's a major forum/conference
        major_indicators = ["conference", "forum", "summit", "конференція", "форум"]
        has_local = any(indicator in title_lower for indicator in local_indicators)
        has_major = any(indicator in title_lower for indicator in major_indicators)
        
        # Exclude if it's a local meeting but not a major event
        if has_local and not has_major:
            return False
        
        # STRICT: Reject clearly irrelevant topics (not related to urban planning/recovery)
        irrelevant_topics = [
            "artificial intelligence", "software engineering", "machine learning",
            "human rights in africa", "cultural identity", "latin american",
            "spanish studies", "arabic studies", "islamic studies",
            "teacher education", "pedagogy", "biotechnology", "biology",
            "medical research", "healthcare", "nursing", "pharmacy",
            "blockchain", "cryptocurrency", "crypto", "bitcoin", "ethereum",
            "fintech", "defi", "nft", "web3"
        ]
        # Check title and summary for irrelevant topics
        combined_text = f"{title_lower} {(event.summary or '').lower()}"
        
        # Urban/recovery keywords that override irrelevance
        urban_keywords = [
            "urban", "city", "cities", "planning", "housing", "recovery",
            "reconstruction", "municipal", "infrastructure", "ukraine"
        ]
        has_urban = any(kw in combined_text for kw in urban_keywords)
        
        for topic in irrelevant_topics:
            if topic in combined_text and not has_urban:
                print(f"  ⚠️  Rejecting irrelevant topic '{topic}': {event.event_title[:50]}")
                return False
        
        # Check summary doesn't indicate it's news or program
        if event.summary:
            summary_lower = event.summary.lower()
            news_phrases = ["news article", "blog post", "reports that", "according to news"]
            program_phrases = ["can submit applications", "applications open", "program starts", "submitting applications", "access to", "compensation program", "housing program"]
            
            if any(phrase in summary_lower for phrase in news_phrases):
                return False
            
            # Reject if it's clearly a program announcement
            if any(phrase in summary_lower for phrase in program_phrases):
                # But allow if it's clearly an event (e.g., "Conference where you can register")
                if not any(indicator in summary_lower for indicator in ["conference", "workshop", "seminar", "webinar", "forum", "event", "meeting"]):
                    return False
        
        return True

