"""Tests for the dependencies module, specifically category initialization."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.dependencies import init_categories, get_default_categories
from app.models.category import Category


def test_get_default_categories():
    """Test that get_default_categories returns a list of Category instances."""
    categories = get_default_categories()
    
    assert isinstance(categories, list)
    assert len(categories) > 0
    
    # Check that all items are Category instances
    for category in categories:
        assert isinstance(category, Category)
        assert category.is_default is True
        assert category.user_id is None
        assert category.name
        assert category.description


def test_get_default_categories_has_expected_categories():
    """Test that get_default_categories includes expected category names."""
    categories = get_default_categories()
    category_names = {cat.name for cat in categories}
    
    # Check for some expected categories
    expected_categories = {
        "Salary", "Groceries", "Rent", "Utilities",
        "Entertainment", "Healthcare", "Uncategorized"
    }
    
    assert expected_categories.issubset(category_names)


def test_get_default_categories_all_unique_names():
    """Test that all default categories have unique names."""
    categories = get_default_categories()
    names = [cat.name for cat in categories]
    
    # Check that there are no duplicate names
    assert len(names) == len(set(names))


@patch('app.dependencies.Session')
def test_init_categories_first_run(mock_session_class):
    """Test init_categories when no categories exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    
    # Mock that no categories exist
    mock_session.exec.return_value.all.return_value = []
    
    # Call the function
    init_categories()
    
    # Verify that categories were added
    assert mock_session.add_all.called
    assert mock_session.commit.called
    
    # Verify the number of categories added
    call_args = mock_session.add_all.call_args[0][0]
    assert len(call_args) > 0


@patch('app.dependencies.Session')
def test_init_categories_idempotent(mock_session_class):
    """Test that init_categories is idempotent when all categories exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    
    # Mock that all categories already exist
    default_categories = get_default_categories()
    existing_names = [cat.name for cat in default_categories]
    mock_session.exec.return_value.all.return_value = existing_names
    
    # Call the function
    init_categories()
    
    # Verify that no categories were added
    assert not mock_session.add_all.called
    assert not mock_session.commit.called


@patch('app.dependencies.Session')
def test_init_categories_partial_existing(mock_session_class):
    """Test init_categories when some categories already exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    
    # Mock that only some categories exist
    mock_session.exec.return_value.all.return_value = ["Salary", "Groceries"]
    
    # Call the function
    init_categories()
    
    # Verify that only missing categories were added
    assert mock_session.add_all.called
    assert mock_session.commit.called
    
    # Get the categories that were added
    call_args = mock_session.add_all.call_args[0][0]
    added_names = {cat.name for cat in call_args}
    
    # Verify that "Salary" and "Groceries" are not in the added list
    assert "Salary" not in added_names
    assert "Groceries" not in added_names
    
    # Verify that some other categories were added
    assert len(call_args) > 0


@patch('app.dependencies.Session')
def test_init_categories_handles_exceptions(mock_session_class):
    """Test that init_categories handles database exceptions properly."""
    # Setup mock to raise an exception
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    mock_session.exec.side_effect = Exception("Database error")
    
    # Verify that exception is raised
    with pytest.raises(Exception) as exc_info:
        init_categories()
    
    assert "Database error" in str(exc_info.value)


@patch('app.dependencies.Session')
@patch('app.dependencies.logger')
def test_init_categories_logs_correctly(mock_logger, mock_session_class):
    """Test that init_categories logs appropriate messages."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session
    
    # Mock that some categories exist
    mock_session.exec.return_value.all.return_value = ["Salary"]
    
    # Call the function
    init_categories()
    
    # Verify that info log was called
    assert mock_logger.info.called
