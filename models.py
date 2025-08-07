from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Activity(BaseModel):
    time: str = Field(..., example="9:00 AM")
    description: str
    location: str

class Day(BaseModel):
    day: int
    theme: str
    activities: List[Activity]

class ItineraryInput(BaseModel):
    destination: str
    durationDays: int = Field(..., gt=0, le=30, description="Trip duration in days (1-30)")

class ItineraryDocument(BaseModel):
    jobId: str
    status: str  # processing, completed, failed
    destination: str
    durationDays: int
    createdAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    itinerary: Optional[List[Day]] = None
    error: Optional[str] = None