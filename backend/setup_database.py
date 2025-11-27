"""Script to set up the Supabase database schema."""
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Set up the database schema and RLS policies."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        print("\nTo get your service role key:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Settings → API")
        print("4. Copy the 'service_role' key (secret)")
        print("5. Add it to .env as SUPABASE_KEY")
        return False
    
    try:
        client: Client = create_client(supabase_url, supabase_key)
        
        # Read schema SQL
        schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
        rls_path = os.path.join(os.path.dirname(__file__), "database", "rls_policy.sql")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with open(rls_path, 'r') as f:
            rls_sql = f.read()
        
        print("📊 Setting up database schema...")
        
        # Execute schema SQL
        # Note: Supabase Python client doesn't directly execute raw SQL
        # We need to use the REST API or PostgREST
        # For now, we'll verify the connection and provide instructions
        
        # Test connection by trying to query
        try:
            # Try a simple query to verify connection
            result = client.table("events").select("id").limit(1).execute()
            print("✅ Database connection successful!")
            print("✅ Events table already exists")
        except Exception as e:
            if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                print("⚠️  Events table does not exist yet")
                print("\n📝 Please run the SQL manually in Supabase SQL Editor:")
                print(f"   1. Go to: {supabase_url.replace('.supabase.co', '.supabase.co/project/qjuaqnhwpwmywgshghpq/sql')}")
                print("   2. Click 'New Query'")
                print("   3. Copy and paste the contents of backend/database/schema.sql")
                print("   4. Click 'Run'")
                print("   5. Then run backend/database/rls_policy.sql")
                return False
            else:
                raise
        
        # Try to set up RLS (this also needs to be done via SQL Editor)
        print("\n📝 To set up Row Level Security:")
        print("   1. Go to Supabase SQL Editor")
        print("   2. Run the contents of backend/database/rls_policy.sql")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        print("\n💡 Alternative: Run SQL manually in Supabase Dashboard")
        print("   1. Go to https://supabase.com/dashboard")
        print("   2. Select your project")
        print("   3. Go to SQL Editor")
        print("   4. Run backend/database/schema.sql")
        print("   5. Run backend/database/rls_policy.sql")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)

