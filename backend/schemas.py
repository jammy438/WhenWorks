from pydantic import BaseModel
from typing import Optional

class TokenData(BaseModel):
    """Schema for token data."""
    username:  Optional[str] = None