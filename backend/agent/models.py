"""Data models for events."""
from pydantic import BaseModel, Field, field_validator
from datetime import date, time
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
    event_time: Optional[time] = Field(None, description="Time of the event in HH:MM format")
    organizer: Optional[str] = Field(None, description="Name of the organizing entity")
    url: str = Field(..., description="Source URL where event information was found")
    registration_url: Optional[str] = Field(None, description="Direct link to event registration page")
    category: EventCategory = Field(..., description="Category of the event")
    is_online: bool = Field(False, description="Whether the event is online")
    target_audience: Optional[str] = Field(None, description="Target audience (e.g., Donors, Government Officials, Architects)")
    summary: Optional[str] = Field(None, description="1-2 sentence description of the event")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is valid."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @field_validator('registration_url')
    @classmethod
    def validate_registration_url(cls, v: Optional[str]) -> Optional[str]:
        """Ensure registration URL is valid if provided."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Registration URL must start with http:// or https://')
        return v
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "event_title": self.event_title,
            "event_date": self.event_date.isoformat(),
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "organizer": self.organizer,
            "url": self.url,
            "registration_url": self.registration_url,
            "category": self.category.value,
            "is_online": self.is_online,
            "target_audience": self.target_audience,
            "summary": self.summary
        }

