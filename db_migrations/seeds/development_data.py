import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import or_

# This file assumes it's being imported after the working directory has been changed to backend
from backend.app.models.user import User
from backend.app.models.events import Event
from backend.app.utils.auth import get_password_hash

def create_seed_users(db: Session) -> list[User]:
    """Create seed users for development."""
    seed_users = [
        {"username": "admin", "name": "Admin User", "email": "admin@whenworks.dev", "password": "admin123"},
        {"username": "testuser", "name": "Test User", "email": "test@whenworks.dev", "password": "test123"},
        {"username": "developer", "name": "Developer User", "email": "dev@whenworks.dev", "password": "dev123"}
    ]
    
    created_users = []
    for user_data in seed_users:
        # Check if user already exists by email OR username
        existing_user = db.query(User).filter(
            or_(
                User.email == user_data["email"],
                User.username == user_data["username"]
            )
        ).first()
        
        if existing_user:
            print(f"User {user_data['username']} ({user_data['email']}) already exists")
            created_users.append(existing_user)
            continue
            
        user = User(
            username=user_data["username"],
            name=user_data["name"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"])
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created_users.append(user)
        print(f"✅ Created user: {user.name} ({user.email})")
    
    return created_users

def create_seed_events(db: Session, users: list[User]) -> list[Event]:
    """Create seed events for development."""
    if not users:
        return []
    
    seed_events = [
        {
            "title": "Team Standup",
            "description": "Daily team standup meeting",
            "start_time": datetime.utcnow() + timedelta(hours=1),
            "end_time": datetime.utcnow() + timedelta(hours=1, minutes=30),
            "location": "Conference Room A",
            "owner_id": users[0].id
        },
        {
            "title": "Project Planning",
            "description": "Sprint planning for Q4",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=1, hours=2),
            "location": "Virtual",
            "owner_id": users[1].id if len(users) > 1 else users[0].id
        },
        {
            "title": "Code Review",
            "description": "Review new feature implementation",
            "start_time": datetime.utcnow() + timedelta(days=2),
            "end_time": datetime.utcnow() + timedelta(days=2, hours=1),
            "location": "Dev Room",
            "owner_id": users[2].id if len(users) > 2 else users[0].id
        }
    ]
    
    created_events = []
    for event_data in seed_events:
        existing_event = db.query(Event).filter(
            Event.title == event_data["title"],
            Event.owner_id == event_data["owner_id"]
        ).first()
        
        if existing_event:
            print(f"Event '{event_data['title']}' already exists")
            created_events.append(existing_event)
            continue
            
        event = Event(**event_data)
        db.add(event)
        db.commit()
        db.refresh(event)
        created_events.append(event)
        print(f"✅ Created event: {event.title}")
    
    return created_events

def seed_development_database(db: Session):
    """Main function to seed the database."""
    try:
        users = create_seed_users(db)
        events = create_seed_events(db, users)
        return {"users": len(users), "events": len(events)}
    except Exception as e:
        db.rollback()
        raise
