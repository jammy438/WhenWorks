# for pydantic models

from pydantic import BaseModel
from typing import Optional

class TokenData(BaseModel):
    """Schema for token data."""
    username:  Optional[str] = None

class UserCreate(BaseModel):
    """Schema for registration requests."""
    username: str
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

