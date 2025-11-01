"""Tests for category service."""

import pytest
from app.services import category
from app.models.category import Category
from app.schemas.category import CreateCategory, UpdateCategory


@pytest.mark.asyncio
async def test_get_all_categories_default(test_db):
    """Test getting all categories with default pagination."""
    # Create test categories
    category1 = Category(name="Food", description="Food expenses")
    category2 = Category(name="Transport", description="Transport expenses")
    test_db.add(category1)
    test_db.add(category2)
    test_db.commit()

    # Get all categories
    categories = await category.get_all_categories(test_db)
    
    assert len(categories) == 2
    assert any(cat.name == "Food" for cat in categories)
    assert any(cat.name == "Transport" for cat in categories)


@pytest.mark.asyncio
async def test_get_all_categories_with_pagination(test_db):
    """Test getting categories with custom pagination."""
    # Create test categories
    for i in range(5):
        cat = Category(name=f"Category {i}", description=f"Description {i}")
        test_db.add(cat)
    test_db.commit()

    # Get with limit
    categories = await category.get_all_categories(test_db, offset=0, limit=3)
    
    assert len(categories) == 3


@pytest.mark.asyncio
async def test_create_category(test_db):
    """Test creating a new category."""
    create_data = CreateCategory(
        name="Entertainment",
        description="Entertainment expenses"
    )
    
    result = await category.create_category(test_db, create_data)
    
    assert result is not None
    assert result.name == "Entertainment"
    assert result.description == "Entertainment expenses"
    assert result.id is not None


@pytest.mark.asyncio
async def test_get_category_by_id(test_db):
    """Test getting a category by ID."""
    # Create test category
    test_category = Category(name="Healthcare", description="Healthcare expenses")
    test_db.add(test_category)
    test_db.commit()
    test_db.refresh(test_category)

    # Get category by ID
    result = await category.get_category(test_db, test_category.id)
    
    assert result is not None
    assert result.id == test_category.id
    assert result.name == "Healthcare"


@pytest.mark.asyncio
async def test_update_category(test_db):
    """Test updating a category."""
    # Create test category
    test_category = Category(name="Shopping", description="Shopping expenses")
    test_db.add(test_category)
    test_db.commit()
    test_db.refresh(test_category)

    # Update category
    update_data = UpdateCategory(name="Online Shopping", description="Online shopping expenses")
    result = await category.update_category(test_db, test_category.id, update_data)
    
    assert result is not None
    assert result.id == test_category.id
    assert result.name == "Online Shopping"
    assert result.description == "Online shopping expenses"


@pytest.mark.asyncio
async def test_delete_category(test_db):
    """Test deleting a category."""
    # Create test category
    test_category = Category(name="Other", description="Other expenses")
    test_db.add(test_category)
    test_db.commit()
    test_db.refresh(test_category)
    category_id = test_category.id

    # Delete category
    result = await category.delete_category(test_db, category_id)
    
    assert result is not None
    assert result.id == category_id
    
    # Verify it's deleted - should raise NoResultFound exception
    from sqlalchemy.exc import NoResultFound
    with pytest.raises(NoResultFound):
        await category.get_category(test_db, category_id)
