# GET api call for users

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.user import User
from app.core.logging import get_logger
from schemas import UserResponse, UserOut

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Search users to share with"""
    users = db.query(User).all()
    if not users: # Checks if users list is empty
        logger.warning("No users found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    return users

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Get a user by their ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    logger.debug(f"Retrieved user with id {user_id}.")
    return user

# The above endpoint accepts a user ID from the URL path, queries the database
# to find the matching user record, and returns the user's information.
# If no user is found with the given ID, it returns a 404 error.
    
# Args:
        # user_id (int): The unique identifier of the user to retrieve (from URL path)
       # db (Session): Database session injected by FastAPI dependency system
        
# Returns:
       # UserOut: User object serialized according to UserOut schema (excludes sensitive data)
    # Raises: HTTPException (404): If no user exists with the provided ID