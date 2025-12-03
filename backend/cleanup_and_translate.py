#!/usr/bin/env python3
"""Clean up database and translate Ukrainian titles."""
import os
import sys
import requests
from datetime import date

# Get credentials from environment or use defaults
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qjuaqnhwpwmywgshghpq.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


def is_ukrainian(text):
    """Check if text contains Ukrainian characters."""
    if not text:
        return False
    ukrainian_chars = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    return any(char.lower() in ukrainian_chars for char in text)


def translate(text, context="event title"):
    """Translate Ukrainian to English using OpenAI."""
    if not OPENAI_API_KEY:
        print("  ⚠️ OPENAI_API_KEY not set, skipping translation")
        return text
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate Ukrainian text to English. Keep it concise and professional for {context}. Return ONLY the translation, no explanations."
                },
                {
                    "role": "user",
                    "content": f"Translate to English: {text}"
                }
            ],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  Translation error: {e}")
        return text


def delete_bad_events():
    """Delete events from spam aggregator sites."""
    # URLs to delete (spam aggregators and irrelevant events)
    bad_url_patterns = [
        'conferencealerts.co.in',
        'allconferencealert.net',
        'internationalconferencealerts.com',
        'conferencealert.com',
        'waset.org',
    ]
    
    print("🗑️ DELETING BAD EVENTS...")
    print("-" * 60)
    
    # Get all events
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=*",
        headers=headers
    )
    events = response.json()
    
    deleted = 0
    for event in events:
        url = event.get('url', '').lower()
        
        # Check if URL matches any bad pattern
        if any(pattern in url for pattern in bad_url_patterns):
            print(f"Deleting: {event['event_title'][:50]}...")
            print(f"  URL: {url[:60]}")
            
            # Delete
            del_response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{event['id']}",
                headers=headers
            )
            
            if del_response.status_code == 200:
                deleted += 1
                print(f"  ✅ Deleted")
            else:
                print(f"  ❌ Failed: {del_response.status_code}")
    
    print(f"\n✅ Deleted {deleted} bad events")
    return deleted


def delete_past_events():
    """Delete events with dates in the past."""
    today = date.today()
    
    print("\n🗑️ DELETING PAST EVENTS...")
    print("-" * 60)
    
    # Delete events before today
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/events?event_date=lt.{today.isoformat()}",
        headers=headers
    )
    
    if response.status_code == 200:
        deleted = response.json()
        print(f"✅ Deleted {len(deleted)} past events")
        return len(deleted)
    else:
        print(f"❌ Failed to delete past events: {response.status_code}")
        return 0


def delete_irrelevant_events():
    """Delete clearly irrelevant events."""
    irrelevant_keywords = [
        'artificial intelligence',
        'software engineering',
        'machine learning',
        'human rights in africa',
        'cultural identity',
        'latin american',
        'spanish studies',
        'teacher education',
        'pedagogy',
        'biotechnology',
    ]
    
    urban_keywords = [
        'urban', 'city', 'cities', 'planning', 'housing', 'recovery',
        'reconstruction', 'municipal', 'infrastructure', 'ukraine'
    ]
    
    print("\n🗑️ DELETING IRRELEVANT EVENTS...")
    print("-" * 60)
    
    # Get all events
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=*",
        headers=headers
    )
    events = response.json()
    
    deleted = 0
    for event in events:
        title = event.get('event_title', '').lower()
        summary = event.get('summary', '').lower()
        combined = f"{title} {summary}"
        
        # Check if irrelevant
        is_irrelevant = any(kw in combined for kw in irrelevant_keywords)
        has_urban = any(kw in combined for kw in urban_keywords)
        
        if is_irrelevant and not has_urban:
            print(f"Deleting irrelevant: {event['event_title'][:50]}...")
            
            # Delete
            del_response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{event['id']}",
                headers=headers
            )
            
            if del_response.status_code == 200:
                deleted += 1
                print(f"  ✅ Deleted")
            else:
                print(f"  ❌ Failed: {del_response.status_code}")
    
    print(f"\n✅ Deleted {deleted} irrelevant events")
    return deleted


def translate_ukrainian_titles():
    """Translate Ukrainian titles to English."""
    if not OPENAI_API_KEY:
        print("\n⚠️ OPENAI_API_KEY not set, skipping translation")
        return 0
    
    print("\n📝 TRANSLATING UKRAINIAN TITLES...")
    print("-" * 60)
    
    # Get all events
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=*&order=event_date",
        headers=headers
    )
    events = response.json()
    
    translated_count = 0
    for event in events:
        title = event['event_title']
        summary = event.get('summary', '')
        event_id = event['id']
        
        updates = {}
        
        # Translate title if Ukrainian
        if is_ukrainian(title):
            new_title = translate(title, "event title")
            if new_title and new_title != title:
                updates['event_title'] = new_title
                print(f"📝 {title[:40]}...")
                print(f"   → {new_title[:40]}...")
        
        # Translate summary if Ukrainian
        if summary and is_ukrainian(summary):
            new_summary = translate(summary, "event description")
            if new_summary and new_summary != summary:
                updates['summary'] = new_summary
        
        # Update if we have changes
        if updates:
            update_response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/events?id=eq.{event_id}",
                headers=headers,
                json=updates
            )
            if update_response.status_code == 200:
                translated_count += 1
                print(f"   ✅ Updated")
            else:
                print(f"   ❌ Failed: {update_response.status_code}")
    
    print(f"\n✅ Translated {translated_count} events")
    return translated_count


def show_final_status():
    """Show final database status."""
    print("\n" + "=" * 80)
    print("📊 FINAL DATABASE STATUS")
    print("=" * 80)
    
    # Get all events
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/events?select=event_date,event_title,url&order=event_date",
        headers=headers
    )
    events = response.json()
    
    print(f"\nTotal events: {len(events)}")
    print("-" * 80)
    
    for e in events:
        print(f"{e['event_date']} | {e['event_title'][:55]}")
    
    print("=" * 80)


def main():
    print("=" * 80)
    print("🧹 DATABASE CLEANUP AND TRANSLATION")
    print("=" * 80)
    
    # Step 1: Delete past events
    delete_past_events()
    
    # Step 2: Delete bad events (spam aggregators)
    delete_bad_events()
    
    # Step 3: Delete irrelevant events
    delete_irrelevant_events()
    
    # Step 4: Translate Ukrainian titles
    translate_ukrainian_titles()
    
    # Step 5: Show final status
    show_final_status()


if __name__ == "__main__":
    main()


