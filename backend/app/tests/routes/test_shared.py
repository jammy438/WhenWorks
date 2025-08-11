# test that shared users can be retrieved for current user
# test that no shared users returns 404 for current user
# test that calendar can be shared with another user
# test that calendar cannot be shared with nonexistent user
# test that calendar can be unshared with another user
# test that calendar cannot be unshared with nonexistent user
# test that calendars shared with me can be retrieved
# test that no calendars shared with me returns 404
# test that shared events can be retrieved from another user's calendar
# test that shared events cannot be retrieved if calendar not shared
# test that event can be shared with me
# test that event cannot be shared if calendar not shared

# NEW CONCEPTS IN THIS FILE:
# 1. Testing many-to-many relationships (users sharing calendars with each other)
# 2. Testing authorization logic (checking if user has permission)
# 3. Using side_effect with functions for complex mock behavior
# 4. Testing different HTTP status codes (403 FORBIDDEN vs 404 NOT FOUND)
# 5. Testing idempotent operations (operations that can be safely repeated)
# 6. Mocking list relationships and membership testing (user in shared_with list)

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.api.routes.shared import (
    get_shared_users,
    share_calendar_with_user,
    unshare_calendar_with_user,
    get_calendars_shared_with_me,
    get_shared_events_with_me,
    share_event_with_me
)
from app.models.user import User
from app.models.events import Event
from typing import List, Any

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db

def mock_user(user_id: int = 1, username: str = "testuser", email: str = "test@example.com"):
    """Mock user object for testing."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.username = username
    user.email = email
    
    # NEW CONCEPT: Mocking list attributes for relationship testing
    # In SQLAlchemy, relationships often appear as lists
    # We initialize it as empty list so we can add/remove items in tests
    user.shared_with = []  # This simulates the many-to-many relationship
    return user

def mock_event(event_id: int = 1, title: str = "Test Event", owner_id: int = 1):
    """Mock event object for testing."""
    event = MagicMock(spec=Event)
    event.id = event_id
    event.title = title
    event.description = "Test description"
    event.owner_id = owner_id
    return event

def test_get_shared_users_empty_db(mock_db) -> None:
    """Test that no shared users are returned when none exist."""
    test_user = mock_user(1, "testuser1")
    mock_db.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        get_shared_users(db=mock_db, current_user=test_user)

    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "No users found"

    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.all.assert_called_once()

def test_get_shared_users_returns_users_with_correct_data(mock_db) -> None:
    """Test that shared users are returned with correct data."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    test_user_3 = mock_user(3, "testuser3")

    mock_query = MagicMock()
    mock_query.all.return_value = [test_user_2, test_user_3]
    mock_db.query.return_value.filter.return_value = mock_query

    result: List[Any] = get_shared_users(db=mock_db, current_user=test_user_1)

    assert len(result) == 2
    assert result[0].id == 2
    assert result[1].id == 3
    assert result[0].username == "testuser2"
    assert result[1].username == "testuser3"

    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.all.assert_called_once()

def test_share_calendar_with_user_success(mock_db) -> None:
    """Test that calendar can be shared with another user."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    
    mock_db.query.return_value.filter.return_value.first.return_value = test_user_2
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    result: Any = share_calendar_with_user(user_id=2, db=mock_db, current_user=test_user_1)

    assert result.id == 2
    assert result.username == "testuser2"

    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(test_user_1)

def test_share_calendar_user_not_found(mock_db) -> None:
    """Test that sharing calendar with nonexistent user raises 404."""
    test_user_1 = mock_user(1, "testuser1")
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        share_calendar_with_user(user_id=999, db=mock_db, current_user=test_user_1)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "User not found"

    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once()

def test_share_calendar_already_shared(mock_db) -> None:
    """Test that sharing calendar with already shared user returns user."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    
    # NEW CONCEPT: Testing list relationships between models
    # We simulate that user1 has already shared their calendar with user2
    # by adding user2 to user1's shared_with list
    test_user_1.shared_with = [test_user_2]  # Already shared
    
    mock_db.query.return_value.filter.return_value.first.return_value = test_user_2

    result: Any = share_calendar_with_user(user_id=2, db=mock_db, current_user=test_user_1)

    assert result.id == 2
    assert result.username == "testuser2"

    # NEW CONCEPT: Testing idempotent operations (operations that can be repeated safely)
    # The function should handle "already shared" gracefully without errors
    mock_db.query.assert_called_once_with(User)

def test_unshare_calendar_with_user_success(mock_db) -> None:
    """Test that calendar can be unshared with another user."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    test_user_1.shared_with = [test_user_2]  # Already shared
    
    mock_db.query.return_value.filter.return_value.first.return_value = test_user_2
    mock_db.commit = MagicMock()

    result: Any = unshare_calendar_with_user(user_id=2, db=mock_db, current_user=test_user_1)

    assert result == {"detail": "Calendar unshared successfully"}

    mock_db.query.assert_called_once_with(User)
    mock_db.commit.assert_called_once()

def test_unshare_calendar_user_not_found(mock_db) -> None:
    """Test that unsharing calendar with nonexistent user raises 404."""
    test_user_1 = mock_user(1, "testuser1")
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        unshare_calendar_with_user(user_id=999, db=mock_db, current_user=test_user_1)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "User not found"

def test_get_calendars_shared_with_me_empty(mock_db) -> None:
    """Test that no calendars shared with me returns 404."""
    test_user_1 = mock_user(1, "testuser1")
    mock_db.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        get_calendars_shared_with_me(db=mock_db, current_user=test_user_1)

    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "No users found"

def test_get_calendars_shared_with_me_returns_users(mock_db) -> None:
    """Test that calendars shared with me are returned correctly."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    test_user_3 = mock_user(3, "testuser3")

    mock_query = MagicMock()
    mock_query.all.return_value = [test_user_2, test_user_3]
    mock_db.query.return_value.filter.return_value = mock_query

    result: List[Any] = get_calendars_shared_with_me(db=mock_db, current_user=test_user_1)

    assert len(result) == 2
    assert result[0].id == 2
    assert result[1].id == 3

def test_get_shared_events_with_me_success(mock_db) -> None:
    """Test that shared events can be retrieved from another user's calendar."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    
    # NEW CONCEPT: Setting up complex relationships
    # We simulate user2 sharing their calendar with user1
    test_user_2.shared_with = [test_user_1]  # user2 shared with user1
    
    test_event_1 = mock_event(1, "Event 1", 2)
    test_event_2 = mock_event(2, "Event 2", 2)
    
    # Mock user query
    mock_db.query.return_value.filter.return_value.first.side_effect = [test_user_2]
    
    # Mock events query
    mock_events_query = MagicMock()
    mock_events_query.all.return_value = [test_event_1, test_event_2]
    
    # NEW CONCEPT: Complex mock chaining for multiple database queries
    # This function makes TWO different queries: one for User, one for Event
    # We need to mock different behaviors based on which model is being queried
    def query_side_effect(model):
        if model == User:
            return mock_db.query.return_value  # Returns the user query chain
        elif model == Event:
            mock_event_query = MagicMock()
            mock_event_query.filter.return_value = mock_events_query  # Returns the events
            return mock_event_query
    
    # NEW CONCEPT: side_effect with functions
    # Instead of a simple return value, we use a function to determine
    # what to return based on the input parameter (User vs Event model)
    mock_db.query.side_effect = query_side_effect

    result: List[Any] = get_shared_events_with_me(user_id=2, db=mock_db, current_user=test_user_1)

    assert len(result) == 2
    assert result[0].title == "Event 1"
    assert result[1].title == "Event 2"

def test_get_shared_events_calendar_not_shared(mock_db) -> None:
    """Test that shared events cannot be retrieved if calendar not shared."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    
    # NEW CONCEPT: Testing authorization/permission logic
    # We explicitly set an empty list to simulate NO sharing relationship
    test_user_2.shared_with = []  # Not shared with user1
    
    mock_db.query.return_value.filter.return_value.first.return_value = test_user_2
    
    # NEW CONCEPT: Testing different HTTP status codes
    # This tests a 404 error, but for authorization reasons (calendar not shared)
    # Different from "user not found" - it's "access denied"
    with pytest.raises(HTTPException) as exc_info:
        get_shared_events_with_me(user_id=2, db=mock_db, current_user=test_user_1)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "Calendar not shared with you"

@patch('app.api.routes.shared.Event')
def test_share_event_with_me_success(mock_event_class, mock_db) -> None:
    """Test that event can be shared with me."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    test_user_2.shared_with = [test_user_1]  # user2 shared with user1
    
    mock_event_data = MagicMock()
    mock_event_data.title = "Shared Event"
    mock_event_data.description = "Test description"
    
    test_event = mock_event(1, "Shared Event", 1)
    mock_event_class.return_value = test_event
    
    mock_db.query.return_value.filter.return_value.first.return_value = test_user_2
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    result: Any = share_event_with_me(event_data=mock_event_data, user_id=2, db=mock_db, current_user=test_user_1)

    assert result.title == "Shared Event"
    assert result.owner_id == 1

    mock_db.add.assert_called_once_with(test_event)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(test_event)

def test_share_event_calendar_not_shared(mock_db) -> None:
    """Test that event cannot be shared if calendar not shared."""
    test_user_1 = mock_user(1, "testuser1")
    test_user_2 = mock_user(2, "testuser2")
    test_user_2.shared_with = []  # Not shared with user1
    
    mock_event_data = MagicMock()
    
    mock_db.query.return_value.filter.return_value.first.return_value = test_user_2
    
    # NEW CONCEPT: Testing 403 FORBIDDEN status code
    # 403 means "I know who you are, but you don't have permission"
    # Different from 404 (not found) or 401 (not authenticated)
    # This is proper REST API design for authorization failures
    with pytest.raises(HTTPException) as exc_info:
        share_event_with_me(event_data=mock_event_data, user_id=2, db=mock_db, current_user=test_user_1)
    
    assert exc_info.value.status_code == 403  # FORBIDDEN, not 404
    assert str(exc_info.value.detail) == "Calendar not shared with you"

def test_share_event_user_not_found(mock_db) -> None:
    """Test that sharing event with nonexistent user raises 404."""
    test_user_1 = mock_user(1, "testuser1")
    mock_event_data = MagicMock()
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        share_event_with_me(event_data=mock_event_data, user_id=999, db=mock_db, current_user=test_user_1)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "User not found"