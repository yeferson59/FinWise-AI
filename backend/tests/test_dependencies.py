"""Tests for the dependencies module, specifically category and source initialization."""

import pytest
from unittest.mock import patch, MagicMock
from app.dependencies import (
    init_categories,
    get_default_categories,
    init_sources,
    get_default_sources,
)
from app.models.category import Category
from app.models.transaction import Source


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
        "Salary",
        "Groceries",
        "Rent",
        "Utilities",
        "Entertainment",
        "Healthcare",
        "Uncategorized",
    }

    assert expected_categories.issubset(category_names)


def test_get_default_categories_all_unique_names():
    """Test that all default categories have unique names."""
    categories = get_default_categories()
    names = [cat.name for cat in categories]

    # Check that there are no duplicate names
    assert len(names) == len(set(names))


@patch("app.dependencies.Session")
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


@patch("app.dependencies.Session")
def test_init_categories_idempotent(mock_session_class):
    """Test that init_categories is idempotent when all categories exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session

    # Mock that all default categories already exist in the database
    # The query returns only the names of existing global categories
    default_categories = get_default_categories()
    all_existing_names = [cat.name for cat in default_categories]
    mock_session.exec.return_value.all.return_value = all_existing_names

    # Call the function
    init_categories()

    # Verify that no new categories were added since all already exist
    assert not mock_session.add_all.called
    assert not mock_session.commit.called


@patch("app.dependencies.Session")
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


@patch("app.dependencies.Session")
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


@patch("app.dependencies.Session")
@patch("app.dependencies.logger")
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


# Tests for default sources
def test_get_default_sources():
    """Test that get_default_sources returns a list of Source instances."""
    sources = get_default_sources()

    assert isinstance(sources, list)
    assert len(sources) > 0

    # Check that all items are Source instances
    for source in sources:
        assert isinstance(source, Source)
        assert source.is_default is True
        assert source.user_id is None
        assert source.name
        assert source.description


def test_get_default_sources_has_expected_sources():
    """Test that get_default_sources includes expected source names."""
    sources = get_default_sources()
    source_names = {src.name for src in sources}

    # Check for some expected sources
    expected_sources = {
        "Bank Account",
        "Credit Card",
        "PayPal",
        "Cash",
        "Cash App",
        "Other",
    }

    assert expected_sources.issubset(source_names)


def test_get_default_sources_all_unique_names():
    """Test that all default sources have unique names."""
    sources = get_default_sources()
    names = [src.name for src in sources]

    # Check that there are no duplicate names
    assert len(names) == len(set(names))


@pytest.mark.asyncio
@patch("app.dependencies.Session")
@patch("app.dependencies.engine")
def test_init_sources_first_run(mock_engine, mock_session_class):
    """Test init_sources when no sources exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session

    # Mock that no sources exist
    mock_session.exec.return_value.all.return_value = []

    # Call the function
    init_sources()

    # Verify that add_all was called with sources
    assert mock_session.add_all.called
    mock_session.commit.assert_called_once()

    # Check that the right number of sources were added
    call_args = mock_session.add_all.call_args[0][0]
    assert len(call_args) == len(get_default_sources())


@pytest.mark.asyncio
@patch("app.dependencies.Session")
@patch("app.dependencies.engine")
def test_init_sources_idempotent(mock_engine, mock_session_class):
    """Test that init_sources is idempotent when all sources exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session

    # Mock that all sources already exist
    default_sources = get_default_sources()
    all_existing_names = [src.name for src in default_sources]
    mock_session.exec.return_value.all.return_value = all_existing_names

    # Call the function
    init_sources()

    # Verify that add_all was not called (no new sources to add)
    assert not mock_session.add_all.called
    assert not mock_session.commit.called


@pytest.mark.asyncio
@patch("app.dependencies.Session")
@patch("app.dependencies.engine")
def test_init_sources_partial_existing(mock_engine, mock_session_class):
    """Test init_sources when some sources already exist."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session

    # Mock that some sources exist
    mock_session.exec.return_value.all.return_value = ["Bank Account", "Cash"]

    # Call the function
    init_sources()

    # Verify that add_all was called with remaining sources
    assert mock_session.add_all.called
    mock_session.commit.assert_called_once()

    # Check that only non-existing sources were added
    call_args = mock_session.add_all.call_args[0][0]
    default_sources = get_default_sources()
    expected_new_sources = len(default_sources) - 2  # Subtract existing ones
    assert len(call_args) == expected_new_sources


@pytest.mark.asyncio
@patch("app.dependencies.Session")
@patch("app.dependencies.engine")
def test_init_sources_handles_exceptions(mock_engine, mock_session_class):
    """Test that init_sources handles database exceptions properly."""
    # Setup mock to raise exception
    mock_session_class.return_value.__enter__.side_effect = Exception("Database error")

    # Call the function and expect it to raise
    with pytest.raises(Exception, match="Database error"):
        init_sources()


@patch("app.dependencies.logger")
def test_init_sources_logs_correctly(mock_logger, mock_session_class):
    """Test that init_sources logs appropriate messages."""
    # Setup mock
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__.return_value = mock_session

    # Mock that some sources exist
    mock_session.exec.return_value.all.return_value = ["Bank Account"]

    # Call the function
    init_sources()

    # Verify that info log was called
    assert mock_logger.info.called
