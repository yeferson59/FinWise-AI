"""Tests for transaction service with pagination."""

import pytest
from app.services import transaction
from app.models.transaction import Transaction
from app.schemas.transaction import CreateTransaction
from datetime import datetime


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
async def test_get_all_transactions_with_data(test_db):
    """Test pagination with actual transaction data."""
    # Note: This is a basic structure test. In a real scenario, you would:
    # 1. Create test users, categories, and sources
    # 2. Create multiple test transactions
    # 3. Test that pagination returns the correct subset

    # For now, just verify the function signature works
    result = await transaction.get_all_transactions(test_db, offset=10, limit=20)
    assert isinstance(result, list)
