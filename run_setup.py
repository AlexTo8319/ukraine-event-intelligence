#!/usr/bin/env python3
"""Quick setup verification and SQL display."""
import os
import sys

def main():
    print("=" * 60)
    print("Database Setup Helper")
    print("=" * 60)
    print()
    
    # Check if table exists
    try:
        import requests
        supabase_url = "https://qjuaqnhwpwmywgshghpq.supabase.co"
        anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik"
        
        response = requests.get(
            f"{supabase_url}/rest/v1/events",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
            params={"select": "id", "limit": "1"},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Events table already exists!")
            print("✅ Database is set up!")
            return 0
    except:
        pass
    
    print("⚠️  Database needs to be set up")
    print()
    print("📋 Quick Setup (2 minutes):")
    print()
    print("1. Open this URL in your browser:")
    print("   https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql")
    print()
    print("2. Copy the SQL below and paste it:")
    print()
    print("-" * 60)
    
    # Read and display SQL
    sql_path = os.path.join(os.path.dirname(__file__), "setup_complete.sql")
    if os.path.exists(sql_path):
        with open(sql_path, 'r') as f:
            print(f.read())
    else:
        print("ERROR: setup_complete.sql not found")
        return 1
    
    print("-" * 60)
    print()
    print("3. Click 'Run' in the SQL Editor")
    print()
    print("4. Verify with: python3 backend/verify_setup.py")
    print()
    
    return 1

if __name__ == "__main__":
    sys.exit(main())

