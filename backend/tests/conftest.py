import pytest
import os
from unittest.mock import Mock, patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables before any tests run"""
    # Set required environment variables for testing
    _ = os.environ.setdefault("OPENAI_API_KEY", "test-key-12345")
    _ = os.environ.setdefault("OPENROUTER_API_KEY", "test-key-12345")
    _ = os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    _ = os.environ.setdefault("ALGORITHM", "HS256")
    _ = os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    _ = os.environ.setdefault("MODELS", "gpt-4o-mini")
    _ = os.environ.setdefault("ENVIRONMENT", "testing")

    yield

    pass


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
