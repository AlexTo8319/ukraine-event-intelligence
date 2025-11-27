"""Data models for events."""
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from enum import Enum


class EventCategory(str, Enum):
    """Event category enumeration."""
    LEGISLATION = "Legislation"
    HOUSING = "Housing"
    RECOVERY = "Recovery"
    GENERAL = "General"


class Event(BaseModel):
    """Event data model."""
    event_title: str = Field(..., description="Title of the event")
    event_date: date = Field(..., description="Date of the event in ISO format (YYYY-MM-DD)")
    organizer: Optional[str] = Field(None, description="Name of the organizing entity")
    url: str = Field(..., description="URL of the event (unique identifier)")
    category: EventCategory = Field(..., description="Category of the event")
    is_online: bool = Field(False, description="Whether the event is online")
    summary: Optional[str] = Field(None, description="Short English summary of why it matters")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is valid."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "event_title": self.event_title,
            "event_date": self.event_date.isoformat(),
            "organizer": self.organizer,
            "url": self.url,
            "category": self.category.value,
            "is_online": self.is_online,
            "summary": self.summary
        }

