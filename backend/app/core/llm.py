from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from app.config import get_settings

settings = get_settings()

model = OpenAIChatModel(
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    provider=OpenRouterProvider(api_key=settings.openai_api_key),
)

agent = Agent(model=model, model_settings={"temperature": 0.2, "top_p": 0.3})
