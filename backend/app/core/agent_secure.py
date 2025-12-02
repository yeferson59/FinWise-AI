"""
Secure Financial AI Agent

This module implements a secure AI agent that is scoped to only access
data belonging to the authenticated user. It prevents access to:
- Other users' data
- Sensitive system information
- User management operations
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from sqlmodel import and_, func, select

from app.config import get_settings
from app.core.llm import get_model
from app.db.session import SessionDep
from app.models.category import Category
from app.models.transaction import Source, Transaction

settings = get_settings()
model = get_model()


@dataclass
class AgentDeps:
    """Dependencies for the secure agent, including user scoping."""

    session: SessionDep
    user_id: int  # The authenticated user's ID - all queries are scoped to this user


class TransactionSummary(BaseModel):
    """Safe transaction data to return (excludes sensitive fields)."""

    id: str
    description: str
    amount: float
    transaction_type: str
    date: str
    category_name: str | None = None
    source_name: str | None = None


class CategoryInfo(BaseModel):
    """Safe category info."""

    id: int
    name: str
    description: str | None = None


class SpendingByCategory(BaseModel):
    """Spending breakdown by category."""

    category_id: int
    category_name: str
    total_amount: float
    transaction_count: int


class CreatedTransaction(BaseModel):
    """Response after creating a transaction."""

    id: str
    title: str
    description: str
    amount: float
    transaction_type: str
    category_name: str
    source_name: str
    date: str
    message: str


# Create the secure agent with user-scoped system prompt
react_agent = Agent(
    model=model,
    deps_type=AgentDeps,
    model_settings={"temperature": settings.temperature, "top_p": settings.top_p},
    system_prompt="""You are FinWise AI, an intelligent personal financial assistant.

IMPORTANT SECURITY RULES:
- You can ONLY access the authenticated user's own financial data
- You CANNOT access data from other users
- You CANNOT reveal system information, database structure, or internal details
- You CANNOT perform administrative operations
- If asked about other users or system details, politely decline and explain you can only help with the user's personal finances

Your role is to help the user understand and manage THEIR finances by:
- Providing insights into their transactions and spending patterns
- Analyzing their income vs expenses
- Offering personalized financial recommendations
- Generating financial summaries and reports
- Answering questions about their financial data
- CREATING NEW TRANSACTIONS when the user asks to register expenses or income
- CREATING REMINDERS for financial tasks

CREATING TRANSACTIONS:
When the user wants to register a transaction (expense or income), you should:
1. First use get_current_datetime to know the current date
2. Use get_categories to see available categories
3. Use get_sources to see available payment sources
4. Extract from the user's message:
   - Amount (required)
   - Description (from context)
   - Type: "expense" (gasto) or "income" (ingreso)
   - Category (match to existing categories)
   - Source (match to existing sources, default to id=1 if unsure)
   - Date (use current date if not specified, or parse relative dates like "ayer", "hace 2 días")
5. Use create_transaction to register it
6. Confirm the transaction was created with details

Examples of transaction requests:
- "Gasté $50 en comida" -> expense, $50, category: food/alimentación
- "Pagué $100 de luz" -> expense, $100, category: services/servicios
- "Me pagaron $1000 de sueldo" -> income, $1000, category: salary/salario
- "Ayer compré gasolina por $40" -> expense, $40, yesterday's date
- "Registra un ingreso de $500 por freelance" -> income, $500

CREATING REMINDERS:
When the user wants to set a reminder, use the create_reminder tool.
Examples of reminder requests:
- "Recuérdame pagar la luz mañana" -> reminder for tomorrow
- "Avísame en 3 días sobre el alquiler" -> reminder in 3 days
- "Crear recordatorio para revisar gastos el viernes"
- "No dejes que olvide pagar la tarjeta"

You can also use get_my_reminders to show the user their pending reminders.

Guidelines:
- Always be helpful, accurate, and professional
- Present financial data clearly with amounts, dates, and context
- Provide actionable insights when analyzing financial patterns
- Be encouraging and supportive about financial goals
- Respond in the same language as the user's question (Spanish or English)
- When creating transactions or reminders, always confirm what was created

When providing financial analysis:
- Calculate totals and aggregations accurately
- Compare time periods when relevant
- Identify spending patterns or trends
- Provide context for the numbers (e.g., "This represents X% of your total spending")""",
)


@react_agent.system_prompt
def add_current_datetime(ctx: RunContext[AgentDeps]) -> str:
    """Add current datetime to system prompt dynamically."""
    now = datetime.now()
    days_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return f"""
CURRENT DATE AND TIME INFORMATION:
- Date: {now.strftime("%Y-%m-%d")}
- Time: {now.strftime("%H:%M:%S")}
- Day: {days_es[now.weekday()]}
- Full: {now.strftime("%d de %B de %Y")}

Use get_current_datetime tool for precise datetime when creating transactions."""


# ==================== CATEGORY TOOLS (Read-only, safe) ====================


@react_agent.tool
def get_categories(ctx: RunContext[AgentDeps], limit: int = 50) -> list[CategoryInfo]:
    """
    Get available spending categories.

    Returns the list of categories that can be used for transactions.
    This includes both default system categories and any custom categories
    created by the user.

    Parameters:
    - limit: maximum number of categories to return (default 50)

    Returns:
        list[CategoryInfo]: list of categories with id, name, and description
    """
    # Get default categories and user's custom categories
    query = (
        select(Category)
        .where(
            (Category.is_default == True)  # noqa: E712
            | (Category.user_id == ctx.deps.user_id)
        )
        .limit(limit)
    )
    categories = ctx.deps.session.exec(query).all()

    return [
        CategoryInfo(id=cat.id, name=cat.name, description=cat.description)
        for cat in categories
    ]


@react_agent.tool
def get_category_by_name(ctx: RunContext[AgentDeps], name: str) -> CategoryInfo | None:
    """
    Find a category by its name.

    Parameters:
    - name: the category name to search for

    Returns:
        CategoryInfo if found, None otherwise
    """
    query = select(Category).where(
        (Category.name.ilike(f"%{name}%"))  # type: ignore[attr-defined]
        & ((Category.is_default == True) | (Category.user_id == ctx.deps.user_id))  # noqa: E712
    )
    category = ctx.deps.session.exec(query).first()

    if category:
        return CategoryInfo(
            id=category.id, name=category.name, description=category.description
        )
    return None


# ==================== TRANSACTION TOOLS (User-scoped) ====================


@react_agent.tool
def get_my_transactions(
    ctx: RunContext[AgentDeps], offset: int = 0, limit: int = 20
) -> list[TransactionSummary]:
    """
    Get the user's recent transactions.

    Retrieves the user's transaction history, ordered by most recent first.

    Parameters:
    - offset: pagination offset (default 0)
    - limit: maximum transactions to return (default 20, max 100)

    Returns:
        list[TransactionSummary]: list of the user's transactions
    """
    limit = min(limit, 100)  # Cap at 100 for performance

    query = (
        select(Transaction, Category.name, Source.name)
        .outerjoin(Category, Transaction.category_id == Category.id)  # type: ignore[arg-type]
        .outerjoin(Source, Transaction.source_id == Source.id)  # type: ignore[arg-type]
        .where(Transaction.user_id == ctx.deps.user_id)
        .order_by(Transaction.date.desc())  # type: ignore[attr-defined]
        .offset(offset)
        .limit(limit)
    )
    results = ctx.deps.session.exec(query).all()

    return [
        TransactionSummary(
            id=str(tx.id),
            description=tx.description,
            amount=tx.amount,
            transaction_type=tx.transaction_type,
            date=tx.date.isoformat() if tx.date else "",
            category_name=cast(str | None, cat_name),
            source_name=cast(str | None, src_name),
        )
        for tx, cat_name, src_name in results
    ]


@react_agent.tool
def get_transactions_by_category(
    ctx: RunContext[AgentDeps], category_name: str, limit: int = 20
) -> list[TransactionSummary]:
    """
    Get the user's transactions in a specific category.

    Parameters:
    - category_name: name of the category to filter by
    - limit: maximum transactions to return (default 20)

    Returns:
        list[TransactionSummary]: transactions in that category
    """
    limit = min(limit, 100)

    query = (
        select(Transaction, Category.name, Source.name)
        .join(Category, Transaction.category_id == Category.id)  # type: ignore[arg-type]
        .outerjoin(Source, Transaction.source_id == Source.id)  # type: ignore[arg-type]
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(Category.name.ilike(f"%{category_name}%"))  # type: ignore[attr-defined]
        .order_by(Transaction.date.desc())  # type: ignore[attr-defined]
        .limit(limit)
    )
    results = ctx.deps.session.exec(query).all()

    return [
        TransactionSummary(
            id=str(tx.id),
            description=tx.description,
            amount=tx.amount,
            transaction_type=tx.transaction_type,
            date=tx.date.isoformat() if tx.date else "",
            category_name=cast(str | None, cat_name),
            source_name=cast(str | None, src_name),
        )
        for tx, cat_name, src_name in results
    ]


@react_agent.tool
def get_transactions_by_date_range(
    ctx: RunContext[AgentDeps],
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> list[TransactionSummary]:
    """
    Get the user's transactions within a date range.

    Parameters:
    - start_date: start date in ISO format (e.g., "2024-01-01")
    - end_date: end date in ISO format (e.g., "2024-01-31")
    - limit: maximum transactions to return (default 50)

    Returns:
        list[TransactionSummary]: transactions in the date range
    """
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return []

    limit = min(limit, 100)

    query = (
        select(Transaction, Category.name, Source.name)
        .outerjoin(Category, Transaction.category_id == Category.id)  # type: ignore[arg-type]
        .outerjoin(Source, Transaction.source_id == Source.id)  # type: ignore[arg-type]
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(and_(Transaction.date >= start_dt, Transaction.date <= end_dt))
        .order_by(Transaction.date.desc())  # type: ignore[attr-defined]
        .limit(limit)
    )
    results = ctx.deps.session.exec(query).all()

    return [
        TransactionSummary(
            id=str(tx.id),
            description=tx.description,
            amount=tx.amount,
            transaction_type=tx.transaction_type,
            date=tx.date.isoformat() if tx.date else "",
            category_name=cast(str | None, cat_name),
            source_name=cast(str | None, src_name),
        )
        for tx, cat_name, src_name in results
    ]


# ==================== FINANCIAL ANALYSIS TOOLS (User-scoped) ====================


@react_agent.tool
def count_my_transactions(ctx: RunContext[AgentDeps]) -> int:
    """
    Count the total number of transactions the user has.

    Returns:
        int: total number of transactions
    """
    # Execute a scalar count query and extract the value reliably.
    # Exec(...).one() may return a scalar or a Row-like object; normalize both cases.
    result = ctx.deps.session.exec(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == ctx.deps.user_id)
    ).one()
    # Normalize possible return shapes (scalar, tuple, Row)
    if isinstance(result, (tuple, list)):
        value = result[0] if result else 0
    else:
        value = cast(Any, result)
    return int(value or 0)


@react_agent.tool
def calculate_my_totals(
    ctx: RunContext[AgentDeps], category_name: str | None = None
) -> dict:
    """
    Calculate the user's total income and expenses.

    Parameters:
    - category_name: optional category to filter by

    Returns:
        dict with total_income, total_expenses, and balance
    """
    base_query = select(
        Transaction.transaction_type, func.sum(Transaction.amount)
    ).where(Transaction.user_id == ctx.deps.user_id)

    if category_name:
        base_query = base_query.join(
            Category,
            Transaction.category_id == Category.id,  # type: ignore[arg-type]
        ).where(Category.name.ilike(f"%{category_name}%"))  # type: ignore[attr-defined]

    query = base_query.group_by(cast(Any, Transaction.transaction_type))  # type: ignore[arg-type]
    results = ctx.deps.session.exec(query).all()

    totals = {"income": 0.0, "expense": 0.0}
    for tx_type, amount in results:
        if tx_type in totals and amount:
            totals[tx_type] = float(amount)

    return {
        "total_income": totals["income"],
        "total_expenses": totals["expense"],
        "balance": totals["income"] - totals["expense"],
    }


@react_agent.tool
def calculate_totals_by_date_range(
    ctx: RunContext[AgentDeps],
    start_date: str,
    end_date: str,
) -> dict:
    """
    Calculate totals for a specific time period.

    Useful for monthly summaries, weekly reports, or custom date ranges.

    Parameters:
    - start_date: start date in ISO format (e.g., "2024-01-01")
    - end_date: end date in ISO format (e.g., "2024-01-31")

    Returns:
        dict with total_income, total_expenses, balance, and transaction_count
    """
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "balance": 0.0,
            "transaction_count": 0,
        }

    # Get totals by type
    query = (
        select(Transaction.transaction_type, func.sum(Transaction.amount))
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(and_(Transaction.date >= start_dt, Transaction.date <= end_dt))
        .group_by(Transaction.transaction_type)
    )
    results = ctx.deps.session.exec(query).all()

    totals = {"income": 0.0, "expense": 0.0}
    for tx_type, amount in results:
        if tx_type in totals and amount:
            totals[tx_type] = float(amount)

    # Get count (normalize scalar/row return)
    result = ctx.deps.session.exec(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(and_(Transaction.date >= start_dt, Transaction.date <= end_dt))
    ).one()
    if isinstance(result, (tuple, list)):
        count = int(result[0] if result else 0)
    else:
        count = int(cast(Any, result) or 0)

    return {
        "total_income": totals["income"],
        "total_expenses": totals["expense"],
        "balance": totals["income"] - totals["expense"],
        "transaction_count": count,
    }


@react_agent.tool
def get_spending_by_category(
    ctx: RunContext[AgentDeps], limit: int = 10
) -> list[SpendingByCategory]:
    """
    Analyze spending breakdown by category.

    Shows how the user's spending is distributed across different categories.
    Useful for budget analysis and identifying major expense areas.

    Parameters:
    - limit: maximum categories to return (default 10)

    Returns:
        list[SpendingByCategory]: categories sorted by spending (highest first)
    """
    query = (
        select(
            cast(Any, Transaction.category_id),
            cast(Any, Category.name),
            cast(Any, func.sum(Transaction.amount)),
            func.count(cast(Any, Transaction.id)),
        )
        .join(Category, Transaction.category_id == Category.id)  # type: ignore[arg-type]
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(Transaction.transaction_type == "expense")
        .group_by(cast(Any, Transaction.category_id), cast(Any, Category.name))  # type: ignore[arg-type]
        .order_by(func.sum(Transaction.amount).desc())  # type: ignore[attr-defined]
        .limit(limit)
    )
    results = ctx.deps.session.exec(query).all()

    return [
        SpendingByCategory(
            category_id=cat_id,
            category_name=cat_name,
            total_amount=float(total) if total else 0.0,
            transaction_count=count,
        )
        for cat_id, cat_name, total, count in results
    ]


@react_agent.tool
def get_income_by_category(
    ctx: RunContext[AgentDeps], limit: int = 10
) -> list[SpendingByCategory]:
    """
    Analyze income breakdown by category.

    Shows how the user's income is distributed across different categories.

    Parameters:
    - limit: maximum categories to return (default 10)

    Returns:
        list[SpendingByCategory]: categories sorted by income (highest first)
    """
    query = (
        select(
            cast(Any, Transaction.category_id),
            cast(Any, Category.name),
            cast(Any, func.sum(Transaction.amount)),
            func.count(cast(Any, Transaction.id)),
        )
        .join(Category, Transaction.category_id == Category.id)  # type: ignore[arg-type]
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(Transaction.transaction_type == "income")
        .group_by(cast(Any, Transaction.category_id), cast(Any, Category.name))  # type: ignore[arg-type]
        .order_by(func.sum(Transaction.amount).desc())  # type: ignore[attr-defined]
        .limit(limit)
    )
    results = ctx.deps.session.exec(query).all()

    return [
        SpendingByCategory(
            category_id=cat_id,
            category_name=cat_name,
            total_amount=float(total) if total else 0.0,
            transaction_count=count,
        )
        for cat_id, cat_name, total, count in results
    ]


@react_agent.tool
def get_monthly_summary(ctx: RunContext[AgentDeps], year: int, month: int) -> dict:
    """
    Get a financial summary for a specific month.

    Parameters:
    - year: the year (e.g., 2024)
    - month: the month (1-12)

    Returns:
        dict with income, expenses, balance, transaction count, and top categories
    """
    # Validate month
    if month < 1 or month > 12:
        return {"error": "Month must be between 1 and 12"}

    # Calculate date range for the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Get totals
    query = (
        select(
            cast(Any, Transaction.transaction_type),
            cast(Any, func.sum(Transaction.amount)),
        )
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(and_(Transaction.date >= start_date, Transaction.date < end_date))
        .group_by(cast(Any, Transaction.transaction_type))  # type: ignore[arg-type]
    )
    results = ctx.deps.session.exec(query).all()

    totals = {"income": 0.0, "expense": 0.0}
    for tx_type, amount in results:
        if tx_type in totals and amount:
            totals[tx_type] = float(amount)

    # Get transaction count (normalize scalar/row return)
    result = ctx.deps.session.exec(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(and_(Transaction.date >= start_date, Transaction.date < end_date))
    ).one()
    if isinstance(result, (tuple, list)):
        count = int(result[0] if result else 0)
    else:
        count = int(cast(Any, result) or 0)

    # Get top spending categories
    top_categories_query = (
        select(cast(Any, Category.name), cast(Any, func.sum(Transaction.amount)))
        .join(Category, Transaction.category_id == Category.id)  # type: ignore[arg-type]
        .where(Transaction.user_id == ctx.deps.user_id)
        .where(Transaction.transaction_type == "expense")
        .where(and_(Transaction.date >= start_date, Transaction.date < end_date))
        .group_by(cast(Any, Category.name))  # type: ignore[arg-type]
        .order_by(func.sum(Transaction.amount).desc())  # type: ignore[attr-defined]
        .limit(5)
    )
    top_categories = ctx.deps.session.exec(top_categories_query).all()

    return {
        "year": year,
        "month": month,
        "total_income": totals["income"],
        "total_expenses": totals["expense"],
        "balance": totals["income"] - totals["expense"],
        "transaction_count": count,
        "top_expense_categories": [
            {"name": name, "amount": float(amount) if amount else 0.0}
            for name, amount in top_categories
        ],
    }


# ==================== UTILITY TOOLS ====================


@react_agent.tool
def get_current_datetime(ctx: RunContext[AgentDeps]) -> dict:
    """
    Get the current date and time.

    Use this tool to know the current date when creating transactions
    or when the user refers to relative dates like "today", "yesterday",
    "last week", etc.

    Returns:
        dict with current datetime information:
        - datetime: full ISO datetime string
        - date: date in YYYY-MM-DD format
        - time: time in HH:MM:SS format
        - day_of_week: name of the day (Monday, Tuesday, etc.)
        - day_of_week_es: nombre del día en español
    """
    now = datetime.now()
    days_en = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    days_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": days_en[now.weekday()],
        "day_of_week_es": days_es[now.weekday()],
        "year": now.year,
        "month": now.month,
        "day": now.day,
    }


@react_agent.tool
def get_sources(ctx: RunContext[AgentDeps], limit: int = 20) -> list[dict]:
    """
    Get available payment/income sources.

    Use this tool to know what sources are available for transactions
    (e.g., cash, credit card, bank account, etc.)

    Parameters:
    - limit: maximum sources to return (default 20)

    Returns:
        list of sources with id and name
    """
    query = (
        select(Source)
        .where(
            (Source.is_default == True)  # noqa: E712
            | (Source.user_id == ctx.deps.user_id)
        )
        .limit(limit)
    )
    sources = ctx.deps.session.exec(query).all()

    return [
        {"id": src.id, "name": src.name, "description": src.description}
        for src in sources
    ]


# ==================== TRANSACTION CREATION TOOLS ====================


@react_agent.tool
def create_transaction(
    ctx: RunContext[AgentDeps],
    amount: float,
    description: str,
    transaction_type: str,
    category_id: int,
    source_id: int = 1,
    title: str = "",
    date_str: str | None = None,
) -> CreatedTransaction:
    """
    Create a new transaction for the user.

    Use this tool when the user wants to register a new expense or income.
    Before calling this, you should:
    1. Use get_current_datetime to know today's date
    2. Use get_categories to find the appropriate category_id
    3. Use get_sources to find the appropriate source_id

    Parameters:
    - amount: The transaction amount (must be positive)
    - description: Description of the transaction (e.g., "Almuerzo en restaurante")
    - transaction_type: Either "expense" (gasto) or "income" (ingreso)
    - category_id: ID of the category (get from get_categories)
    - source_id: ID of the source (default 1, get from get_sources)
    - title: Short title for the transaction (optional)
    - date_str: Date in YYYY-MM-DD format (optional, defaults to today)
                Can also be relative: "yesterday", "ayer", or days ago like "-1", "-2"

    Returns:
        CreatedTransaction with the details of the created transaction
    """
    # Validate transaction type
    if transaction_type not in ["expense", "income"]:
        return CreatedTransaction(
            id="",
            title="",
            description="",
            amount=0,
            transaction_type="",
            category_name="",
            source_name="",
            date="",
            message=f"Error: transaction_type debe ser 'expense' o 'income', no '{transaction_type}'",
        )

    # Validate amount
    if amount <= 0:
        return CreatedTransaction(
            id="",
            title="",
            description="",
            amount=0,
            transaction_type="",
            category_name="",
            source_name="",
            date="",
            message="Error: El monto debe ser mayor a 0",
        )

    # Parse date
    now = datetime.now()
    if date_str is None:
        tx_date = now
    elif date_str.lower() in ["yesterday", "ayer"]:
        tx_date = now - timedelta(days=1)
    elif date_str.startswith("-") and date_str[1:].isdigit():
        days_ago = int(date_str[1:])
        tx_date = now - timedelta(days=days_ago)
    else:
        try:
            tx_date = datetime.fromisoformat(date_str)
        except ValueError:
            tx_date = now

    # Get category name
    category = ctx.deps.session.exec(
        select(Category).where(Category.id == category_id)
    ).first()
    category_name = category.name if category else "Desconocida"

    # Get source name
    source = ctx.deps.session.exec(select(Source).where(Source.id == source_id)).first()
    source_name = source.name if source else "Desconocida"

    # Create the transaction
    transaction = Transaction(
        user_id=ctx.deps.user_id,
        category_id=category_id,
        source_id=source_id,
        title=title or description[:50],
        description=description,
        amount=amount,
        transaction_type=transaction_type,
        date=tx_date,
        state="completed",
    )

    ctx.deps.session.add(transaction)
    ctx.deps.session.commit()
    ctx.deps.session.refresh(transaction)

    type_label = "gasto" if transaction_type == "expense" else "ingreso"

    return CreatedTransaction(
        id=str(transaction.id),
        title=transaction.title,
        description=transaction.description,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        category_name=category_name,
        source_name=source_name,
        date=transaction.date.strftime("%Y-%m-%d %H:%M"),
        message=f"✅ {type_label.capitalize()} registrado: ${amount:.2f} en {category_name}",
    )


@react_agent.tool
def parse_relative_date(ctx: RunContext[AgentDeps], relative_date: str) -> str:
    """
    Parse a relative date expression to an ISO date string.

    Use this helper to convert relative date expressions to actual dates.

    Parameters:
    - relative_date: Expression like "hoy", "ayer", "anteayer", "hace 3 días",
                    "la semana pasada", "el lunes", etc.

    Returns:
        ISO date string (YYYY-MM-DD)
    """
    now = datetime.now()
    relative_date = relative_date.lower().strip()

    # Common Spanish date expressions
    if relative_date in ["hoy", "today"]:
        return now.strftime("%Y-%m-%d")
    elif relative_date in ["ayer", "yesterday"]:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    elif relative_date in ["anteayer", "antes de ayer"]:
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")
    elif "hace" in relative_date and "día" in relative_date:
        # "hace 3 días", "hace 1 día"
        import re

        match = re.search(r"(\d+)", relative_date)
        if match:
            days = int(match.group(1))
            return (now - timedelta(days=days)).strftime("%Y-%m-%d")
    elif "semana pasada" in relative_date or "last week" in relative_date:
        return (now - timedelta(days=7)).strftime("%Y-%m-%d")

    # Default to today if can't parse
    return now.strftime("%Y-%m-%d")


# ==================== NOTIFICATION/REMINDER TOOLS ====================


class ReminderCreated(BaseModel):
    """Response after creating a reminder."""

    id: int
    title: str
    body: str
    scheduled_at: str | None
    message: str


@react_agent.tool
def create_reminder(
    ctx: RunContext[AgentDeps],
    title: str,
    body: str,
    scheduled_date: str | None = None,
    scheduled_time: str | None = None,
) -> ReminderCreated:
    """
    Create a reminder notification for the user.

    Use this tool when the user wants to set a reminder for something,
    like paying a bill, checking their balance, or any financial task.

    Parameters:
    - title: Short title for the reminder (e.g., "Pagar factura de luz")
    - body: Detailed description (e.g., "Recuerda pagar antes del día 15")
    - scheduled_date: Date for the reminder in YYYY-MM-DD format (optional)
    - scheduled_time: Time for the reminder in HH:MM format (optional)

    Examples of reminder requests:
    - "Recuérdame pagar la luz mañana"
    - "Crear recordatorio para revisar mis gastos el viernes"
    - "Avísame en 3 días sobre el pago del alquiler"

    Returns:
        ReminderCreated with details of the created reminder
    """
    from app.models.notification import (
        Notification,
        NotificationType,
        NotificationPriority,
    )

    now = datetime.now()

    # Parse scheduled datetime
    scheduled_at = None
    if scheduled_date:
        try:
            # Handle relative dates
            if scheduled_date.lower() in ["mañana", "tomorrow"]:
                scheduled_at = now + timedelta(days=1)
            elif scheduled_date.lower() in ["pasado mañana"]:
                scheduled_at = now + timedelta(days=2)
            elif scheduled_date.startswith("+") and scheduled_date[1:].isdigit():
                days = int(scheduled_date[1:])
                scheduled_at = now + timedelta(days=days)
            else:
                scheduled_at = datetime.fromisoformat(scheduled_date)

            # Add time if provided
            if scheduled_time and scheduled_at:
                try:
                    hour, minute = map(int, scheduled_time.split(":"))
                    scheduled_at = scheduled_at.replace(hour=hour, minute=minute)
                except ValueError:
                    pass
        except ValueError:
            scheduled_at = None

    # Create the notification
    notification = Notification(
        user_id=ctx.deps.user_id,
        title=f"🔔 {title}",
        body=body,
        notification_type=NotificationType.REMINDER.value,
        priority=NotificationPriority.MEDIUM.value,
        icon="bell.badge",
        scheduled_at=scheduled_at,
    )

    ctx.deps.session.add(notification)
    ctx.deps.session.commit()
    ctx.deps.session.refresh(notification)

    scheduled_str = (
        scheduled_at.strftime("%Y-%m-%d %H:%M") if scheduled_at else "Inmediato"
    )

    return ReminderCreated(
        id=notification.id,
        title=notification.title,
        body=notification.body,
        scheduled_at=scheduled_str if scheduled_at else None,
        message=f"✅ Recordatorio creado: {title}"
        + (f" para {scheduled_str}" if scheduled_at else ""),
    )


@react_agent.tool
def get_my_reminders(
    ctx: RunContext[AgentDeps],
    include_past: bool = False,
    limit: int = 10,
) -> list[dict]:
    """
    Get the user's pending reminders.

    Use this tool when the user asks about their reminders or
    wants to see what they have scheduled.

    Parameters:
    - include_past: Whether to include past/triggered reminders (default False)
    - limit: Maximum reminders to return (default 10)

    Returns:
        List of reminders with id, title, body, and scheduled_at
    """
    from app.models.notification import Notification, NotificationType

    now = datetime.now()

    query = (
        select(Notification)
        .where(Notification.user_id == ctx.deps.user_id)
        .where(Notification.notification_type == NotificationType.REMINDER.value)
    )

    if not include_past:
        query = query.where(
            (Notification.scheduled_at == None)  # noqa: E711
            | (cast(Any, Notification.scheduled_at) >= now)
        )

    query = query.order_by(cast(Any, Notification.scheduled_at).asc()).limit(limit)
    reminders = ctx.deps.session.exec(query).all()

    return [
        {
            "id": r.id,
            "title": r.title,
            "body": r.body,
            "scheduled_at": r.scheduled_at.strftime("%Y-%m-%d %H:%M")
            if r.scheduled_at
            else None,
            "is_read": r.is_read,
        }
        for r in reminders
    ]
