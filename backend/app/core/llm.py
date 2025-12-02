from functools import lru_cache

from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.config import get_models, get_settings


@lru_cache
def get_model():
    """Get or create the OpenAI chat model instance"""
    settings = get_settings()
    models = get_models()

    return OpenRouterModel(
        models[0],
        provider=OpenRouterProvider(
            api_key=settings.openai_api_key,
        ),
    )
