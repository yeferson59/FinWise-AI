from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from app.config import get_settings, get_models
from app.db.session import SessionDep
from app.models.user import User
from sqlmodel import select
from functools import lru_cache


@dataclass
class AgentDeps:
    session: SessionDep


@lru_cache
def get_model():
    """Get or create the OpenAI chat model instance"""
    settings = get_settings()
    models = get_models()

    return OpenAIChatModel(
        models[0],
        provider=OpenRouterProvider(api_key=settings.openai_api_key),
    )


@lru_cache
def get_agent():
    """Get or create the base agent instance"""
    settings = get_settings()
    model = get_model()

    return Agent(
        model=model,
        model_settings={"temperature": settings.temperature, "top_p": settings.top_p},
    )


@lru_cache
def get_react_agent():
    """Get or create the ReAct agent instance"""
    settings = get_settings()
    model = get_model()

    react_agent_instance = Agent(
        model=model,
        deps_type=AgentDeps,
        model_settings={"temperature": settings.temperature, "top_p": settings.top_p},
        system_prompt="""Eres un agente ReAct que puede usar herramientas para responder preguntas.

    Debes seguir este patrón:
    1. RAZONA sobre qué necesitas hacer
    2. ACTÚA usando las herramientas disponibles
    3. OBSERVA los resultados
    4. Repite si es necesario

    Piensa paso a paso antes de usar cada herramienta.""",
    )

    @react_agent_instance.tool
    async def get_users_db(ctx: RunContext[AgentDeps]) -> list[User]:
        """
        Utilices esta herramienta cuando necesites los usuarios dentro de la base de datos
        retorna una lista de usuarios registrados en la aplicación
        """
        users = ctx.deps.session.exec(select(User)).all()
        return list(users)

    return react_agent_instance
