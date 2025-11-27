"""Supabase database client for event storage."""
import os
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class DatabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.table_name = "events"
    
    def upsert_event(self, event_data: dict) -> dict:
        """
        Insert or update an event based on URL (unique identifier).
        
        Args:
            event_data: Dictionary containing event fields
            
        Returns:
            The inserted/updated event record
        """
        # Check if event with this URL already exists
        existing = self.client.table(self.table_name)\
            .select("id, url")\
            .eq("url", event_data["url"])\
            .execute()
        
        if existing.data:
            # Update existing event
            event_id = existing.data[0]["id"]
            result = self.client.table(self.table_name)\
                .update(event_data)\
                .eq("id", event_id)\
                .execute()
            return result.data[0] if result.data else None
        else:
            # Insert new event
            result = self.client.table(self.table_name)\
                .insert(event_data)\
                .execute()
            return result.data[0] if result.data else None
    
    def get_events(self, limit: int = 100, category: Optional[str] = None) -> List[dict]:
        """
        Retrieve events from database.
        
        Args:
            limit: Maximum number of events to return
            category: Optional category filter
            
        Returns:
            List of event records
        """
        query = self.client.table(self.table_name)\
            .select("*")\
            .order("event_date", desc=False)\
            .limit(limit)
        
        if category:
            query = query.eq("category", category)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_upcoming_events(self, days: int = 28) -> List[dict]:
        """
        Get events in the next N days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of upcoming event records
        """
        from datetime import date, timedelta
        today = date.today()
        future_date = today + timedelta(days=days)
        
        result = self.client.table(self.table_name)\
            .select("*")\
            .gte("event_date", today.isoformat())\
            .lte("event_date", future_date.isoformat())\
            .order("event_date", desc=False)\
            .execute()
        
        return result.data if result.data else []

