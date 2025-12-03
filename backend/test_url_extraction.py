"""Test URL extraction from specific URLs."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.url_content_analyzer import URLContentAnalyzer

# Test cases
test_cases = [
    {
        "url": "https://conferenceineurope.net/contact",
        "title": "International Conference on e-Government, Smart Cities, and Digital Societies"
    },
    {
        "url": "https://hmarochos.kiev.ua/2025/11/26/na-pochatku-grudnya-v-u",
        "title": "Forum of Energy Managers"
    }
]

analyzer = URLContentAnalyzer()

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}: {test['title'][:50]}...")
    print(f"URL: {test['url']}")
    print('='*60)
    
    result = analyzer.analyze_url(test['url'], test['title'], None)
    
    print(f"Final URL: {result.get('actual_url', 'N/A')}")
    print(f"Found better URL: {result.get('found_better_url', False)}")
    print(f"Extracted date: {result.get('extracted_date', 'N/A')}")
    if result.get('error'):
        print(f"Error: {result['error']}")



