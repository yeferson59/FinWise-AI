import pytest
from unittest.mock import Mock, patch


@pytest.fixture(scope="function", autouse=True)
def clear_settings_cache():
    """Clear lru_cache for settings functions before each test"""
    from app.config import get_settings, get_models

    get_settings.cache_clear()
    get_models.cache_clear()

    yield

    get_settings.cache_clear()
    get_models.cache_clear()


@pytest.fixture(scope="function")
def mock_openrouter_provider():
    """Mock OpenRouterProvider to avoid actual API calls"""
    with patch("app.core.llm.OpenRouterProvider") as mock_provider:
        mock_instance = Mock()
        mock_provider.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_agent():
    """Mock the AI agent to avoid actual API calls"""
    with patch("app.core.llm.get_agent") as mock_get_agent:
        mock_agent_instance = Mock()
        mock_get_agent.return_value = mock_agent_instance
        yield mock_agent_instance


@pytest.fixture(scope="function")
def mock_react_agent():
    """Mock the ReAct agent to avoid actual API calls"""
    with patch("app.core.llm.get_react_agent") as mock_get_react_agent:
        mock_react_agent_instance = Mock()
        mock_get_react_agent.return_value = mock_react_agent_instance
        yield mock_react_agent_instance


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    from app.db.base import engine
    from sqlmodel import Session, SQLModel

    # Create all tables
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Cleanup - drop all tables
    SQLModel.metadata.drop_all(engine)
