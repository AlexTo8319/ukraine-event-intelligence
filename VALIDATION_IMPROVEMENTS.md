# Validation and Data Quality Improvements

## Issues Addressed

### 1. Title-Content Mismatch Detection
**Problem**: Events with titles that don't match URL content (e.g., "Urban studies" leading to "Spanish/Latin American Studies")

**Solution**:
- ✅ Extract page title and h1 heading from URL
- ✅ Check for topic mismatches (urban vs language studies, education, etc.)
- ✅ Verify title keywords appear in page title/h1
- ✅ Reject events where title topic doesn't match URL content topic

### 2. Relevance Filtering
**Problem**: Events not relevant to urban planning (e.g., "Europe in a Time of War" - war/policy focus, not urban planning)

**Solution**:
- ✅ Check for urban planning keywords (urban, city, planning, recovery, housing, etc.)
- ✅ Filter out irrelevant topics (teacher education, language studies, war/policy, biotechnology)
- ✅ Allow events with urban keywords even if they mention war/conflict in context of recovery
- ✅ Check URL content for relevance

### 3. URL Improvement
**Problem**: Generic listing URLs instead of specific eventdetail URLs

**Solution**:
- ✅ Automatically find eventdetail URLs from listing pages
- ✅ Follow links up to 2 levels deep
- ✅ Verify found URLs match event title
- ✅ Update URLs in database automatically

## Enhanced Validation System

### New Script: `enhanced_relevance_validation.py`

**Features**:
1. **Title-Content Matching**
   - Extracts page title and h1 from URL
   - Checks for topic mismatches
   - Verifies title keywords in page content
   - Rejects events with mismatched topics

2. **Relevance Checking**
   - Checks for urban planning keywords
   - Filters irrelevant topics
   - Validates URL content relevance

3. **Automatic URL Fixing**
   - Finds eventdetail URLs from listing pages
   - Verifies URLs match event titles
   - Updates database automatically

### Validation Checks

1. ✅ **Title-Content Match**: Page title/h1 must match event title topic
2. ✅ **Relevance**: Event must be relevant to urban planning
3. ✅ **URL Quality**: Prefer eventdetail URLs over listing pages
4. ✅ **Topic Mismatch**: Reject if title topic ≠ URL content topic

## Usage

```bash
cd backend
python3 enhanced_relevance_validation.py
```

## Integration

This validation can be:
1. **Added to weekly cleanup** (`.github/workflows/weekly-cleanup.yml`)
2. **Run after research** (in `research_agent.py`)
3. **Run manually** (whenever you want to validate/fix events)

## Results

- **Events validated**: All events in database
- **Events fixed**: URLs improved to eventdetail
- **Events removed**: Title mismatches, irrelevant topics
- **Valid events remaining**: Only relevant, correctly matched events

The system now automatically detects and fixes these issues!


