"""Tests for user service."""

import pytest
from app.services import user
from app.models.user import User
from app.schemas.user import CreateUser, UpdateUser, FilterPagination


@pytest.mark.asyncio
async def test_create_user(test_db):
    """Test creating a new user."""
    create_data = CreateUser(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="SecurePass123!@"
    )
    
    result = await user.create_user(create_data, test_db)
    
    assert result is not None
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "john.doe@example.com"
    assert result.id is not None
    # Password should be hashed
    assert result.password != "SecurePass123!@"
    assert len(result.password) > 20  # Hashed passwords are longer


@pytest.mark.asyncio
async def test_get_user_by_id(test_db):
    """Test getting a user by ID."""
    # Create test user
    test_user = User(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        password="hashed_password"
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)

    # Get user by ID
    result = await user.get_user(test_user.id, test_db)
    
    assert result is not None
    assert result.id == test_user.id
    assert result.first_name == "Jane"
    assert result.email == "jane.smith@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email(test_db):
    """Test getting a user by email."""
    # Create test user
    test_user = User(
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com",
        password="hashed_password"
    )
    test_db.add(test_user)
    test_db.commit()

    # Get user by email
    result = await user.get_user_by_email("bob.johnson@example.com", test_db)
    
    assert result is not None
    assert result.email == "bob.johnson@example.com"
    assert result.first_name == "Bob"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(test_db):
    """Test getting a user by email when not found."""
    result = await user.get_user_by_email("nonexistent@example.com", test_db)
    
    assert result is None


@pytest.mark.asyncio
async def test_check_user_exists_by_email(test_db):
    """Test checking if a user exists by email."""
    # Create test user
    test_user = User(
        first_name="Alice",
        last_name="Brown",
        email="alice.brown@example.com",
        password="hashed_password"
    )
    test_db.add(test_user)
    test_db.commit()

    # Check existing user
    exists = await user.check_user_exists_by_email("alice.brown@example.com", test_db)
    assert exists is True

    # Check non-existing user
    not_exists = await user.check_user_exists_by_email("nobody@example.com", test_db)
    assert not_exists is False


@pytest.mark.asyncio
async def test_update_user(test_db):
    """Test updating a user."""
    # Create test user
    test_user = User(
        first_name="Charlie",
        last_name="Wilson",
        email="charlie.wilson@example.com",
        password="hashed_password"
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)

    # Update user
    update_data = UpdateUser(first_name="Charles", last_name="Wilson Jr.")
    result = await user.update_user(test_user.id, update_data, test_db)
    
    assert result is not None
    assert result.id == test_user.id
    assert result.first_name == "Charles"
    assert result.last_name == "Wilson Jr."
    assert result.email == "charlie.wilson@example.com"  # Email unchanged


@pytest.mark.asyncio
async def test_update_user_password(test_db):
    """Test updating a user's password."""
    # Create test user
    test_user = User(
        first_name="David",
        last_name="Lee",
        email="david.lee@example.com",
        password="old_hashed_password"
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)
    old_password = test_user.password

    # Update password
    update_data = UpdateUser(password="NewSecurePass123!@")
    result = await user.update_user(test_user.id, update_data, test_db)
    
    assert result is not None
    assert result.password != old_password  # Password changed
    assert result.password != "NewSecurePass123!@"  # Password is hashed
    assert len(result.password) > 20  # Hashed passwords are longer


@pytest.mark.asyncio
async def test_delete_user(test_db):
    """Test deleting a user."""
    # Create test user
    test_user = User(
        first_name="Eve",
        last_name="Martinez",
        email="eve.martinez@example.com",
        password="hashed_password"
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)
    user_id = test_user.id

    # Delete user
    result = await user.delete_user(user_id, test_db)
    
    assert result is not None
    assert result.id == user_id
    
    # Verify user is deleted - should raise NoResultFound exception
    from sqlalchemy.exc import NoResultFound
    with pytest.raises(NoResultFound):
        await user.get_user(user_id, test_db)


@pytest.mark.asyncio
async def test_get_users_with_pagination(test_db):
    """Test getting users with pagination."""
    # Create multiple test users
    for i in range(5):
        test_user = User(
            first_name=f"User{i}",
            last_name=f"Last{i}",
            email=f"user{i}@example.com",
            password="hashed_password"
        )
        test_db.add(test_user)
    test_db.commit()

    # Get users with pagination
    filter_pagination = FilterPagination(page=1, limit=3)
    result = await user.get_users(test_db, filter_pagination)
    
    assert result is not None
    assert len(result.users) == 3
    assert result.pagination.page == 1
    assert result.pagination.limit == 3
    assert result.total == 5
    assert result.pages == 2  # 5 users with limit 3 = 2 pages


@pytest.mark.asyncio
async def test_get_users_paginated(test_db):
    """Test getting users with paginated method."""
    # Create multiple test users
    for i in range(10):
        test_user = User(
            first_name=f"TestUser{i}",
            last_name=f"TestLast{i}",
            email=f"testuser{i}@example.com",
            password="hashed_password"
        )
        test_db.add(test_user)
    test_db.commit()

    # Get first page
    result = await user.get_users_paginated(test_db, page=1, limit=5)
    
    assert result is not None
    assert len(result.data) == 5
    assert result.pagination.page == 1
    assert result.pagination.limit == 5
    assert result.pagination.total == 10
