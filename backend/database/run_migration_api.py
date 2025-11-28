#!/usr/bin/env python3
"""Run database migration using Supabase Management API."""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def run_migration_via_api():
    """Execute migration using Supabase Management API."""
    supabase_url = os.getenv("SUPABASE_URL") or "https://qjuaqnhwpwmywgshghpq.supabase.co"
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("❌ ERROR: SUPABASE_KEY not found in .env")
        sys.exit(1)
    
    print("🔍 Checking current database schema...")
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    # Check if columns already exist
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
                
                if has_time and has_audience and has_reg_url:
                    print("✅ Migration already complete! All new columns exist.")
                    print("   - event_time ✓")
                    print("   - target_audience ✓")
                    print("   - registration_url ✓")
                    return True
                else:
                    print("⚠️  Some columns are missing:")
                    print(f"   - event_time: {'✓' if has_time else '✗'}")
                    print(f"   - target_audience: {'✓' if has_audience else '✗'}")
                    print(f"   - registration_url: {'✓' if has_reg_url else '✗'}")
        elif response.status_code == 400:
            error_text = response.text.lower()
            if 'column' in error_text and 'does not exist' in error_text:
                print("⚠️  New columns don't exist - migration needed")
            else:
                print(f"⚠️  API error: {response.status_code}")
                print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"⚠️  Error checking schema: {str(e)}")
    
    print("\n" + "="*60)
    print("⚠️  AUTOMATED MIGRATION NOT POSSIBLE")
    print("="*60)
    print("\nSupabase doesn't allow direct SQL execution via REST API")
    print("for security reasons. You need to run the migration manually.")
    print("\n📋 QUICK MIGRATION STEPS (2 minutes):")
    print("-" * 60)
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Click 'SQL Editor' in the left sidebar")
    print("4. Click 'New Query'")
    print("5. Copy and paste this SQL:")
    print("\n" + "-" * 60)
    
    # Read and display the migration SQL
    migration_file = os.path.join(os.path.dirname(__file__), "schema_update.sql")
    if os.path.exists(migration_file):
        with open(migration_file, 'r') as f:
            sql_content = f.read()
            # Remove comments for cleaner output
            lines = sql_content.split('\n')
            sql_lines = [line for line in lines if line.strip() and not line.strip().startswith('--')]
            print("\n".join(sql_lines))
    
    print("-" * 60)
    print("6. Click 'Run' button (or press Ctrl+Enter)")
    print("7. Wait for 'Success' message")
    print("\n✅ That's it! The migration will be complete.")
    print("\n" + "="*60)
    
    return False


if __name__ == "__main__":
    success = run_migration_via_api()
    sys.exit(0 if success else 1)

