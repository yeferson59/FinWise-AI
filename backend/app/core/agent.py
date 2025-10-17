from pydantic_ai import Agent, RunContext
from app.models.user import User
from sqlmodel import select
from functools import lru_cache
from .llm import get_model
from dataclasses import dataclass
from app.db.session import SessionDep
from app.config import get_settings

settings = get_settings()
model = get_model()


@dataclass
class AgentDeps:
    session: SessionDep


@lru_cache
def get_agent():
    """Get or create the base agent instance"""

    return Agent(
        model=model,
        model_settings={"temperature": settings.temperature, "top_p": settings.top_p},
    )


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
