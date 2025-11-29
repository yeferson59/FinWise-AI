"""
Secure Financial AI Agent

This module implements a secure AI agent that is scoped to only access
data belonging to the authenticated user. It prevents access to:
- Other users' data
- Sensitive system information
- User management operations
"""

from dataclasses import dataclass
from datetime import datetime
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

Guidelines:
- Always be helpful, accurate, and professional
- Present financial data clearly with amounts, dates, and context
- Provide actionable insights when analyzing financial patterns
- Be encouraging and supportive about financial goals
- Respond in the same language as the user's question (Spanish or English)

When providing financial analysis:
- Calculate totals and aggregations accurately
- Compare time periods when relevant
- Identify spending patterns or trends
- Provide context for the numbers (e.g., "This represents X% of your total spending")""",
)


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
            category_name=cat_name,
            source_name=src_name,
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
            category_name=cat_name,
            source_name=src_name,
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
            category_name=cat_name,
            source_name=src_name,
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
            cast(Any, func.count(Transaction.id)),
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
            cast(Any, func.count(Transaction.id)),
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
