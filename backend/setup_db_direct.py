"""Set up database using direct PostgreSQL connection or Supabase service role."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def setup_with_service_role():
    """Try to set up using Supabase service role key."""
    from supabase import create_client, Client
    
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_KEY")
    
    if not service_key or service_key == "YOUR_SERVICE_ROLE_KEY_HERE":
        return False, "Service role key not set"
    
    try:
        client: Client = create_client(supabase_url, service_key)
        
        # Read SQL files
        base_dir = os.path.dirname(__file__)
        schema_path = os.path.join(base_dir, "database", "schema.sql")
        rls_path = os.path.join(base_dir, "database", "rls_policy.sql")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with open(rls_path, 'r') as f:
            rls_sql = f.read()
        
        # Supabase Python client doesn't support raw SQL execution
        # We need to use the REST API or direct PostgreSQL connection
        return False, "Need direct PostgreSQL connection or REST API method"
        
    except Exception as e:
        return False, str(e)

def setup_with_postgres():
    """Try to set up using direct PostgreSQL connection."""
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        return False, "psycopg2 not installed. Install with: pip install psycopg2-binary"
    
    # Get connection details
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not db_password:
        return False, "Database password not set. Set SUPABASE_DB_PASSWORD in .env"
    
    # Extract project ref from URL
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    # Supabase direct connection
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Read and execute schema SQL
        base_dir = os.path.dirname(__file__)
        schema_path = os.path.join(base_dir, "database", "schema.sql")
        rls_path = os.path.join(base_dir, "database", "rls_policy.sql")
        
        print("📊 Creating events table...")
        with open(schema_path, 'r') as f:
            cur.execute(f.read())
        
        print("🔒 Setting up RLS policies...")
        with open(rls_path, 'r') as f:
            cur.execute(f.read())
        
        cur.close()
        conn.close()
        
        return True, "Database set up successfully!"
        
    except Exception as e:
        return False, f"Database connection error: {str(e)}"

def setup_via_rest_api():
    """Try to set up using Supabase REST API."""
    import requests
    
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_KEY")
    
    if not service_key or service_key == "YOUR_SERVICE_ROLE_KEY_HERE":
        return False, "Service role key required"
    
    # Supabase doesn't expose SQL execution via REST API
    # We need direct PostgreSQL connection
    return False, "REST API doesn't support SQL execution"

def main():
    """Main setup function."""
    print("=" * 60)
    print("Database Setup")
    print("=" * 60)
    print()
    
    # Try method 1: Direct PostgreSQL connection
    if os.getenv("SUPABASE_DB_PASSWORD"):
        print("🔍 Trying direct PostgreSQL connection...")
        success, message = setup_with_postgres()
        if success:
            print(f"✅ {message}")
            return 0
        else:
            print(f"⚠️  {message}")
    
    # Try method 2: Service role key (if we can use it)
    service_key = os.getenv("SUPABASE_KEY")
    if service_key and service_key != "YOUR_SERVICE_ROLE_KEY_HERE":
        print("🔍 Service role key found, but need direct SQL execution...")
        print("   Installing psycopg2 for direct PostgreSQL connection...")
        print("   Run: pip install psycopg2-binary")
        print("   Then set SUPABASE_DB_PASSWORD in .env")
    
    print()
    print("=" * 60)
    print("⚠️  Automated setup requires one of these:")
    print("=" * 60)
    print()
    print("Option 1: Database Password (Easiest)")
    print("  1. Go to: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/settings/database")
    print("  2. Copy the database password")
    print("  3. Add to .env: SUPABASE_DB_PASSWORD=your_password")
    print("  4. Install: pip install psycopg2-binary")
    print("  5. Run this script again")
    print()
    print("Option 2: Manual Setup (2 minutes)")
    print("  1. Go to: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql")
    print("  2. Copy setup_complete.sql")
    print("  3. Paste and run")
    print()
    
    return 1

if __name__ == "__main__":
    sys.exit(main())

