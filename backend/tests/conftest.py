import pytest
from unittest.mock import Mock, patch
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinWise API"
    port: int = 8000
    version: str = "1.0.0"
    environment: str = "testing"
    openai_api_key: str = "test-key-12345"
    prefix_api: str = "/api/v1"
    database_url: str = "sqlite:///:memory:"
    secret_key: str = ""
    algorithm: str = ""
    access_token_expire_minutes: int = 30
    models: str = "gpt-4o-mini"
    top_p: float = 0.3
    temperature: float = 0.2

    model_config = SettingsConfigDict(env_file=".env.test")


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables before any tests run"""
    _ = Settings()


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
