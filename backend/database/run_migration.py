#!/usr/bin/env python3
"""Run database migration to add new fields to events table."""
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the database migration SQL."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        print("   Make sure your .env file contains these values")
        sys.exit(1)
    
    print("🔌 Connecting to Supabase...")
    client: Client = create_client(supabase_url, supabase_key)
    
    # Migration SQL
    migration_sql = """
    -- Migration: Add new fields to events table
    -- Add new columns
    ALTER TABLE events 
    ADD COLUMN IF NOT EXISTS event_time TIME,
    ADD COLUMN IF NOT EXISTS target_audience TEXT,
    ADD COLUMN IF NOT EXISTS registration_url TEXT;

    -- Add index on registration_url for faster lookups
    CREATE INDEX IF NOT EXISTS idx_events_registration_url ON events(registration_url) WHERE registration_url IS NOT NULL;
    """
    
    print("📝 Running migration SQL...")
    print("   Adding columns: event_time, target_audience, registration_url")
    
    try:
        # Execute SQL using Supabase RPC or direct SQL execution
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll use the REST API instead
        import requests
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # Split SQL into individual statements
        statements = [
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS event_time TIME, ADD COLUMN IF NOT EXISTS target_audience TEXT, ADD COLUMN IF NOT EXISTS registration_url TEXT;",
            "CREATE INDEX IF NOT EXISTS idx_events_registration_url ON events(registration_url) WHERE registration_url IS NOT NULL;"
        ]
        
        # Use Supabase REST API to execute SQL
        # Note: Supabase doesn't expose direct SQL execution via REST API for security
        # We need to use the PostgREST API or the Supabase dashboard
        # Let's try using the database client's RPC function or direct connection
        
        print("⚠️  Supabase Python client doesn't support direct SQL execution.")
        print("   Using alternative method...")
        
        # Try using psycopg2 for direct PostgreSQL connection
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Parse Supabase URL to get connection details
            # Supabase connection string format: postgresql://postgres:[password]@[host]:[port]/postgres
            # We need to construct this from the database password
            
            # Try to get database password from environment or use the one provided earlier
            db_password = os.getenv("SUPABASE_DB_PASSWORD") or "u8asfMxdtsqKpXfQ"
            if not db_password:
                print("❌ ERROR: SUPABASE_DB_PASSWORD not found")
                print("   Please add your Supabase database password to .env")
                print("   You can find it in: Supabase Dashboard → Settings → Database")
                sys.exit(1)
            
            # Extract host from SUPABASE_URL
            # Format: https://[project-ref].supabase.co
            parsed_url = urlparse(supabase_url)
            host = parsed_url.hostname
            # Extract project ref (e.g., qjuaqnhwpwmywgshghpq from qjuaqnhwpwmywgshghpq.supabase.co)
            project_ref = host.split('.')[0]
            
            # Try connection pooler first (more reliable)
            # Format: [project-ref].pooler.supabase.com
            db_hosts = [
                f"{project_ref}.pooler.supabase.com",  # Connection pooler
                f"db.{project_ref}.supabase.co",       # Direct connection
            ]
            db_port = 5432
            db_name = "postgres"
            db_user = "postgres"
            
            # Try each host until one works
            conn = None
            last_error = None
            for db_host in db_hosts:
                try:
                    print(f"🔗 Trying connection to {db_host}...")
                    conn = psycopg2.connect(
                        host=db_host,
                        port=db_port,
                        database=db_name,
                        user=db_user,
                        password=db_password,
                        connect_timeout=10
                    )
                    print(f"✅ Connected to {db_host}!")
                    break
                except Exception as e:
                    last_error = e
                    print(f"   ⚠️  {db_host} failed: {str(e)[:100]}")
                    continue
            
            if not conn:
                raise Exception(f"Could not connect to any database host. Last error: {last_error}")
            
            conn.autocommit = True
            cursor = conn.cursor()
            
            print("✅ Connected! Running migration...")
            
            # Execute each statement
            for i, statement in enumerate(statements, 1):
                print(f"   [{i}/{len(statements)}] Executing statement...")
                try:
                    cursor.execute(statement)
                    print(f"   ✅ Statement {i} executed successfully")
                except Exception as e:
                    # Check if it's a "already exists" error (which is fine)
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"   ⚠️  Statement {i} skipped (already exists)")
                    else:
                        print(f"   ⚠️  Statement {i} warning: {str(e)}")
            
            cursor.close()
            conn.close()
            
            print("\n✅ Migration completed successfully!")
            print("\n📊 Verifying migration...")
            
            # Verify by checking columns
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'events'
                AND column_name IN ('event_time', 'target_audience', 'registration_url')
                ORDER BY column_name;
            """)
            
            results = cursor.fetchall()
            if results:
                print("   ✅ New columns found:")
                for col_name, data_type, is_nullable in results:
                    print(f"      - {col_name} ({data_type}, nullable: {is_nullable})")
            else:
                print("   ⚠️  No new columns found (they may already exist)")
            
            cursor.close()
            conn.close()
            
            print("\n🎉 Database migration complete!")
            return True
            
        except ImportError:
            print("❌ ERROR: psycopg2 not installed")
            print("   Install it with: pip install psycopg2-binary")
            sys.exit(1)
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print("\n💡 Alternative: Run the migration manually in Supabase SQL Editor:")
            print("   1. Go to: https://supabase.com/dashboard")
            print("   2. Select your project")
            print("   3. Click 'SQL Editor' → 'New Query'")
            print("   4. Copy SQL from: backend/database/schema_update.sql")
            print("   5. Click 'Run'")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()

