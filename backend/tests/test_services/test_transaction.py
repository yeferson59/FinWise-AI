"""Tests for transaction service with pagination and filters."""

import pytest
from app.services import transaction
from app.models.transaction import Transaction, Source
from app.models.user import User
from app.models.category import Category
from app.schemas.transaction import TransactionFilters
from datetime import datetime, timezone, timedelta


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_category(test_db):
    """Create a test category."""
    category = Category(name="Test Category", description="Test description")
    test_db.add(category)
    test_db.commit()
    test_db.refresh(category)
    return category


@pytest.fixture
def test_source(test_db):
    """Create a test source."""
    source = Source(name="Test Source")
    test_db.add(source)
    test_db.commit()
    test_db.refresh(source)
    return source


@pytest.mark.asyncio
async def test_get_all_transactions_default_pagination(test_db):
    """Test that get_all_transactions works with default pagination."""
    result = await transaction.get_all_transactions(test_db)
    assert isinstance(result, list)
    # With empty database, should return empty list
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_all_transactions_custom_pagination(test_db):
    """Test that get_all_transactions respects custom offset and limit."""
    result = await transaction.get_all_transactions(test_db, offset=0, limit=50)
    assert isinstance(result, list)
    assert len(result) <= 50


@pytest.mark.asyncio
async def test_filter_by_user_id(test_db, test_user, test_category, test_source):
    """Test filtering transactions by user_id."""
    # Create transactions for test user
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Transaction 1",
        amount=100.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    test_db.add(trans1)
    test_db.commit()

    # Create another user and transaction
    user2 = User(
        first_name="User",
        last_name="Two",
        email="user2@example.com",
        password="hashed_password",
    )
    test_db.add(user2)
    test_db.commit()
    test_db.refresh(user2)

    trans2 = Transaction(
        user_id=user2.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Transaction 2",
        amount=200.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    test_db.add(trans2)
    test_db.commit()

    # Test filter by first user
    filters = TransactionFilters(user_id=test_user.id)
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 1
    assert result[0].user_id == test_user.id
    assert result[0].description == "Transaction 1"


@pytest.mark.asyncio
async def test_filter_by_category_id(test_db, test_user, test_category, test_source):
    """Test filtering transactions by category_id."""
    # Create category 2
    category2 = Category(name="Category 2", description="Second category")
    test_db.add(category2)
    test_db.commit()
    test_db.refresh(category2)

    # Create transactions with different categories
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Transaction Cat 1",
        amount=100.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=category2.id,
        source_id=test_source.id,
        description="Transaction Cat 2",
        amount=200.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    test_db.add_all([trans1, trans2])
    test_db.commit()

    # Test filter by category
    filters = TransactionFilters(category_id=test_category.id)
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 1
    assert result[0].category_id == test_category.id


@pytest.mark.asyncio
async def test_filter_by_date_range(test_db, test_user, test_category, test_source):
    """Test filtering transactions by date range."""
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    # Create transactions with different dates
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Last week",
        amount=100.0,
        date=last_week,
        state="completed",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Yesterday",
        amount=200.0,
        date=yesterday,
        state="completed",
    )
    trans3 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Today",
        amount=300.0,
        date=now,
        state="completed",
    )
    test_db.add_all([trans1, trans2, trans3])
    test_db.commit()

    # Test filter by date range (last 3 days)
    filters = TransactionFilters(
        start_date=now - timedelta(days=3), end_date=now + timedelta(hours=1)
    )
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 2
    assert any(t.description == "Yesterday" for t in result)
    assert any(t.description == "Today" for t in result)
    assert not any(t.description == "Last week" for t in result)


@pytest.mark.asyncio
async def test_filter_by_amount_range(test_db, test_user, test_category, test_source):
    """Test filtering transactions by amount range."""
    # Create transactions with different amounts
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Small",
        amount=50.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Medium",
        amount=150.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    trans3 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Large",
        amount=500.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    test_db.add_all([trans1, trans2, trans3])
    test_db.commit()

    # Test filter by amount range (100-200)
    filters = TransactionFilters(min_amount=100.0, max_amount=200.0)
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 1
    assert result[0].description == "Medium"
    assert result[0].amount == 150.0


@pytest.mark.asyncio
async def test_filter_by_state(test_db, test_user, test_category, test_source):
    """Test filtering transactions by state."""
    # Create transactions with different states
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Pending",
        amount=100.0,
        date=datetime.now(timezone.utc),
        state="pending",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Completed",
        amount=200.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    test_db.add_all([trans1, trans2])
    test_db.commit()

    # Test filter by state
    filters = TransactionFilters(state="completed")
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 1
    assert result[0].state == "completed"
    assert result[0].description == "Completed"


@pytest.mark.asyncio
async def test_combined_filters(test_db, test_user, test_category, test_source):
    """Test combining multiple filters."""
    now = datetime.now(timezone.utc)

    # Create multiple transactions
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Match",
        amount=150.0,
        date=now,
        state="completed",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Wrong state",
        amount=150.0,
        date=now,
        state="pending",
    )
    trans3 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Wrong amount",
        amount=50.0,
        date=now,
        state="completed",
    )
    test_db.add_all([trans1, trans2, trans3])
    test_db.commit()

    # Test combined filters
    filters = TransactionFilters(
        user_id=test_user.id,
        category_id=test_category.id,
        state="completed",
        min_amount=100.0,
    )
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 1
    assert result[0].description == "Match"


@pytest.mark.asyncio
async def test_sort_by_amount_ascending(test_db, test_user, test_category, test_source):
    """Test sorting transactions by amount in ascending order."""
    # Create transactions with different amounts
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Large",
        amount=500.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Small",
        amount=50.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    trans3 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Medium",
        amount=150.0,
        date=datetime.now(timezone.utc),
        state="completed",
    )
    test_db.add_all([trans1, trans2, trans3])
    test_db.commit()

    # Test sort by amount ascending
    filters = TransactionFilters(sort_by="amount", sort_desc=False)
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 3
    assert result[0].description == "Small"
    assert result[1].description == "Medium"
    assert result[2].description == "Large"


@pytest.mark.asyncio
async def test_sort_by_date_descending(test_db, test_user, test_category, test_source):
    """Test sorting transactions by date in descending order (default)."""
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    # Create transactions with different dates
    trans1 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Last week",
        amount=100.0,
        date=last_week,
        state="completed",
    )
    trans2 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Today",
        amount=300.0,
        date=now,
        state="completed",
    )
    trans3 = Transaction(
        user_id=test_user.id,
        category_id=test_category.id,
        source_id=test_source.id,
        description="Yesterday",
        amount=200.0,
        date=yesterday,
        state="completed",
    )
    test_db.add_all([trans1, trans2, trans3])
    test_db.commit()

    # Test sort by date descending (newest first)
    filters = TransactionFilters(sort_by="date", sort_desc=True)
    result = await transaction.get_all_transactions(test_db, filters=filters)

    assert len(result) == 3
    assert result[0].description == "Today"
    assert result[1].description == "Yesterday"
    assert result[2].description == "Last week"
