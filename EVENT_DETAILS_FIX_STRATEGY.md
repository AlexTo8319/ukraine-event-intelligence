# Strategy for Fixing Incorrect Event Details

## Problem Statement
Events are sometimes extracted incorrectly from landing pages, resulting in:
- Generic URLs (e.g., `/home`, `/contact`) instead of direct event pages
- Wrong dates (especially for week-long events)
- Missing or incorrect event details
- Links that don't work or point to wrong pages

## Multi-Layered Approach

### Layer 1: Pre-Extraction Validation (LLM Prompt)
**Status**: ✅ Implemented
- Explicit instructions to extract direct event URLs
- Priority rules for `eventdetail` URLs
- Date range handling (use start date)
- Rejection of news articles and program announcements

**Improvements Needed**:
- Add more examples of correct vs incorrect URL extraction
- Emphasize following links from aggregator pages

### Layer 2: Post-Extraction URL Improvement
**Status**: ✅ Partially Implemented
- `_improve_event_url()` method with 3 strategies
- URL extraction from search results
- Following aggregator pages
- Content analysis

**Improvements Needed**:
1. **More Aggressive URL Following**:
   - If URL contains `/home`, `/contact`, `/about`, `/events` → ALWAYS follow
   - Don't just check if it's an aggregator, actively search for event links
   - Follow up to 2 levels deep (aggregator → event list → event detail)

2. **Better Generic Page Detection**:
   - Check if URL path is too short (e.g., `/home`, `/contact`)
   - Check if URL doesn't contain event-related keywords
   - Check if page content is mostly navigation/header/footer

3. **Enhanced Content Analysis**:
   - Extract ALL links from page, not just event-related ones
   - Score links based on:
     - Presence of event title keywords
     - URL structure (eventdetail > /event/ > /events/)
     - Context around link (nearby text matching event title)
   - Validate that extracted URL actually contains event details

### Layer 3: URL Validation & Accessibility Check
**Status**: ✅ Implemented
- URL format validation
- Accessibility check (HEAD/GET requests)
- Content analysis for date validation

**Improvements Needed**:
1. **Retry Logic**:
   - If URL returns 404/403, try alternative URLs from search results
   - If URL redirects, follow redirect and validate final URL

2. **Content Verification**:
   - After extracting URL, verify it contains:
     - Event title (fuzzy match)
     - Event date (within 1 day of extracted date)
     - Event-related keywords (conference, workshop, etc.)
   - If verification fails, try next best URL

### Layer 4: Periodic Cleanup & Validation
**Status**: ✅ Implemented
- `cleanup_existing_events.py` script
- `analyze_all_events.py` script
- `fix_remaining_issues.py` for manual fixes

**Improvements Needed**:
1. **Automated Re-validation**:
   - Run URL validation on all events weekly
   - Check for broken links
   - Re-extract URLs for events with generic URLs

2. **Alert System**:
   - Flag events with generic URLs for manual review
   - Track events that fail URL validation
   - Monitor date inconsistencies

### Layer 5: Manual Review Interface (Future)
**Status**: ❌ Not Implemented
- Admin interface to review flagged events
- Ability to manually correct URLs and dates
- Bulk operations for fixing similar issues

## Implementation Priority

### High Priority (Immediate)
1. ✅ Fix frontend date filtering (use current date, not hardcoded)
2. ✅ Add API credits tracking
3. 🔄 Enhance URL extraction to be more aggressive about following links
4. 🔄 Add content verification after URL extraction

### Medium Priority (Next Sprint)
1. Add retry logic for broken URLs
2. Implement automated weekly re-validation
3. Improve generic page detection
4. Add more examples to LLM prompt

### Low Priority (Future)
1. Build manual review interface
2. Add alert system for problematic events
3. Implement machine learning for URL quality scoring

## Specific Code Changes Needed

### 1. Enhance `_improve_event_url()` in `llm_processor.py`
```python
# Add more aggressive generic page detection
generic_indicators = ['/home', '/contact', '/about', '/events?', '/event-list']
if any(ind in event_url for ind in generic_indicators):
    # ALWAYS try to find better URL, don't just check if aggregator
    # Follow links more aggressively
    # Check up to 2 levels deep
```

### 2. Improve `URLFollower.find_direct_event_url()`
```python
# Add depth parameter (max_depth=2)
# Extract ALL links, not just event-related
# Score all links and pick best
# Verify final URL contains event details
```

### 3. Add URL Verification Step
```python
def verify_event_url(url: str, event_title: str, event_date: date) -> bool:
    """Verify URL actually contains event details"""
    content = fetch_url_content(url)
    # Check for title match (fuzzy)
    # Check for date match (within 1 day)
    # Check for event keywords
    return all_checks_pass
```

### 4. Track Credits Usage
```python
# In research_agent.py, track Tavily API usage
# Store in database or file
# Update credits API endpoint to show real usage
```

## Testing Strategy

1. **Unit Tests**:
   - Test URL extraction from various page types
   - Test date range handling
   - Test generic page detection

2. **Integration Tests**:
   - Test full event extraction pipeline
   - Test URL improvement strategies
   - Test duplicate detection

3. **Manual Testing**:
   - Run research agent on known problematic sites
   - Verify extracted URLs are correct
   - Check dates are accurate

## Success Metrics

- **URL Accuracy**: >95% of events have direct event URLs (not generic pages)
- **Date Accuracy**: >98% of dates match URL content (within 1 day)
- **Link Accessibility**: >99% of URLs are accessible (not 404/403)
- **Manual Fixes**: <5% of events require manual URL correction

## Next Steps

1. ✅ Fix frontend date filtering
2. ✅ Add credits tracking
3. 🔄 Enhance URL extraction (in progress)
4. ⏳ Add content verification
5. ⏳ Implement automated re-validation


