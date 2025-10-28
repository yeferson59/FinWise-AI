"""
Tests for React Agent tools functionality.

This test suite verifies that all the tools added to the React Agent
work correctly and provide accurate data from the database.
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction, Source
from app.core.agent import (
    AgentDeps,
    get_users_count,
    get_user_by_id,
    get_user_by_email,
    get_all_users,
    get_all_transactions,
    get_transactions_by_user,
    get_transactions_by_category,
    get_transaction_by_id,
    count_transactions,
    count_user_transactions,
    calculate_total_amount,
    get_transactions_by_date_range,
    calculate_amount_by_date_range,
    get_spending_by_category,
    get_all_categories,
    get_category_by_name,
)


@pytest.fixture
def sample_users(test_db: Session):
    """Create sample users for testing"""
    users = [
        User(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="hashed_password_1",
            is_active=True,
        ),
        User(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            password="hashed_password_2",
            is_active=True,
        ),
        User(
            first_name="Bob",
            last_name="Johnson",
            email="bob@example.com",
            password="hashed_password_3",
            is_active=False,
        ),
    ]
    for user in users:
        test_db.add(user)
    test_db.commit()
    for user in users:
        test_db.refresh(user)
    return users


@pytest.fixture
def sample_categories(test_db: Session, sample_users):
    """Create sample categories for testing"""
    categories = [
        Category(name="Food", description="Food and groceries", is_default=True),
        Category(name="Transport", description="Transportation costs", is_default=True),
        Category(
            name="Entertainment",
            description="Entertainment expenses",
            is_default=False,
            user_id=sample_users[0].id,
        ),
    ]
    for category in categories:
        test_db.add(category)
    test_db.commit()
    for category in categories:
        test_db.refresh(category)
    return categories


@pytest.fixture
def sample_source(test_db: Session):
    """Create a sample transaction source"""
    source = Source(name="Cash")
    test_db.add(source)
    test_db.commit()
    test_db.refresh(source)
    return source


@pytest.fixture
def sample_transactions(
    test_db: Session, sample_users, sample_categories, sample_source
):
    """Create sample transactions for testing"""
    base_date = datetime(2024, 1, 1)
    transactions = [
        # User 1 transactions
        Transaction(
            user_id=sample_users[0].id,
            category_id=sample_categories[0].id,  # Food
            source_id=sample_source.id,
            description="Grocery shopping",
            amount=150.50,
            date=base_date,
            state="completed",
        ),
        Transaction(
            user_id=sample_users[0].id,
            category_id=sample_categories[1].id,  # Transport
            source_id=sample_source.id,
            description="Gas",
            amount=45.00,
            date=base_date + timedelta(days=5),
            state="completed",
        ),
        Transaction(
            user_id=sample_users[0].id,
            category_id=sample_categories[2].id,  # Entertainment
            source_id=sample_source.id,
            description="Movie tickets",
            amount=30.00,
            date=base_date + timedelta(days=10),
            state="completed",
        ),
        # User 2 transactions
        Transaction(
            user_id=sample_users[1].id,
            category_id=sample_categories[0].id,  # Food
            source_id=sample_source.id,
            description="Restaurant",
            amount=75.00,
            date=base_date + timedelta(days=3),
            state="completed",
        ),
        Transaction(
            user_id=sample_users[1].id,
            category_id=sample_categories[1].id,  # Transport
            source_id=sample_source.id,
            description="Uber ride",
            amount=25.00,
            date=base_date + timedelta(days=15),
            state="pending",
        ),
    ]
    for transaction in transactions:
        test_db.add(transaction)
    test_db.commit()
    for transaction in transactions:
        test_db.refresh(transaction)
    return transactions


@pytest.fixture
def agent_deps(test_db: Session):
    """Create AgentDeps for testing"""
    return AgentDeps(session=test_db)


@pytest.fixture
def mock_context(agent_deps):
    """Create a mock RunContext for testing"""

    class MockContext:
        def __init__(self, deps):
            self.deps = deps

    return MockContext(agent_deps)


# ==================== USER MANAGEMENT TOOL TESTS ====================


def test_get_users_count(mock_context, sample_users):
    """Test getting total user count"""
    count = get_users_count(mock_context)
    assert count == 3
    assert isinstance(count, int)


def test_get_user_by_id(mock_context, sample_users):
    """Test getting user by ID"""
    user = get_user_by_id(mock_context, sample_users[0].id)
    assert user is not None
    assert user.email == "john@example.com"
    assert user.first_name == "John"


def test_get_user_by_id_not_found(mock_context):
    """Test getting non-existent user returns None"""
    user = get_user_by_id(mock_context, 9999)
    assert user is None


def test_get_user_by_email(mock_context, sample_users):
    """Test getting user by email"""
    user = get_user_by_email(mock_context, "jane@example.com")
    assert user is not None
    assert user.first_name == "Jane"
    assert user.last_name == "Smith"


def test_get_user_by_email_not_found(mock_context):
    """Test getting user by non-existent email"""
    user = get_user_by_email(mock_context, "nonexistent@example.com")
    assert user is None


def test_get_all_users(mock_context, sample_users):
    """Test getting all users with pagination"""
    users = get_all_users(mock_context, offset=0, limit=10)
    assert len(users) == 3
    assert all(isinstance(user, User) for user in users)


def test_get_all_users_pagination(mock_context, sample_users):
    """Test user pagination"""
    # Get first user
    users_page1 = get_all_users(mock_context, offset=0, limit=1)
    assert len(users_page1) == 1

    # Get second user
    users_page2 = get_all_users(mock_context, offset=1, limit=1)
    assert len(users_page2) == 1

    # Ensure they're different users
    assert users_page1[0].id != users_page2[0].id


# ==================== CATEGORY TOOL TESTS ====================


def test_get_all_categories(mock_context, sample_categories):
    """Test getting all categories"""
    categories = get_all_categories(mock_context, offset=0, limit=10)
    assert len(categories) == 3
    assert all(isinstance(cat, Category) for cat in categories)


def test_get_category_by_name(mock_context, sample_categories):
    """Test getting category by name"""
    category = get_category_by_name(mock_context, "Food")
    assert category is not None
    assert category.name == "Food"
    assert category.is_default is True


def test_get_category_by_name_not_found(mock_context):
    """Test getting non-existent category"""
    category = get_category_by_name(mock_context, "NonExistent")
    assert category is None


# ==================== TRANSACTION TOOL TESTS ====================


def test_get_all_transactions(mock_context, sample_transactions):
    """Test getting all transactions"""
    transactions = get_all_transactions(mock_context, offset=0, limit=10)
    assert len(transactions) == 5
    assert all(isinstance(t, Transaction) for t in transactions)


def test_get_transactions_by_user(mock_context, sample_transactions, sample_users):
    """Test getting transactions for a specific user"""
    user1_transactions = get_transactions_by_user(
        mock_context, sample_users[0].id, offset=0, limit=10
    )
    assert len(user1_transactions) == 3
    assert all(t.user_id == sample_users[0].id for t in user1_transactions)


def test_get_transactions_by_category(
    mock_context, sample_transactions, sample_categories
):
    """Test getting transactions for a specific category"""
    food_transactions = get_transactions_by_category(
        mock_context, sample_categories[0].id, offset=0, limit=10
    )
    assert len(food_transactions) == 2
    assert all(t.category_id == sample_categories[0].id for t in food_transactions)


def test_get_transaction_by_id(mock_context, sample_transactions):
    """Test getting a specific transaction by ID"""
    transaction = get_transaction_by_id(mock_context, sample_transactions[0].id)
    assert transaction is not None
    assert transaction.description == "Grocery shopping"
    assert transaction.amount == 150.50


def test_get_transaction_by_id_not_found(mock_context):
    """Test getting non-existent transaction"""
    transaction = get_transaction_by_id(mock_context, "non-existent-uuid")
    assert transaction is None


def test_count_transactions(mock_context, sample_transactions):
    """Test counting total transactions"""
    count = count_transactions(mock_context)
    assert count == 5
    assert isinstance(count, int)


def test_count_user_transactions(mock_context, sample_transactions, sample_users):
    """Test counting transactions for a specific user"""
    count = count_user_transactions(mock_context, sample_users[0].id)
    assert count == 3

    count2 = count_user_transactions(mock_context, sample_users[1].id)
    assert count2 == 2


# ==================== FINANCIAL ANALYSIS TOOL TESTS ====================


def test_calculate_total_amount_all(mock_context, sample_transactions):
    """Test calculating total amount of all transactions"""
    total = calculate_total_amount(mock_context)
    expected = 150.50 + 45.00 + 30.00 + 75.00 + 25.00
    assert abs(total - expected) < 0.01  # Allow for floating point precision


def test_calculate_total_amount_by_user(
    mock_context, sample_transactions, sample_users
):
    """Test calculating total for a specific user"""
    total = calculate_total_amount(mock_context, user_id=sample_users[0].id)
    expected = 150.50 + 45.00 + 30.00
    assert abs(total - expected) < 0.01


def test_calculate_total_amount_by_category(
    mock_context, sample_transactions, sample_categories
):
    """Test calculating total for a specific category"""
    total = calculate_total_amount(mock_context, category_id=sample_categories[0].id)
    expected = 150.50 + 75.00  # Food category
    assert abs(total - expected) < 0.01


def test_calculate_total_amount_by_user_and_category(
    mock_context, sample_transactions, sample_users, sample_categories
):
    """Test calculating total for user and category combination"""
    total = calculate_total_amount(
        mock_context, user_id=sample_users[0].id, category_id=sample_categories[0].id
    )
    expected = 150.50  # User 1, Food category
    assert abs(total - expected) < 0.01


def test_get_transactions_by_date_range(
    mock_context, sample_transactions, sample_users
):
    """Test getting transactions within a date range"""
    start = "2024-01-01"
    end = "2024-01-10"

    transactions = get_transactions_by_date_range(
        mock_context, start, end, user_id=sample_users[0].id, offset=0, limit=10
    )

    # User 1 has 2 transactions in this range (Jan 1 and Jan 6)
    assert len(transactions) == 2


def test_get_transactions_by_date_range_invalid_dates(mock_context):
    """Test date range with invalid dates"""
    transactions = get_transactions_by_date_range(
        mock_context, "invalid-date", "2024-01-31", offset=0, limit=10
    )
    assert len(transactions) == 0


def test_calculate_amount_by_date_range(
    mock_context, sample_transactions, sample_users
):
    """Test calculating amount for a date range"""
    start = "2024-01-01"
    end = "2024-01-10"

    total = calculate_amount_by_date_range(
        mock_context, start, end, user_id=sample_users[0].id
    )

    expected = 150.50 + 45.00  # Grocery + Gas
    assert abs(total - expected) < 0.01


def test_calculate_amount_by_date_range_invalid(mock_context):
    """Test calculating amount with invalid date range"""
    total = calculate_amount_by_date_range(mock_context, "invalid-date", "2024-01-31")
    assert total == 0.0


def test_get_spending_by_category(
    mock_context, sample_transactions, sample_users, sample_categories
):
    """Test getting spending breakdown by category"""
    spending = get_spending_by_category(mock_context, sample_users[0].id, limit=10)

    assert len(spending) == 3
    assert isinstance(spending, list)
    assert all(isinstance(item, dict) for item in spending)

    # Check structure
    for item in spending:
        assert "category_id" in item
        assert "category_name" in item
        assert "total_amount" in item

    # First item should be Food (highest amount)
    assert spending[0]["category_name"] == "Food"
    assert abs(spending[0]["total_amount"] - 150.50) < 0.01


def test_get_spending_by_category_empty_user(mock_context, sample_users):
    """Test spending analysis for user with no transactions"""
    spending = get_spending_by_category(mock_context, sample_users[2].id, limit=10)
    assert len(spending) == 0


def test_get_spending_by_category_limit(
    mock_context, sample_transactions, sample_users
):
    """Test spending analysis respects limit"""
    spending = get_spending_by_category(mock_context, sample_users[0].id, limit=2)
    assert len(spending) <= 2
