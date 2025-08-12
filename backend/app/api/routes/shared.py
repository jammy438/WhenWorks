#post - share calendar with others
#get - have calendars shared with you

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.user import User
from app.models.events import Event
from schemas import EventResponse, EventCreate, EventUpdate
from app.core.logging import get_logger
from schemas import UserResponse
from app.utils.auth import get_current_user

#Logging is heavy. Trace, info, warn and error (standard) - should be able to configure what level you want. change infos to traces? would allow to debug in trace mode. live would be info. diff levels of logging at test, live etc.
# utalise global logger to - create own logger class as wrapper which can set variables auto and then import it from wrapper -  link to config and manually setin env?
logger = get_logger(__name__)

router = APIRouter(prefix="/shared", tags=["shared"])

def get_database_connection():
    """Get a database connection."""
    return get_db()

@router.get("/", response_model=list[UserResponse])
def get_shared_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Get users with whom the current user's calendar is shared."""
    shared_users = db.query(User).filter(User.shared_with.any(id=current_user.id)).all()
    if not shared_users:
        logger.warning(f"No users found with whom {current_user.email}'s calendar is shared.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    logger.debug(f"Retrieved {len(shared_users)} users with whom {current_user.email}'s calendar is shared.")
    return shared_users

@router.post("/share/{user_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def share_calendar_with_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Share the current user's calendar with another user."""
    user_to_share = db.query(User).filter(User.id == user_id).first()
    if not user_to_share:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_to_share in current_user.shared_with:
        logger.debug(f"{current_user.email} has already shared their calendar with {user_to_share.email}.")
        return user_to_share
    
    current_user.shared_with.append(user_to_share)
    db.commit()
    db.refresh(current_user)
    logger.debug(f"{current_user.email} shared their calendar with {user_to_share.email}.")
    return user_to_share

@router.delete("/unshare/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_calendar_with_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Unshare the current user's calendar with another user."""
    user_to_unshare = db.query(User).filter(User.id == user_id).first()
    if not user_to_unshare:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_to_unshare not in current_user.shared_with:
        logger.debug(f"{current_user.email} has not shared their calendar with {user_to_unshare.email}.")
        return
    
    current_user.shared_with.remove(user_to_unshare)
    db.commit()
    logger.debug(f"{current_user.email} unshared their calendar with {user_to_unshare.email}.")

    return {"detail": "Calendar unshared successfully"}

@router.get("/shared-with-me", response_model=list[UserResponse])
def get_calendars_shared_with_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Get users who have shared their calendars with the current user."""
    users_who_shared = db.query(User).filter(User.shared_with.any(id=current_user.id)).all()
    if not users_who_shared:
        logger.warning(f"No users found who have shared their calendars with {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    logger.debug(f"Retrieved {len(users_who_shared)} users who have shared their calendars with {current_user.email}.")
    return users_who_shared

@router.post("/share-with-me/{user_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def share_calendar_with_me(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Allow another user to share their calendar with the current user."""
    user_to_share = db.query(User).filter(User.id == user_id).first()
    if not user_to_share:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user in user_to_share.shared_with:
        logger.debug(f"{user_to_share.email} has already shared their calendar with {current_user.email}.")
        return current_user
    
    user_to_share.shared_with.append(current_user)
    db.commit()
    db.refresh(user_to_share)
    logger.debug(f"{user_to_share.email} shared their calendar with {current_user.email}.")
    return current_user

@router.delete("/unshare-with-me/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_calendar_with_me(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Allow another user to stop sharing their calendar with the current user."""
    user_to_unshare = db.query(User).filter(User.id == user_id).first()
    if not user_to_unshare:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user not in user_to_unshare.shared_with:
        logger.debug(f"{user_to_unshare.email} has not shared their calendar with {current_user.email}.")
        return
    
    user_to_unshare.shared_with.remove(current_user)
    db.commit()
    logger.debug(f"{user_to_unshare.email} unshared their calendar with {current_user.email}.")
    
    return {"detail": "Calendar unshared successfully"}

@router.get("/shared-with-me/{user_id}", response_model=UserResponse)
def get_shared_calendar_with_me(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Get a specific user's calendar that has been shared with the current user."""
    user_to_check = db.query(User).filter(User.id == user_id).first()
    if not user_to_check:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user not in user_to_check.shared_with:
        logger.debug(f"{user_to_check.email} has not shared their calendar with {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not shared with you")
    
    logger.debug(f"Retrieved shared calendar for {user_to_check.email} for {current_user.email}.")
    return user_to_check

@router.get("/shared-with-me/{user_id}/events", response_model=list[EventResponse])
def get_shared_events_with_me(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Get events from a specific user's calendar that has been shared with the current user."""
    user_to_check = db.query(User).filter(User.id == user_id).first()
    if not user_to_check:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user not in user_to_check.shared_with:
        logger.debug(f"{user_to_check.email} has not shared their calendar with {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not shared with you")
    
    events = db.query(Event).filter(Event.owner_id == user_to_check.id).all()
    if not events:
        logger.warning(f"No events found in {user_to_check.email}'s calendar shared with {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
    
    logger.debug(f"Retrieved {len(events)} events from {user_to_check.email}'s calendar shared with {current_user.email}.")
    return events

@router.post("/share-with-me/{user_id}/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def share_event_with_me(event_data: EventCreate, user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Allow another user to share a specific event with the current user."""
    user_to_share = db.query(User).filter(User.id == user_id).first()
    if not user_to_share:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user in user_to_share.shared_with:
        # Create new event for the current user using the EventCreate data
        new_event = Event(
            title=event_data.title,
            description=event_data.description,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            location=event_data.location,
            owner_id=current_user.id
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        logger.debug(f"{user_to_share.email} shared an event with {current_user.email}.")
        return new_event
    
    logger.debug(f"{user_to_share.email} has not shared their calendar with {current_user.email}.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Calendar not shared with you")

@router.delete("/unshare-with-me/{user_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_event_with_me(event_id: int, user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Allow another user to stop sharing a specific event with the current user."""
    user_to_unshare = db.query(User).filter(User.id == user_id).first()
    if not user_to_unshare:
        logger.warning(f"User with id {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user not in user_to_unshare.shared_with:
        logger.debug(f"{user_to_unshare.email} has not shared their calendar with {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not shared with you")
    
    event_to_unshare = db.query(Event).filter(Event.id == event_id, Event.owner_id == user_to_unshare.id).first()
    if not event_to_unshare:
        logger.warning(f"Event with id {event_id} not found in {user_to_unshare.email}'s calendar.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    db.delete(event_to_unshare)
    db.commit()
    logger.debug(f"{user_to_unshare.email} unshared event {event_to_unshare.title} with {current_user.email}.")
    
    return {"detail": "Event unshared successfully"}
