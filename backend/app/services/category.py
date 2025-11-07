from app.db.session import SessionDep
from app.models.category import Category
from app.schemas.category import CreateCategory, UpdateCategory
from app.utils.crud import CRUDService
from fastapi import UploadFile
from app.services.file import extract_text
from app.core.agent import react_agent, AgentDeps
from app.utils import db

# Initialize CRUD service for Category
_category_crud = CRUDService[Category, CreateCategory, UpdateCategory](Category)


async def get_all_categories(session: SessionDep, offset: int = 0, limit: int = 100):
    """Get all categories with pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns:
        List of Category objects
    """
    return await _category_crud.get_all(session, offset, limit)


async def create_category(session: SessionDep, create_category: CreateCategory):
    return await _category_crud.create(session, create_category)


async def get_category(session: SessionDep, id: int):
    return await _category_crud.get_by_id(session, id)


async def update_category(
    session: SessionDep, id: int, update_category: UpdateCategory
):
    return await _category_crud.update(session, id, update_category)


async def delete_category(session: SessionDep, id: int):
    return await _category_crud.delete(session, id)


async def classification(session: SessionDep, document_type: str, file: UploadFile):
    # Check if categories exist before attempting classification
    # Optimization: Use count query instead of fetching records
    from app.models.category import Category as CategoryModel
    from sqlmodel import select, func
    
    category_count = session.exec(
        select(func.count()).select_from(CategoryModel)
    ).one()
    
    if category_count == 0:
        raise ValueError("No categories found in the database. Please create categories before classifying documents.")

    data = await extract_text(document_type, file)
    deps = AgentDeps(session)

    response = await react_agent.run(
        f"You are an excellent categorizer of information from images and documents. Your task is to classify the provided text into one of the existing categories in the finWise application. The document type is: '{document_type}'. First, retrieve the list of all existing categories from the database using the available tools. Then, analyze the following text extracted from the document or image: '{str(data['raw_text'])}'. Determine which category it best fits into based on its content and the document type. Finally, return exactly the name of the matching category as it is stored in the database, without any additional text, explanation, or formatting.",
        deps=deps,
        output_type=str,
    )

    category_name = response.output.strip()
    if not category_name:
        raise ValueError("Unable to classify the document. The AI agent could not determine an appropriate category.")

    # Verify the returned category actually exists
    category = db.get_entity_by_field(Category, "name", category_name, session)
    if not category:
        raise ValueError(f"The classified category '{category_name}' does not exist in the database.")

    return category


async def classify_text(session: SessionDep, text: str, document_type: str = "general") -> Category:
    """
    Classify extracted text directly into a category.

    Performance Optimization: Uses efficient count query instead of fetching categories.

    Args:
        session: Database session
        text: The text to classify
        document_type: Type of document for context

    Returns:
        Category object

    Raises:
        ValueError: If no categories exist or classification fails
    """
    # Check if categories exist before attempting classification
    # Optimization: Use count query instead of fetching records
    from app.models.category import Category as CategoryModel
    from sqlmodel import select, func
    
    category_count = session.exec(
        select(func.count()).select_from(CategoryModel)
    ).one()
    
    if category_count == 0:
        raise ValueError("No categories found in the database. Please create categories before classifying documents.")

    deps = AgentDeps(session)

    response = await react_agent.run(
        f"You are an excellent categorizer of information from images and documents. Your task is to classify the provided text into one of the existing categories in the finWise application. The document type is: '{document_type}'. First, retrieve the list of all existing categories from the database using the available tools. Then, analyze the following text extracted from the document or image: '{str(text)}'. Determine which category it best fits into based on its content and the document type. Finally, return exactly the name of the matching category as it is stored in the database, without any additional text, explanation, or formatting.",
        deps=deps,
        output_type=str,
    )

    category_name = response.output.strip()
    if not category_name:
        raise ValueError("Unable to classify the document. The AI agent could not determine an appropriate category.")

    # Verify the returned category actually exists
    category = db.get_entity_by_field(Category, "name", category_name, session)
    if not category:
        raise ValueError(f"The classified category '{category_name}' does not exist in the database.")

    return category
