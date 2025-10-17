from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from app.config import get_settings, get_models
from functools import lru_cache


@lru_cache
def get_model():
    """Get or create the OpenAI chat model instance"""
    settings = get_settings()
    models = get_models()

    return OpenAIChatModel(
        models[0],
        provider=OpenRouterProvider(api_key=settings.openai_api_key),
    )
