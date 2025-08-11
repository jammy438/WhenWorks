# AUTH ROUTES TESTING - COMPREHENSIVE TEST SUITE
# ================================================
# This test file demonstrates several advanced testing concepts:
# 1. Mocking with unittest.mock (MagicMock, patch decorators)
# 2. Testing FastAPI route functions directly
# 3. Database session mocking for SQLAlchemy
# 4. Exception testing with pytest.raises
# 5. Side effects for simulating different database states
# 6. Proper bcrypt hash mocking to avoid cryptographic errors
# 7. Patch targeting (patching where functions are used, not defined)

# Test Coverage:
# - User registration with validation
# - User login with credential verification  
# - User profile retrieval and updates
# - Conflict handling (duplicate emails/usernames)
# - Password hashing integration
# - Database transaction mocking

# Key Testing Patterns Demonstrated:
# - Fixture usage for reusable test data
# - Mock chaining for complex database queries
# - Sequential query simulation with side_effect
# - Proper type annotations for optional parameters
# - Security testing with bcrypt hash formats
# - Exception assertion with pytest.raises
# - Mock verification with assert_called_once_with

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from typing import Any, Optional

# Add the backend directory to Python path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException, status
from app.api.routes.auth_routes import register_user, login_user, get_current_user_info, update_user_info, delete_user
from app.models.user import User

@pytest.fixture
def mock_db():
    """
    PYTEST FIXTURE CONCEPT: Creates a reusable mock database session.
    Fixtures provide consistent test data/objects across multiple tests.
    The 'mock_db' parameter in test functions automatically receives this object.
    """
    db = MagicMock()
    return db

def mock_user(user_id: int = 1, username: str = "testuser", email: str = "test@example.com", name: str = "Test User"):
    """
    MOCK OBJECT CREATION: Creates a mock User object with spec=User.
    Using spec ensures the mock has the same interface as the real User model.
    
    BCRYPT HASH FORMAT: Uses proper bcrypt format ($2b$12$...) instead of plain text.
    This prevents 'passlib.exc.UnknownHashError' when password verification is tested.
    Real bcrypt hashes have: $algorithm$cost$salt+hash
    """
    user = MagicMock(spec=User)
    user.id = user_id
    user.username = username
    user.email = email
    user.name = name
    # CRITICAL: Use properly formatted bcrypt hash to avoid passlib errors
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdkxuivzBmcHW"  # "password"
    return user

def mock_user_create_data(username: str = "newuser", email: str = "new@example.com", password: str = "password123"):
    """
    PYDANTIC SCHEMA MOCKING: Simulates UserCreate request schema.
    In real FastAPI, this would be a Pydantic model with validation.
    Mock objects allow testing without actual HTTP requests.
    """
    user_data = MagicMock()
    user_data.username = username
    user_data.email = email
    user_data.password = password
    return user_data

def mock_user_login_data(email: str = "test@example.com", password: str = "password123"):
    """Mock UserLogin schema data for authentication testing."""
    user_data = MagicMock()
    user_data.email = email
    user_data.password = password
    return user_data

def mock_user_update_data(username: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None):
    """
    OPTIONAL FIELDS MOCKING: Simulates partial updates where fields can be None.
    This tests the PATCH-style update behavior where only provided fields are updated.
    
    TYPE ANNOTATION FIX: Using Optional[str] instead of str = None for proper type checking.
    Optional[str] is equivalent to Union[str, None] but more readable.
    """
    user_data = MagicMock()
    user_data.username = username
    user_data.email = email
    user_data.password = password
    return user_data

# ================================
# REGISTRATION TESTS
# ================================

@patch('app.api.routes.auth_routes.get_password_hash')  # Patch where it's used
@patch('app.api.routes.auth_routes.User')  # Patch where it's used
def test_register_user_success(mock_user_class, mock_hash, mock_db) -> None:
    """
    COMPREHENSIVE REGISTRATION TEST:
    - Tests successful user creation flow
    - Validates database operations (add, commit, refresh)
    - Ensures password hashing is called correctly
    - Verifies no existing user conflicts
    
    PATCH TARGETING CONCEPT: Patch where functions are imported/used, not where they're defined.
    When auth_routes.py imports: "from app.utils.auth import get_password_hash"
    You must patch the reference in auth_routes, not the original in utils.auth
    
    MOCK CHAINING: mock_db.query.return_value.filter.return_value.first.return_value
    This simulates: db.query(User).filter(User.email == email).first()
    """
    user_data = mock_user_create_data()
    new_user = mock_user(1, "newuser", "new@example.com")
    
    mock_user_class.return_value = new_user
    mock_hash.return_value = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdkxuivzBmcHW"
    
    # DATABASE MOCK SETUP: Simulates queries returning None (no existing users)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    result: Any = register_user(user_data=user_data, db=mock_db)

    # ASSERTIONS: Verify expected behavior
    assert result.username == "newuser"
    assert result.email == "new@example.com"
    
    # MOCK VERIFICATION: Ensure functions were called with correct parameters
    mock_hash.assert_called_once_with("password123")
    mock_db.add.assert_called_once_with(new_user)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(new_user)

def test_register_user_email_exists(mock_db) -> None:
    """
    CONFLICT TESTING: Tests duplicate email validation.
    
    SIDE_EFFECT CONCEPT: side_effect allows different return values for multiple calls.
    [existing_user, None] means:
    - First query (email check) returns existing_user 
    - Second query (username check) returns None
    This simulates finding an email conflict but no username conflict.
    """
    user_data = mock_user_create_data()
    existing_user = mock_user()
    
    mock_db.query.return_value.filter.return_value.first.side_effect = [existing_user, None]
    
    # EXCEPTION TESTING: pytest.raises captures and validates HTTPException
    with pytest.raises(HTTPException) as exc_info:
        register_user(user_data=user_data, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert str(exc_info.value.detail) == "Email already registered"

def test_register_user_username_exists(mock_db) -> None:
    """Tests duplicate username validation using side_effect pattern."""
    user_data = mock_user_create_data()
    existing_user = mock_user()
    
    # [None, existing_user] = no email conflict, username conflict  
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, existing_user]
    
    with pytest.raises(HTTPException) as exc_info:
        register_user(user_data=user_data, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert str(exc_info.value.detail) == "Username already taken"

# ================================
# LOGIN/AUTHENTICATION TESTS
# ================================

@patch('app.api.routes.auth_routes.create_access_token')  # Patch where it's used
@patch('app.api.routes.auth_routes.verify_password')  # Patch where it's used
def test_login_user_success(mock_verify, mock_create_token, mock_db) -> None:
    """
    AUTHENTICATION FLOW TESTING:
    - Mocks password verification (bcrypt comparison)
    - Mocks JWT token generation
    - Tests successful login response format
    
    DECORATOR ORDER: @patch decorators are applied bottom-up:
    - mock_verify corresponds to verify_password (second decorator)  
    - mock_create_token corresponds to create_access_token (first decorator)
    """
    user_data = mock_user_login_data()
    db_user = mock_user()
    
    mock_db.query.return_value.filter.return_value.first.return_value = db_user
    mock_verify.return_value = True
    mock_create_token.return_value = "fake_jwt_token_123"
    
    result: Any = login_user(user_data=user_data, db=mock_db)
    
    # JWT TOKEN RESPONSE FORMAT: Standard OAuth2 bearer token format
    assert result["access_token"] == "fake_jwt_token_123"
    assert result["token_type"] == "bearer"
    
    # VERIFY PARAMETERS: Ensure password verification called with correct values
    mock_verify.assert_called_once_with("password123", "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdkxuivzBmcHW")
    mock_create_token.assert_called_once()

def test_login_user_not_found(mock_db) -> None:
    """
    AUTHENTICATION ERROR TESTING: Tests user not found scenario.
    
    HTTP 401 vs 400: 
    - 401 Unauthorized: Authentication failed (wrong credentials)
    - 400 Bad Request: Validation error (malformed data)
    
    WWW-Authenticate header required for 401 responses per HTTP spec.
    """
    user_data = mock_user_login_data("nonexistent@example.com")
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        login_user(user_data=user_data, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert str(exc_info.value.detail) == "Invalid credentials"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

@patch('app.api.routes.auth_routes.verify_password')  # Patch where it's used
def test_login_user_wrong_password(mock_verify, mock_db) -> None:
    """Tests password verification failure - user exists but password is wrong."""
    user_data = mock_user_login_data()
    db_user = mock_user()
    
    mock_db.query.return_value.filter.return_value.first.return_value = db_user
    mock_verify.return_value = False  # Password verification fails
    
    with pytest.raises(HTTPException) as exc_info:
        login_user(user_data=user_data, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert str(exc_info.value.detail) == "Invalid credentials"

# ================================
# USER INFO RETRIEVAL TESTS
# ================================

def test_get_current_user_info_success() -> None:
    """
    SIMPLE PASS-THROUGH TESTING: Tests endpoint that just returns current user.
    No database operations or external dependencies to mock.
    This tests the FastAPI dependency injection system indirectly.
    """
    current_user = mock_user()
    
    result: Any = get_current_user_info(current_user=current_user)
    
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    assert result.id == 1

# ================================
# USER UPDATE TESTS
# ================================

@patch('app.api.routes.auth_routes.get_password_hash')  # Patch where it's used
def test_update_user_info_username_success(mock_hash, mock_db) -> None:
    """
    PARTIAL UPDATE TESTING: Tests PATCH-style updates where only some fields change.
    
    SIDE_EFFECT FOR SEQUENTIAL QUERIES:
    1. First query: Check username conflicts (returns None - no conflict)
    2. Second query: Fetch updated user after database update
    """
    current_user = mock_user()
    user_data = mock_user_update_data(username="newusername")
    updated_user = mock_user(1, "newusername", "test@example.com")
    
    # Mock the conflict check queries to return None (no conflicts)
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, updated_user]
    mock_db.query.return_value.filter.return_value.update = MagicMock()
    mock_db.commit = MagicMock()
    
    result: Any = update_user_info(user_data=user_data, current_user=current_user, db=mock_db)
    
    assert result.username == "newusername"
    
    # DICTIONARY UPDATE VERIFICATION: Ensure correct SQL UPDATE parameters
    expected_update_data = {'username': 'newusername', 'name': 'newusername'}
    mock_db.query.return_value.filter.return_value.update.assert_called_once_with(expected_update_data)

def test_update_user_info_username_conflict(mock_db) -> None:
    """
    CONFLICT DETECTION TESTING: Tests username uniqueness validation.
    return_value (not side_effect) because we expect immediate conflict on first query.
    """
    current_user = mock_user(1)
    user_data = mock_user_update_data(username="existinguser")
    conflicting_user = mock_user(2, "existinguser")
    
    mock_db.query.return_value.filter.return_value.first.return_value = conflicting_user
    
    with pytest.raises(HTTPException) as exc_info:
        update_user_info(user_data=user_data, current_user=current_user, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert str(exc_info.value.detail) == "Username already taken"

def test_update_user_info_email_conflict(mock_db) -> None:
    current_user = mock_user(1)
    user_data = mock_user_update_data(email="existing@example.com")
    conflicting_user = mock_user(2, "otheruser", "existing@example.com")
    
    # SINGLE QUERY MOCK: Return conflicting user on first database query
    mock_db.query.return_value.filter.return_value.first.return_value = conflicting_user
    
    with pytest.raises(HTTPException) as exc_info:
        update_user_info(user_data=user_data, current_user=current_user, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert str(exc_info.value.detail) == "Email already taken"

@patch('app.api.routes.auth_routes.get_password_hash')  # Patch where it's used
def test_update_user_info_password_change_success(mock_hash, mock_db) -> None:
    """
    PASSWORD UPDATE TESTING: Tests secure password change workflow.
    
    KEY CONCEPTS:
    - Password updates don't require conflict checking (passwords are user-specific)
    - New password must be hashed before database storage
    - Original password verification could be added for extra security
    """
    current_user = mock_user()
    user_data = mock_user_update_data(password="newpassword123")
    updated_user = mock_user()
    
    mock_hash.return_value = "$2b$12$NEW_HASHED_PASSWORD_HERE"
    # For password-only updates, no conflict checks should happen
    mock_db.query.return_value.filter.return_value.first.return_value = updated_user
    mock_db.query.return_value.filter.return_value.update = MagicMock()
    mock_db.commit = MagicMock()
    
    result: Any = update_user_info(user_data=user_data, current_user=current_user, db=mock_db)
    
    # SECURITY VERIFICATION: Ensure password was hashed before storage
    mock_hash.assert_called_once_with("newpassword123")
    
    expected_update_data = {'hashed_password': '$2b$12$NEW_HASHED_PASSWORD_HERE'}
    mock_db.query.return_value.filter.return_value.update.assert_called_once_with(expected_update_data)

def test_update_user_info_no_changes_provided(mock_db) -> None:
    """
    NO-OP UPDATE TESTING: Tests behavior when no fields are provided for update.
    
    EFFICIENCY CONCEPT: Avoid unnecessary database operations when no changes requested.
    This is common in PATCH endpoints where all fields are optional.
    """
    current_user = mock_user()
    user_data = mock_user_update_data()  # All fields are None
    
    result: Any = update_user_info(user_data=user_data, current_user=current_user, db=mock_db)
    
    assert result == current_user
    
    # NEGATIVE TESTING: Verify NO database operations occurred
    mock_db.query.assert_not_called()
    mock_db.commit.assert_not_called()

# ================================
# USER DELETION TESTS
# ================================

def test_delete_user_account_success(mock_db) -> None:
    """
    DELETE OPERATION TESTING: Tests user account deletion.
    
    TRANSACTION CONCEPTS:
    - delete() marks object for deletion
    - commit() actually removes from database
    - Soft deletes (marking as inactive) vs hard deletes could be implemented
    
    RETURN VALUE: Delete operations typically return None (204 No Content)
    """
    current_user = mock_user()
    
    mock_db.delete = MagicMock()
    mock_db.commit = MagicMock()
    
    result: Any = delete_user(current_user=current_user, db=mock_db)
    
    assert result is None
    
    # TRANSACTION VERIFICATION: Ensure proper delete sequence
    mock_db.delete.assert_called_once_with(current_user)
    mock_db.commit.assert_called_once()