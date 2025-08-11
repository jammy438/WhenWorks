#test that all events are gotten for current user
#test that no events found returns 404 for current user
#test that an event can be created for the current user
#test that an event cannot be created with invalid data
#test that an event can be updated for the current user
#test that an event cannot be updated with invalid data
#test that an event cannot be updated if it does not exist or belong to current user
#test that an event can be deleted for the current user
#test that an event cannot be deleted if it does not exist or belong to current user

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.api.routes.events import get_events, create_event, update_event, delete_event
from app.models.events import Event
from typing import List, Any

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db

def mock_event():
    """Mock event object for testing."""
    event = MagicMock(spec=Event)
    event.id = 1
    event.title = "Test Event"
    event.description = "This is a test event."
    event.date = "2023-10-01"
    event.owner_id = 1
    return event

def test_get_events_empty_db(mock_db) -> None:
    """Test that no events are returned when the database is empty."""
    mock_db.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        get_events(db=mock_db, current_user=MagicMock(id=1))

    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "No events found"

    mock_db.query.assert_called_once_with(Event)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.all.assert_called_once()

def test_update_event_not_found(mock_db) -> None:
    """Test that update raises 404 when event doesn't exist."""
    Test_user_4 = MagicMock(id=4, username="testuser1")
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        update_event(db=mock_db, event_id=999, event_update=MagicMock(), current_user=Test_user_4)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "Event not found"

def test_get_events_returns_events_with_correct_data(mock_db) -> None:
    Test_user_1 = MagicMock(id=1, username="testuser1")
    Test_event_1 = MagicMock(id=1, title="Test Event 1", owner_id=Test_user_1.id)

    mock_query = MagicMock()
    mock_query.all.return_value = [Test_event_1]
    mock_db.query.return_value.filter.return_value = mock_query

    result: List[Any] = get_events(db=mock_db, current_user=Test_user_1)

    assert len(result) == 1
    assert result[0].id == 1

    assert result[0].title == "Test Event 1"
    assert result[0].owner_id == Test_user_1.id

    mock_db.query.assert_called_once_with(Event)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.all.assert_called_once()

@patch('app.api.routes.events.Event')
def test_create_event(mock_event, mock_db) -> None:
    """Test that an event can be created for the current user."""
    Test_user_4 = MagicMock(id=4, username="testuser1")
    Test_event_4 = MagicMock(id=4, title="Test Event 4", owner_id=Test_user_4.id)
    
    mock_event.return_value = Test_event_4
    
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    result: Any= create_event(db=mock_db, event=MagicMock() , current_user=Test_user_4)

    assert result.title == "Test Event 4"
    assert result.owner_id == Test_user_4.id

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(result)

@patch('app.api.routes.events.Event')
def test_update_event(mock_event, mock_db) -> None:
    """Test that an event can be updated for the current user."""
    Test_user_4 = MagicMock(id=4, username="testuser1")
    Test_event_4 = MagicMock(id=4, title="Test Event 4", owner_id=Test_user_4.id)
    
    mock_event.return_value = Test_event_4
    
    mock_db.query.return_value.filter.return_value.first.return_value = Test_event_4
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    result: Any= update_event(db=mock_db, event_id=MagicMock, event_update=MagicMock() , current_user=Test_user_4)

    assert result.title == "Test Event 4"
    assert result.owner_id == Test_user_4.id

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(result)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()

@patch('app.api.routes.events.Event')
def test_event_not_found(mock_event, mock_db) -> None:
    """Test that when event isn't found it raises an error."""
    Test_user_5 = MagicMock(id=5, username="testuser1")
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        update_event(db=mock_db, event_id=999, event_update=MagicMock(), current_user=Test_user_5)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "Event not found"

    mock_db.query.assert_called_once_with(mock_event)
    mock_db.query.return_value.filter.assert_called_once()

@patch('app.api.routes.events.Event')
def test_delete_event(mock_event, mock_db) -> None:
    """Test that an event can be deleted for the current user."""
    Test_user_5 = MagicMock(id=5, username="testuser1")
    Test_event_5 = MagicMock(id=5, title="Test Event 4", owner_id=Test_user_5.id)
    
    mock_event.return_value = Test_event_5
    
    mock_db.query.return_value.filter.return_value.first.return_value = Test_event_5
    mock_db.delete = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.commit.return_value = None
    mock_db.delete.return_value = None
    
    result: Any= delete_event(db=mock_db, event_id=5, current_user=Test_user_5)

    mock_db.delete.assert_called_once_with(Test_event_5)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()

@patch('app.api.routes.events.Event')
def test_update_event_wrong_owner(mock_event, mock_db) -> None:
    """Test that an event cannot be updated if it does not belong to the current user."""
    Test_user_6 = MagicMock(id=6, username="testuser1")
    Test_event_6 = MagicMock(id=6, title="Test Event 6", owner_id=7)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        update_event(db=mock_db, event_id=6, event_update=MagicMock(), current_user=Test_user_6)
    
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "Event not found"
    
    mock_db.query.assert_called_once_with(mock_event)
    mock_db.query.return_value.filter.assert_called_once()
