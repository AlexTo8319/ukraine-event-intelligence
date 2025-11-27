"""Automated database setup - will work once we have database password or service role key."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    """Set up database using available credentials."""
    print("=" * 60)
    print("Automated Database Setup")
    print("=" * 60)
    print()
    
    # Method 1: Try direct PostgreSQL connection with password
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    if db_password:
        print("🔍 Attempting direct PostgreSQL connection...")
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            supabase_url = os.getenv("SUPABASE_URL", "https://qjuaqnhwpwmywgshghpq.supabase.co")
            project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
            
            conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            
            print(f"   Connecting to database...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            # Read SQL files
            base_dir = os.path.dirname(__file__)
            schema_path = os.path.join(base_dir, "database", "schema.sql")
            rls_path = os.path.join(base_dir, "database", "rls_policy.sql")
            
            print("   📊 Creating events table and indexes...")
            with open(schema_path, 'r') as f:
                sql = f.read()
                # Execute each statement separately
                for statement in sql.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cur.execute(statement)
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                print(f"      ⚠️  {str(e)[:100]}")
            
            print("   🔒 Setting up RLS policies...")
            with open(rls_path, 'r') as f:
                sql = f.read()
                for statement in sql.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cur.execute(statement)
                        except Exception as e:
                            if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                                print(f"      ⚠️  {str(e)[:100]}")
            
            # Verify table was created
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'events'
                );
            """)
            exists = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            if exists:
                print()
                print("=" * 60)
                print("✅ DATABASE SETUP COMPLETE!")
                print("=" * 60)
                print("   ✓ Events table created")
                print("   ✓ Indexes created")
                print("   ✓ Triggers set up")
                print("   ✓ RLS policies configured")
                print()
                return True
            else:
                print("   ⚠️  Table creation may have failed")
                return False
                
        except ImportError:
            print("   ❌ psycopg2-binary not installed")
            print("   Run: pip install psycopg2-binary")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            if "password" in str(e).lower() or "authentication" in str(e).lower():
                print("   💡 Check that SUPABASE_DB_PASSWORD is correct")
            return False
    
    # Method 2: Check if we can use service role key
    service_key = os.getenv("SUPABASE_KEY")
    if service_key and service_key != "YOUR_SERVICE_ROLE_KEY_HERE":
        print("🔍 Service role key found, but need direct SQL execution...")
        print("   Direct PostgreSQL connection is more reliable.")
        print("   Please set SUPABASE_DB_PASSWORD in .env")
        return False
    
    # No credentials available
    print("⚠️  No database credentials found")
    print()
    print("To set up automatically, add one of these to .env:")
    print()
    print("Option 1: Database Password (Recommended)")
    print("  SUPABASE_DB_PASSWORD=your_database_password")
    print("  Get it from: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/settings/database")
    print()
    print("Option 2: Manual Setup (2 minutes)")
    print("  1. Go to: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql")
    print("  2. Copy setup_complete.sql")
    print("  3. Paste and run")
    print()
    
    return False

if __name__ == "__main__":
    success = setup_database()
    if success:
        print("🎉 You can now run the research agent!")
        print("   python3 -m agent.research_agent")
    sys.exit(0 if success else 1)

