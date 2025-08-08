# for pydantic models

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data."""
    username:  Optional[str] = None

class UserOut(BaseModel):
    """Schema for user output."""
    id: int
    username: str
    email: str

    class Config:
        """Configuration that allows conversion from SQLAlchemy models."""
        from_attributes = True

class UserCreate(BaseModel):
    """Schema for registration requests."""
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    """Schema for login requests."""
    email: str
    password: str

class UserResponse(BaseModel):
    """Schema for API responses."""
    id: int
    username: str
    email: str

    class Config:
        """Configuration that allows conversion from SQLAlchemy models."""
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = None
    email: str
    password: Optional[str] = None

#Event Schemas
class EventCreate(BaseModel):
    """Schema for creating an event."""
    title: str
    description: Optional[str] = None
    start_time: str  # ISO format date-time string
    end_time: str  # ISO format date-time string
    location: Optional[str] = None

class EventResponse(BaseModel):
    """Schema for event responses."""
    id: int
    title: str
    description: Optional[str] = None
    start_time: str  # ISO format date-time string
    end_time: str  # ISO format date-time string
    location: Optional[str] = None
    created_at: str  # ISO format date-time string
    updated_at: str  # ISO format date-time string
    owner_id: int

    class Config:
        from_attributes = True

class EventUpdate(BaseModel):
    """Schema for updating an event."""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None  # ISO format date-time string
    end_time: Optional[str] = None  # ISO format date-time string
    location: Optional[str] = None

    class Config:
        from_attributes = True