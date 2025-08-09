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
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.api.routes.events import get_events, create_event, update_event, delete_event
from app.models.events import Event
from typing import List, Any

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db

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
