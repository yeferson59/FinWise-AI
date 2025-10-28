from pydantic_ai import Agent, RunContext
from app.models.category import Category
from app.models.user import User
from app.models.transaction import Transaction
from functools import lru_cache
from app.core.llm import get_model
from dataclasses import dataclass
from app.db.session import SessionDep
from app.config import get_settings
from app.utils import db
from sqlmodel import select, func, and_
from datetime import datetime

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
    system_prompt="""You are FinWise AI, an intelligent financial assistant specialized in personal finance management.
    
Your role is to help users understand and manage their finances by:
- Providing insights into their transactions and spending patterns
- Answering questions about their financial data (users, categories, transactions)
- Analyzing income vs expenses and financial health
- Offering personalized financial recommendations based on their data
- Generating financial summaries and reports

You follow the ReAct (Reasoning + Acting) pattern:
1. REASON about what information you need to answer the user's question
2. ACT by using the available tools to gather that information
3. OBSERVE the results from the tools
4. Repeat as necessary to gather all required information
5. Provide a clear, helpful response based on the data

Available data domains:
- Users: User accounts and profiles in the system
- Categories: Financial transaction categories (income, expenses, etc.)
- Transactions: Financial transactions with amounts, dates, categories, and sources

Guidelines:
- Always think step by step before using tools
- Use multiple tools if needed to provide comprehensive answers
- Present financial data clearly with amounts, dates, and context
- Respect pagination limits when querying large datasets
- Provide actionable insights when analyzing financial patterns
- Be helpful, accurate, and professional in your responses

When users ask about financial summaries or analysis, make sure to:
- Calculate totals and aggregations accurately
- Compare time periods when relevant
- Identify spending patterns or anomalies
- Provide context for the numbers (e.g., "This represents X% of your total spending")""",
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


# ==================== USER MANAGEMENT TOOLS ====================


@react_agent.tool
def get_users_count(ctx: RunContext[AgentDeps]) -> int:
    """
    Get the total number of users in the system.

    Use this tool when the agent needs to know how many users are registered
    in the system, for example when answering questions like "How many users
    do we have?" or "What's the total user count?".

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).

    Returns:
    - int: total number of users in the database.
    """
    return db.get_total_count(User, ctx.deps.session)


@react_agent.tool
def get_user_by_id(ctx: RunContext[AgentDeps], user_id: int) -> User | None:
    """
    Get a specific user by their ID.

    Use this tool when you need to retrieve details about a specific user,
    such as their name, email, or account status.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - user_id: the unique identifier of the user.

    Returns:
    - User | None: User object if found, None otherwise.

    User schema:
    - id: int
    - first_name: str
    - last_name: str
    - email: str
    - is_active: bool
    - created_at: datetime
    - updated_at: datetime
    """
    try:
        return db.get_entity_by_id(User, user_id, ctx.deps.session)
    except Exception:
        return None


@react_agent.tool
def get_user_by_email(ctx: RunContext[AgentDeps], email: str) -> User | None:
    """
    Find a user by their email address.

    Use this tool when you need to look up a user by their email,
    for example when the user provides an email instead of an ID.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - email: the email address to search for.

    Returns:
    - User | None: User object if found, None otherwise.
    """
    return db.get_entity_by_field(
        type_entity=User,
        field_name="email",
        field_value=email,
        session=ctx.deps.session,
    )


@react_agent.tool
def get_all_users(
    ctx: RunContext[AgentDeps], offset: int = 0, limit: int = 10
) -> list[User]:
    """
    Get a paginated list of all users in the system.

    Use this tool when you need to list users, for example to show
    all registered users or to iterate through the user base.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - offset: pagination offset (starting index), default is 0.
    - limit: maximum number of users to return, default is 10.

    Returns:
    - list[User]: list of User objects respecting pagination parameters.
    """
    return db.get_db_entities(
        entity=User, offset=offset, limit=limit, session=ctx.deps.session
    )


# ==================== TRANSACTION MANAGEMENT TOOLS ====================


@react_agent.tool
def get_all_transactions(
    ctx: RunContext[AgentDeps], offset: int = 0, limit: int = 10
) -> list[Transaction]:
    """
    Get a paginated list of all transactions in the system.

    Use this tool to retrieve transactions from the database. This is useful
    for general queries about transactions or when listing recent activity.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - offset: pagination offset (starting index), default is 0.
    - limit: maximum number of transactions to return, default is 10.

    Returns:
    - list[Transaction]: list of Transaction objects.

    Transaction schema:
    - id: str (UUID)
    - user_id: int (foreign key to user)
    - category_id: int (foreign key to category)
    - source_id: int (foreign key to source)
    - description: str
    - amount: float
    - date: datetime
    - state: str (e.g., "pending", "completed")
    - created_at: datetime
    - updated_at: datetime
    """
    return db.get_db_entities(
        entity=Transaction, offset=offset, limit=limit, session=ctx.deps.session
    )


@react_agent.tool
def get_transactions_by_user(
    ctx: RunContext[AgentDeps], user_id: int, offset: int = 0, limit: int = 10
) -> list[Transaction]:
    """
    Get all transactions for a specific user.

    Use this tool when you need to retrieve a user's transaction history,
    for example to analyze their spending or answer questions about their
    financial activity.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - user_id: the ID of the user whose transactions you want to retrieve.
    - offset: pagination offset, default is 0.
    - limit: maximum number of transactions to return, default is 10.

    Returns:
    - list[Transaction]: list of transactions belonging to the user.
    """
    return db.get_entities_by_field(
        type_entity=Transaction,
        field_name="user_id",
        field_value=user_id,
        session=ctx.deps.session,
        offset=offset,
        limit=limit,
    )


@react_agent.tool
def get_transactions_by_category(
    ctx: RunContext[AgentDeps], category_id: int, offset: int = 0, limit: int = 10
) -> list[Transaction]:
    """
    Get all transactions for a specific category.

    Use this tool when analyzing spending in a particular category,
    such as "Food", "Transportation", or "Entertainment".

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - category_id: the ID of the category to filter by.
    - offset: pagination offset, default is 0.
    - limit: maximum number of transactions to return, default is 10.

    Returns:
    - list[Transaction]: list of transactions in that category.
    """
    return db.get_entities_by_field(
        type_entity=Transaction,
        field_name="category_id",
        field_value=category_id,
        session=ctx.deps.session,
        offset=offset,
        limit=limit,
    )


@react_agent.tool
def get_transaction_by_id(
    ctx: RunContext[AgentDeps], transaction_id: str
) -> Transaction | None:
    """
    Get a specific transaction by its ID.

    Use this tool when you need detailed information about a specific
    transaction, for example to check its status or details.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - transaction_id: the unique identifier (UUID) of the transaction.

    Returns:
    - Transaction | None: Transaction object if found, None otherwise.
    """
    try:
        return db.get_entity_by_id(Transaction, transaction_id, ctx.deps.session)
    except Exception:
        return None


@react_agent.tool
def count_transactions(ctx: RunContext[AgentDeps]) -> int:
    """
    Get the total number of transactions in the system.

    Use this tool when you need to know how many transactions exist,
    for example to provide statistics or context about the data volume.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).

    Returns:
    - int: total number of transactions.
    """
    return db.get_total_count(Transaction, ctx.deps.session)


@react_agent.tool
def count_user_transactions(ctx: RunContext[AgentDeps], user_id: int) -> int:
    """
    Count how many transactions a specific user has.

    Use this tool when you need to know a user's transaction volume,
    for example to assess their activity level or provide statistics.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - user_id: the ID of the user.

    Returns:
    - int: number of transactions for the user.
    """
    count = ctx.deps.session.exec(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == user_id)
    ).one()
    return count


# ==================== FINANCIAL ANALYSIS TOOLS ====================


@react_agent.tool
def calculate_total_amount(
    ctx: RunContext[AgentDeps],
    user_id: int | None = None,
    category_id: int | None = None,
) -> float:
    """
    Calculate the total amount of transactions with optional filters.

    Use this tool to compute total spending or income. You can filter
    by user or category to get specific totals.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - user_id: optional user ID to filter by.
    - category_id: optional category ID to filter by.

    Returns:
    - float: total sum of transaction amounts matching the filters.

    Examples:
    - calculate_total_amount(user_id=1) -> total for user 1
    - calculate_total_amount(category_id=5) -> total for category 5
    - calculate_total_amount(user_id=1, category_id=5) -> total for user 1 in category 5
    - calculate_total_amount() -> grand total of all transactions
    """
    query = select(func.sum(Transaction.amount)).select_from(Transaction)

    filters = []
    if user_id is not None:
        filters.append(Transaction.user_id == user_id)
    if category_id is not None:
        filters.append(Transaction.category_id == category_id)

    if filters:
        query = query.where(and_(*filters))

    result = ctx.deps.session.exec(query).one()
    return float(result) if result is not None else 0.0


@react_agent.tool
def get_transactions_by_date_range(
    ctx: RunContext[AgentDeps],
    start_date: str,
    end_date: str,
    user_id: int | None = None,
    offset: int = 0,
    limit: int = 10,
) -> list[Transaction]:
    """
    Get transactions within a specific date range.

    Use this tool to analyze transactions for a specific time period,
    such as monthly or weekly reports.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - start_date: start date in ISO format (e.g., "2024-01-01" or "2024-01-01T00:00:00").
    - end_date: end date in ISO format (e.g., "2024-01-31" or "2024-01-31T23:59:59").
    - user_id: optional user ID to filter by.
    - offset: pagination offset, default is 0.
    - limit: maximum number of transactions to return, default is 10.

    Returns:
    - list[Transaction]: transactions within the date range.

    Example:
    - get_transactions_by_date_range("2024-01-01", "2024-01-31", user_id=1)
      -> all transactions for user 1 in January 2024
    """
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return []

    query = select(Transaction).where(
        and_(Transaction.date >= start_dt, Transaction.date <= end_dt)
    )

    if user_id is not None:
        query = query.where(Transaction.user_id == user_id)

    query = query.offset(offset).limit(limit)
    transactions = ctx.deps.session.exec(query).all()
    return list(transactions)


@react_agent.tool
def calculate_amount_by_date_range(
    ctx: RunContext[AgentDeps],
    start_date: str,
    end_date: str,
    user_id: int | None = None,
    category_id: int | None = None,
) -> float:
    """
    Calculate total transaction amount within a date range.

    Use this tool to compute spending or income for a specific time period,
    useful for monthly summaries, budget tracking, and trend analysis.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - start_date: start date in ISO format (e.g., "2024-01-01").
    - end_date: end date in ISO format (e.g., "2024-01-31").
    - user_id: optional user ID to filter by.
    - category_id: optional category ID to filter by.

    Returns:
    - float: total amount of transactions in the date range.

    Example:
    - calculate_amount_by_date_range("2024-01-01", "2024-01-31", user_id=1)
      -> total spending for user 1 in January 2024
    """
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 0.0

    query = (
        select(func.sum(Transaction.amount))
        .select_from(Transaction)
        .where(and_(Transaction.date >= start_dt, Transaction.date <= end_dt))
    )

    if user_id is not None:
        query = query.where(Transaction.user_id == user_id)
    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)

    result = ctx.deps.session.exec(query).one()
    return float(result) if result is not None else 0.0


@react_agent.tool
def get_spending_by_category(
    ctx: RunContext[AgentDeps], user_id: int, limit: int = 10
) -> list[dict]:
    """
    Analyze a user's spending breakdown by category.

    Use this tool to understand how a user distributes their spending
    across different categories. This is useful for budget analysis and
    identifying major expense categories.

    Parameters:
    - ctx: execution context providing dependencies (e.g., DB session).
    - user_id: the ID of the user to analyze.
    - limit: maximum number of categories to return, default is 10.

    Returns:
    - list[dict]: list of dictionaries with category_id, category_name, and total_amount.
      Results are ordered by total_amount descending (highest spending first).

    Example result:
    [
        {"category_id": 1, "category_name": "Food", "total_amount": 500.0},
        {"category_id": 2, "category_name": "Transport", "total_amount": 200.0}
    ]
    """
    query = (
        select(
            Transaction.category_id,
            Category.name.label("category_name"),
            func.sum(Transaction.amount).label("total_amount"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )

    results = ctx.deps.session.exec(query).all()

    return [
        {
            "category_id": row[0],
            "category_name": row[1],
            "total_amount": float(row[2]) if row[2] else 0.0,
        }
        for row in results
    ]
