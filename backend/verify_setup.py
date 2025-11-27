"""Quick verification script to check if all dependencies and environment variables are set up correctly."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_env_var(name: str, required: bool = True) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(name)
    if required and not value:
        print(f"❌ {name} is not set")
        return False
    elif value:
        # Mask the value for security
        masked = value[:8] + "..." if len(value) > 8 else "***"
        print(f"✅ {name} is set ({masked})")
        return True
    else:
        print(f"⚠️  {name} is not set (optional)")
        return True

def check_import(module_name: str) -> bool:
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} is installed")
        return True
    except ImportError:
        print(f"❌ {module_name} is not installed")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Event Intelligence Platform - Setup Verification")
    print("=" * 60)
    print()
    
    print("Checking Environment Variables:")
    print("-" * 60)
    env_vars_ok = True
    env_vars_ok &= check_env_var("TAVILY_API_KEY", required=True)
    env_vars_ok &= check_env_var("OPENAI_API_KEY", required=True)
    env_vars_ok &= check_env_var("SUPABASE_URL", required=True)
    env_vars_ok &= check_env_var("SUPABASE_KEY", required=True)
    print()
    
    print("Checking Python Dependencies:")
    print("-" * 60)
    deps_ok = True
    deps_ok &= check_import("openai")
    deps_ok &= check_import("tavily")
    deps_ok &= check_import("supabase")
    deps_ok &= check_import("dotenv")
    deps_ok &= check_import("pydantic")
    print()
    
    print("=" * 60)
    if env_vars_ok and deps_ok:
        print("✅ All checks passed! You're ready to run the research agent.")
        print()
        print("Next steps:")
        print("  1. Make sure Supabase database is set up (run schema.sql)")
        print("  2. Run: python -m agent.research_agent")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        if not env_vars_ok:
            print("  - Set missing environment variables in .env file")
        if not deps_ok:
            print("  - Install missing dependencies: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())

