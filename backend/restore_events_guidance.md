# Restoring Events - Guidance

## What Happened

The enhanced validation was too aggressive and removed valid events. We need to:

1. **Make validation less aggressive** (only remove clearly wrong events)
2. **Run research again** to repopulate events
3. **Use conservative validation** going forward

## Solution

### Option 1: Run Research Again (Recommended)
The research agent will find events again, and with the improved (less aggressive) validation, it will keep valid events:

```bash
cd backend
python3 -m agent.research_agent
```

### Option 2: Manual Event Addition
If you have a list of events that were removed, we can add them back manually.

## Updated Validation Logic

The validation is now **more conservative**:

1. **Title-Content Matching**: Only removes if it's a CLEAR mismatch (e.g., "urban studies" → "spanish studies")
2. **Relevance**: Only removes clearly irrelevant topics (teacher education, language studies, biotechnology)
3. **War/Conflict**: Keeps events that mention war/conflict if they're about recovery
4. **Urban Keywords**: If event has urban keywords, it's kept even if it mentions other topics

## Next Steps

1. ✅ Validation made less aggressive
2. ⏳ Run research agent to repopulate events
3. ⏳ Monitor validation results

The system will now be more conservative and only remove events that are clearly wrong!


