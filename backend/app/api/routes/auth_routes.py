# API endpoints for user authentication and management
# POST/register, POST/login, GET/me, PUT/me, DELETE/me
#Import utility functions

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user
from database import get_db
from app.models.user import User
import logging
from schemas import TokenData, UserCreate, UserResponse, UserUpdate
from app.utils.auth import verify_password, get_password_hash, create_access_token
from pydantic import BaseModel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

def get_database_connection():
    """Get a database connection."""
    return get_db()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: User, db: Session = Depends(get_db)):
    """Register a new user."""
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        logger.warning(f"User with email {user.email} already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User {user.email} registered successfully.")
    return user

@router.post("/login", response_model=User)
def login_user(user: User, db: Session = Depends(get_database_connection)):
    """Login a user."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not db_user.verify_password(user.password):
        logger.warning(f"Failed login attempt for email {user.email}.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    logger.info(f"User {user.email} logged in successfully.")
    return TokenData

@router.get("/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get the current logged-in user's information."""
    logger.info(f"Retrieved current user info for {current_user.email}.")
    return current_user

@router.put("/me", response_model=User)
def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    """Update the current user's information."""
    
    if user_data.email != current_user.email:
        logger.warning(f"User {current_user.email} attempted to update email to {user_data.email}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change email address")
    
    # if user_data.password:
    #     hashed_password = get_password_hash(user_data.password)
    #     user.hashed_password = hashed_password
    #     logger.info(f"User {current_user.email} updated password successfully.")

    db.commit()

    db.refresh(current_user)
    logger.info(f"User {current_user.email} updated successfully.")
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Delete the current user's account."""
    db.delete(current_user)
    db.commit()
    logger.info(f"User {current_user.email} deleted successfully.")
    return {"detail": "User deleted successfully"}


