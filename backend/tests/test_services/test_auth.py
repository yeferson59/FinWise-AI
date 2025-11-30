"""Tests for auth service."""

import pytest
from app.services import auth
from app.models.user import User
from app.models.auth import Session
from app.schemas.auth import Login, Register


@pytest.mark.asyncio
async def test_register_success(test_db):
    """Test successful user registration."""
    register_data = Register(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="SecurePass123!@",
        confirm_password="SecurePass123!@",
        terms_and_conditions=True,
    )

    result = await auth.register(test_db, register_data)

    assert result == "Register successfully"

    # Verify user was created
    from app.services import user as user_service

    created_user = await user_service.get_user_by_email("john.doe@example.com", test_db)
    assert created_user is not None
    assert created_user.email == "john.doe@example.com"


@pytest.mark.asyncio
async def test_register_password_mismatch(test_db):
    """Test registration with password mismatch."""
    register_data = Register(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="SecurePass123!@",
        confirm_password="DifferentPass123!@",
        terms_and_conditions=True,
    )

    result = await auth.register(test_db, register_data)

    assert result == "No successfully"


@pytest.mark.asyncio
async def test_register_terms_not_accepted(test_db):
    """Test registration without accepting terms."""
    register_data = Register(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="SecurePass123!@",
        confirm_password="SecurePass123!@",
        terms_and_conditions=False,
    )

    result = await auth.register(test_db, register_data)

    assert result == "Terms and conditions must be accepted"


@pytest.mark.asyncio
async def test_login_success(test_db):
    """Test successful login."""
    # First create a user
    from app.services import user as user_service
    from app.schemas.user import CreateUser

    create_data = CreateUser(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        password="SecurePass123!@",
    )
    await user_service.create_user(create_data, test_db)

    # Now try to login
    login_data = Login(email="jane.smith@example.com", password="SecurePass123!@")

    result = await auth.login(test_db, login_data)

    assert result.success is True
    assert result.access_token is not None
    assert result.user.email == "jane.smith@example.com"
    assert result.user.id is not None


@pytest.mark.asyncio
async def test_login_wrong_password(test_db):
    """Test login with wrong password."""
    from app.core.exceptions import InvalidCredentialsError

    # First create a user
    from app.services import user as user_service
    from app.schemas.user import CreateUser

    create_data = CreateUser(
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com",
        password="SecurePass123!@",
    )
    await user_service.create_user(create_data, test_db)

    # Try to login with wrong password
    login_data = Login(email="bob.johnson@example.com", password="WrongPassword123!@")

    with pytest.raises(InvalidCredentialsError):
        await auth.login(test_db, login_data)


@pytest.mark.asyncio
async def test_login_user_not_found(test_db):
    """Test login with non-existent user."""
    from app.core.exceptions import InvalidCredentialsError

    login_data = Login(email="nonexistent@example.com", password="SecurePass123!@")

    with pytest.raises(InvalidCredentialsError):
        await auth.login(test_db, login_data)


@pytest.mark.asyncio
async def test_logout(test_db):
    """Test logout functionality."""
    # Create a test session
    test_user = User(
        first_name="Alice",
        last_name="Brown",
        email="alice.brown@example.com",
        password="hashed_password",
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)

    from datetime import datetime, timezone, timedelta

    test_session = Session(
        user_id=test_user.id,
        token="test_token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    test_db.add(test_session)
    test_db.commit()
    test_db.refresh(test_session)

    # Use real session instance
    current_session = Session(
        id=test_session.id,
        user_id=test_session.user_id,
        token=test_session.token,
        expires_at=test_session.expires_at,
    )

    # Logout - the function doesn't return a value, it just deletes the session
    await auth.logout(test_db, current_session)

    # Verify session was deleted
    from sqlmodel import select

    deleted_session = test_db.exec(
        select(Session).where(Session.id == test_session.id)
    ).first()
    assert deleted_session is None
