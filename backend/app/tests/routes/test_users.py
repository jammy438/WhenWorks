# test that 404 is raised when no users are found
# test that id is returned correctly when fetching users
# test that correct error message is returned when database is empty

import pytest
from unittest.mock import MagicMock, patch
from typing import Any, List
from app.models.user import User
from app.api.routes.users import get_users, get_user_by_id
from fastapi import HTTPException

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db

def test_get_users_empty_db(mock_db) -> None:
    """Test that no users are returned when the database is empty."""
    mock_db.query.return_value.all.return_value = []
    
    with pytest.raises(HTTPException) as exc_info:
        get_users(db=mock_db)
        
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "No users found"

    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.all.assert_called_once()

def test_get_users_returns_users_with_correct_data(mock_db) -> None:
    """Test that id is returned correctly when fetching users."""
    test_user_1 = MagicMock()
    test_user_1.id = 1
    test_user_1.username = "testuser1"
    test_user_1.email = "test1@email.com"
    
    test_user_2 = MagicMock()
    test_user_2.id = 2
    test_user_2.username = "testuser2"
    test_user_2.email = "test2@email.com"

    mock_query = MagicMock()
    mock_query.all.return_value = [test_user_1, test_user_2]
    mock_db.query.return_value = mock_query

    # Type annotation to help with type checker
    result: List[Any] = get_users(db=mock_db)

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].username == "testuser1"
    assert result[0].email == "test1@email.com"
    
    assert result[1].id == 2
    assert result[1].username == "testuser2"
    assert result[1].email == "test2@email.com"
    
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.all.assert_called_once()

def test_get_users_by_id(mock_db) -> None:
    """Tests that the database can get a user by their id"""
    # Mock user data for testing by creating a user with id 3
    test_user_3 = MagicMock()
    test_user_3.id = 3

    mock_query = MagicMock()
    # mock the query, then filter it to return the user with id 3
    mock_query.filter.return_value.first.return_value= test_user_3
    #mock the query to return the mock_query
    mock_db.query.return_value = mock_query

    # tells the type checker "this result can be any type, don't try to enforce SQLAlchemy rules on it
    result: Any = get_user_by_id(user_id=3, db=mock_db)

    assert result.id == 3
        
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()

def test_get_user_by_id_not_found(mock_db) -> None:
    """Test that a 404 error is raised when the user is not found."""
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query

    with pytest.raises(HTTPException) as exc_info:
        get_user_by_id(user_id=999, db=mock_db)
        
    assert exc_info.value.status_code == 404
    assert str(exc_info.value.detail) == "User not found"

    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.return_value.first.assert_called_once()