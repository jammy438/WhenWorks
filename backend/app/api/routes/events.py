# GET /events (get user's events)
# POST /events (create event)
# PUT /events/{id} (update event)
# DELETE /events/{id} (delete event)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from app.models.events import Event
from app.core.logging import get_logger
from schemas import EventCreate, EventResponse, EventUpdate
from app.utils.auth import get_current_user
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])

def get_database_connection():
    """Get a database connection."""
    return get_db()

@router.get("/", response_model=list[EventResponse])
def get_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Get all events for the current user."""
    events = db.query(Event).filter(Event.owner_id == current_user.id).all()
    if not events:
        logger.warning(f"No events found for user {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
    logger.debug(f"Retrieved {len(events)} events for user {current_user.username}.")
    return events

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Create a new event for the current user."""
    new_event = Event(**event.dict(), owner_id=current_user.id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    logger.debug(f"Event {new_event.title} created for user {current_user.username}.")
    return new_event

@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_update: EventUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Update an existing event for the current user."""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        logger.warning(f"Event with id {event_id} not found for user {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    for key, value in event_update.dict(exclude_unset=True).items():
        setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    logger.debug(f"Event {event.title} updated for user {current_user.username}.")
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_database_connection)):
    """Delete an existing event for the current user."""
    event = db.query(Event).filter(Event.id == event_id, Event.owner_id == current_user.id).first()
    if not event:
        logger.warning(f"Event with id {event_id} not found for user {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    db.delete(event)
    db.commit()
    logger.debug(f"Event {event.title} deleted for user {current_user.username}.")
    return {"detail": "Event deleted successfully"}

