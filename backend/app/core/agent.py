from pydantic_ai import Agent, RunContext
from app.models.category import Category
from functools import lru_cache
from app.core.llm import get_model
from dataclasses import dataclass
from app.db.session import SessionDep
from app.config import get_settings
from app.utils import db
from sqlmodel import select

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
def get_all_categories(
    ctx: RunContext[AgentDeps], offset: int = 0, limit: int = 10
) -> list[Category]:
    """
    Obtiene las categorías ya definidas en el proyecto.

    Usa esta herramienta cuando el agente necesite conocer las categorías disponibles
    (por ejemplo, para mostrar opciones al usuario, clasificar elementos, o sugerir
    categorías relevantes). Devuelve una lista paginada de instancias de la entidad
    Category almacenadas en la base de datos.

    Parámetros:
    - ctx: contexto de ejecución que provee dependencias (p. ej. sesión de BD).
    - offset: desplazamiento para paginación (índice de inicio) por defecto es 0 pero puedes pasar cualquier número entero positivo.
    - limit: número máximo de categorías a devolver por defecto es 10 pero puedes pasar cualquier número entero positivo.

    Retorna:
    - list[Category]: lista de objetos Category (pueden incluir categorías por defecto
      y/o creadas por usuarios), respetando offset y limit.

    Esquema de la tabla Category:
    - id: int
    - name: str
    - description: str
    - is_default: bool
    - user_id: int (foreign key references user(id))
    - created_at: datetime
    - updated_at: datetime
    """
    return db.get_db_entities(
        entity=Category, offset=offset, limit=limit, session=ctx.deps.session
    )


@react_agent.tool
def get_category_by_name(ctx: RunContext[AgentDeps], name: str) -> Category | None:
    """
    Obtiene una categoría por su nombre.

    Usa esta herramienta cuando el agente necesita encontrar una categoría específica
    por su nombre (por ejemplo, para mostrar detalles, clasificar elementos, o sugerir
    categorías relacionadas).

    Parámetros:
    - ctx: contexto de ejecución que provee dependencias (p. ej. sesión de BD).
    - name: nombre de la categoría a buscar.

    Retorna:
    - Category | None: objeto Category si se encuentra, None si no se encuentra.
    """
    return db.get_entity_by_field(
        type_entity=Category,
        field_name="name",
        field_value=name,
        session=ctx.deps.session,
    )
