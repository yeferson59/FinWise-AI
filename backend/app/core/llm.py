from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from app.config import get_settings, get_models
from app.db.session import SessionDep
from app.models.user import User
from sqlmodel import select

settings = get_settings()
models = get_models()

model = OpenAIChatModel(
    models[0],
    provider=OpenRouterProvider(api_key=settings.openai_api_key),
)

agent = Agent(
    model=model,
    model_settings={"temperature": settings.temperature, "top_p": settings.top_p},
)


@dataclass
class AgentDeps:
    session: SessionDep


react_agent = Agent(
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


@react_agent.tool
async def get_users_db(ctx: RunContext[AgentDeps]) -> list[User]:
    """
    Utilices esta herramienta cuando necesites los usuarios dentro de la base de datos
    retorna una lista de usuarios registrados en la aplicación
    """
    users = ctx.deps.session.exec(select(User)).all()
    return list(users)
