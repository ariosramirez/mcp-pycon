"""Pydantic models for the Task API."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
import uuid


class UserType(str, Enum):
    """Type of user in the system."""
    CLIENT = "client"
    PROSPECT = "prospect"
    PARTNER = "partner"


class CallStatus(str, Enum):
    """Status of a scheduled call."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class UserCreate(BaseModel):
    """Request model for creating a new user."""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    company: str = Field(..., min_length=1, max_length=100, description="Company name")
    user_type: UserType = Field(default=UserType.CLIENT, description="Type of user")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about the user")


class User(BaseModel):
    """User model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique user ID")
    name: str
    email: str
    company: str
    user_type: UserType
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScheduleCallCreate(BaseModel):
    """Request model for scheduling a call."""
    user_id: str = Field(..., description="ID of the user to schedule call with")
    title: str = Field(..., min_length=1, max_length=200, description="Call title/purpose")
    scheduled_for: datetime = Field(..., description="Date and time for the call")
    duration_minutes: int = Field(default=30, ge=15, le=240, description="Call duration in minutes")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes for the call")


class ScheduledCall(BaseModel):
    """Scheduled call model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique call ID")
    user_id: str
    title: str
    scheduled_for: datetime
    duration_minutes: int
    notes: Optional[str] = None
    status: CallStatus = Field(default=CallStatus.SCHEDULED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    user_id: Optional[str] = Field(None, description="User ID if task is related to a user")
    due_date: Optional[datetime] = Field(None, description="Task due date")


class Task(BaseModel):
    """Task model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique task ID")
    title: str
    description: Optional[str] = None
    user_id: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
