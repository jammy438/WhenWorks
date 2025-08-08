# API endpoints for user authentication and management
# POST/register, POST/login, GET/me, PUT/me, DELETE/me

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user, verify_password, get_password_hash, create_access_token
from database import get_db
from app.models.user import User
import logging
from schemas import Token, TokenData, UserCreate, UserResponse, UserUpdate, UserLogin
from datetime import timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"User with email {user_data.email} already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        logger.warning(f"Username {user_data.username} already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    
    # Hash the password and create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.username,  # Using username as name since schema doesn't have name
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User {new_user.email} registered successfully.")
    return new_user

@router.post("/login", response_model=Token)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login a user and return JWT token."""
    # Find user by email
    db_user = db.query(User).filter(User.email == user_data.email).first()
    
    if not db_user:
        logger.warning(f"User not found for email {user_data.email}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Explicitly get the password hash as string
    stored_password_hash = str(db_user.hashed_password)
    
    # Verify password
    if not verify_password(user_data.password, stored_password_hash):
        logger.warning(f"Invalid password for email {user_data.email}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)  # 30 minutes
    access_token = create_access_token(
        data={"sub": db_user.username}, 
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {user_data.email} logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get the current logged-in user's information."""
    logger.info(f"Retrieved current user info for {current_user.email}.")
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's information."""
    
    update_data = {}
    
    # Check and prepare username update
    if user_data.username:
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        update_data['username'] = user_data.username
        update_data['name'] = user_data.username  # Update name field too
    
    # Check and prepare email update
    if user_data.email:
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        update_data['email'] = user_data.email
    
    # Check and prepare password update
    if user_data.password:
        hashed_password = get_password_hash(user_data.password)
        update_data['hashed_password'] = hashed_password
        logger.debug(f"User {current_user.email} updated password successfully.")
    
    # Perform the update if there's data to update
    if update_data:
        db.query(User).filter(User.id == current_user.id).update(update_data)
        db.commit()
        
        # Get the updated user
        updated_user = db.query(User).filter(User.id == current_user.id).first()
        logger.debug(f"User updated successfully.")
        return updated_user
    
    # No updates needed
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete the current user's account."""
    db.delete(current_user)
    db.commit()
    logger.debug(f"User {current_user.email} deleted successfully.")
    return None