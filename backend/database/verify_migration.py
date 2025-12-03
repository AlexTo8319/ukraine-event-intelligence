#!/usr/bin/env python3
"""Verify that database migration was successful."""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_migration():
    """Check if migration columns exist."""
    supabase_url = os.getenv("SUPABASE_URL") or "https://qjuaqnhwpwmywgshghpq.supabase.co"
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("❌ ERROR: SUPABASE_KEY not found")
        return False
    
    print("🔍 Verifying database migration...")
    print()
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    # Try to query the new columns
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/events?select=id,event_time,target_audience,registration_url&limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                sample = data[0]
                has_time = 'event_time' in sample
                has_audience = 'target_audience' in sample
                has_reg_url = 'registration_url' in sample
                
                print("📊 Migration Status:")
                print("-" * 40)
                print(f"   event_time:         {'✅ EXISTS' if has_time else '❌ MISSING'}")
                print(f"   target_audience:    {'✅ EXISTS' if has_audience else '❌ MISSING'}")
                print(f"   registration_url:   {'✅ EXISTS' if has_reg_url else '❌ MISSING'}")
                print("-" * 40)
                
                if has_time and has_audience and has_reg_url:
                    print("\n✅ SUCCESS! All migration columns exist.")
                    print("   The database is ready for the new features!")
                    return True
                else:
                    print("\n⚠️  Migration incomplete. Some columns are missing.")
                    print("\n📋 To complete the migration:")
                    print("   1. Go to: https://supabase.com/dashboard")
                    print("   2. SQL Editor → New Query")
                    print("   3. Run the SQL from: backend/database/schema_update.sql")
                    return False
            else:
                print("⚠️  No events found in database (this is OK)")
                print("   Cannot verify columns without data")
                return False
        elif response.status_code == 400:
            error_text = response.text.lower()
            if 'column' in error_text and 'does not exist' in error_text:
                print("❌ Migration not completed - columns don't exist")
                print("\n📋 Run the migration SQL in Supabase SQL Editor:")
                print("   backend/database/schema_update.sql")
                return False
            else:
                print(f"⚠️  API error: {response.status_code}")
                print(f"   {response.text[:200]}")
                return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying migration: {str(e)}")
        return False


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)




