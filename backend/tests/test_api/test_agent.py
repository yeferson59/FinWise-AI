from app.config import get_models, get_settings
from tests.test_main import client


def test_settings_loaded_from_env_test():
    """Test that settings are loaded correctly from .env.test"""
    settings = get_settings()

    # Verify environment is set (value may vary based on .env.test)
    assert settings.environment is not None
    assert isinstance(settings.environment, str)

    # Verify API key is loaded (should not be empty in .env.test)
    assert settings.openai_api_key != ""
    assert len(settings.openai_api_key) > 0

    # Verify database URL is set
    assert settings.database_url != ""

    # Verify security settings are present
    assert settings.secret_key != ""
    assert settings.algorithm != ""

    # Verify models string is not empty
    assert settings.models != ""


def test_get_models_from_env_test():
    """Test that get_models returns a valid list of models from .env.test"""
    models = get_models()

    # Should return a list
    assert isinstance(models, list)

    # Should have at least one model
    assert len(models) > 0

    # First model should not be empty
    assert models[0] != ""
    assert len(models[0]) > 0


def test_models_are_properly_parsed():
    """Test that models string is correctly split into list"""
    settings = get_settings()
    models = get_models()

    # Number of models should match number of commas + 1 in settings
    expected_count = settings.models.count(",") + 1
    assert len(models) == expected_count

    # Each model should be a non-empty string
    for model in models:
        assert isinstance(model, str)
        assert len(model.strip()) > 0


def test_settings_cache_is_working():
    """Test that lru_cache is working for get_settings"""
    settings1 = get_settings()
    settings2 = get_settings()

    # Should return the same instance (cached)
    assert settings1 is settings2


def test_models_cache_is_working():
    """Test that lru_cache is working for get_models"""
    models1 = get_models()
    models2 = get_models()

    # Should return the same instance (cached)
    assert models1 is models2


# Uncomment when you have a client fixture set up
def test_agent_api():
    """Test agent API endpoint"""
    res = client.post("/api/v1/agents", json={"message": "Hello, who are you?"})
    assert res.status_code == 200
    assert res.json() != ""
