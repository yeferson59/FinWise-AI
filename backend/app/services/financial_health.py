"""
Financial Health Analysis Service

Provides AI-powered financial health analysis for users,
including health score calculation and personalized recommendations.
"""

from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlmodel import select, func, and_

from app.db.session import SessionDep
from app.models.transaction import Transaction
from app.models.category import Category
from app.core.llm import get_model
from app.config import get_settings

settings = get_settings()


class FinancialHealthResponse(BaseModel):
    """Response model for financial health analysis."""

    score: int  # 0-100
    status: str  # "excellent", "good", "fair", "needs_attention", "critical"
    status_color: str  # Color code for UI
    total_income: float
    total_expenses: float
    balance: float
    savings_rate: float  # Percentage of income saved
    transaction_count: int
    top_expense_categories: list[dict]
    ai_summary: str  # AI-generated analysis
    ai_recommendations: list[str]  # AI-generated recommendations
    period_days: int


def calculate_health_score(
    total_income: float,
    total_expenses: float,
    transaction_count: int,
) -> tuple[int, str, str]:
    """
    Calculate financial health score based on income vs expenses.

    Returns:
        tuple of (score, status, status_color)
    """
    if total_income == 0 and total_expenses == 0:
        return 50, "sin_datos", "#9e9e9e"

    if total_income == 0:
        return 10, "critical", "#f44336"

    savings_rate = ((total_income - total_expenses) / total_income) * 100

    # Score calculation based on savings rate
    if savings_rate >= 30:
        score = min(100, 85 + int(savings_rate - 30))
        status = "excellent"
        color = "#4caf50"
    elif savings_rate >= 20:
        score = 75 + int((savings_rate - 20) * 1)
        status = "good"
        color = "#8bc34a"
    elif savings_rate >= 10:
        score = 60 + int((savings_rate - 10) * 1.5)
        status = "fair"
        color = "#ffb86b"
    elif savings_rate >= 0:
        score = 40 + int(savings_rate * 2)
        status = "needs_attention"
        color = "#ff9800"
    else:
        score = max(0, 40 + int(savings_rate))
        status = "critical"
        color = "#f44336"

    # Adjust for transaction activity
    if transaction_count < 5:
        score = max(score - 10, 0)

    return score, status, color


async def generate_ai_analysis(
    total_income: float,
    total_expenses: float,
    balance: float,
    savings_rate: float,
    top_categories: list[dict],
    transaction_count: int,
    period_days: int,
) -> tuple[str, list[str]]:
    """
    Generate AI-powered financial analysis and recommendations.
    """
    model = get_model()

    # Build context for AI
    categories_text = (
        ", ".join([f"{c['name']}: ${c['amount']:.2f}" for c in top_categories[:5]])
        if top_categories
        else "Sin gastos por categoría"
    )

    prompt = f"""Analiza la salud financiera del usuario y proporciona un resumen breve y 3 recomendaciones prácticas.

DATOS FINANCIEROS (últimos {period_days} días):
- Ingresos totales: ${total_income:.2f}
- Gastos totales: ${total_expenses:.2f}
- Balance: ${balance:.2f}
- Tasa de ahorro: {savings_rate:.1f}%
- Número de transacciones: {transaction_count}
- Principales categorías de gasto: {categories_text}

INSTRUCCIONES:
1. Escribe un resumen de 2-3 oraciones sobre la situación financiera actual (sé directo y útil)
2. Proporciona exactamente 3 recomendaciones cortas y accionables (máximo 15 palabras cada una)

FORMATO DE RESPUESTA (usa exactamente este formato):
RESUMEN: [Tu resumen aquí]
RECOMENDACIÓN 1: [Primera recomendación]
RECOMENDACIÓN 2: [Segunda recomendación]
RECOMENDACIÓN 3: [Tercera recomendación]"""

    try:
        from pydantic_ai import Agent

        agent = Agent(
            model=model,
            model_settings={"temperature": 0.7, "top_p": 0.9},
        )

        result = await agent.run(prompt)
        response_text = result.output

        # Parse response
        lines = response_text.strip().split("\n")
        summary = ""
        recommendations = []

        for line in lines:
            line = line.strip()
            if line.startswith("RESUMEN:"):
                summary = line.replace("RESUMEN:", "").strip()
            elif line.startswith("RECOMENDACIÓN"):
                rec = line.split(":", 1)[-1].strip()
                if rec:
                    recommendations.append(rec)

        # Fallback if parsing fails
        if not summary:
            summary = "Tu situación financiera está siendo analizada. Revisa tus ingresos y gastos para tomar mejores decisiones."
        if len(recommendations) < 3:
            default_recs = [
                "Revisa tus gastos principales y busca oportunidades de ahorro",
                "Establece un presupuesto mensual para cada categoría",
                "Intenta ahorrar al menos el 20% de tus ingresos",
            ]
            recommendations.extend(default_recs[len(recommendations) : 3])

        return summary, recommendations[:3]

    except Exception as e:
        print(f"AI Analysis error: {e}")
        # Provide fallback analysis based on data
        if savings_rate >= 20:
            summary = "¡Excelente! Estás ahorrando una buena parte de tus ingresos. Mantén este hábito."
        elif savings_rate >= 0:
            summary = "Tu balance es positivo pero podrías mejorar tu tasa de ahorro. Revisa gastos no esenciales."
        else:
            summary = "Tus gastos superan tus ingresos. Es importante reducir gastos o aumentar ingresos."

        recommendations = [
            "Revisa tus gastos principales y busca oportunidades de ahorro",
            "Establece un presupuesto mensual para cada categoría",
            "Intenta ahorrar al menos el 20% de tus ingresos",
        ]

        return summary, recommendations


async def get_financial_health(
    session: SessionDep,
    user_id: int,
    period_days: int = 30,
) -> FinancialHealthResponse:
    """
    Calculate financial health score and generate AI analysis for a user.

    Args:
        session: Database session
        user_id: The user's ID
        period_days: Number of days to analyze (default 30)

    Returns:
        FinancialHealthResponse with score, analysis, and recommendations
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)

    # Get transactions for the period
    query = (
        select(Transaction.transaction_type, func.sum(Transaction.amount))
        .where(Transaction.user_id == user_id)
        .where(and_(Transaction.date >= start_date, Transaction.date <= end_date))
        .group_by(Transaction.transaction_type)
    )
    results = session.exec(query).all()

    totals = {"income": 0.0, "expense": 0.0}
    for tx_type, amount in results:
        if tx_type in totals and amount:
            totals[tx_type] = float(amount)

    total_income = totals["income"]
    total_expenses = totals["expense"]
    balance = total_income - total_expenses
    savings_rate = (
        ((total_income - total_expenses) / total_income * 100)
        if total_income > 0
        else 0.0
    )

    # Get transaction count
    count_query = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == user_id)
        .where(and_(Transaction.date >= start_date, Transaction.date <= end_date))
    )
    transaction_count = session.exec(count_query).one()

    # Get top expense categories
    categories_query = (
        select(Category.name, func.sum(Transaction.amount))
        .join(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .where(Transaction.transaction_type == "expense")
        .where(and_(Transaction.date >= start_date, Transaction.date <= end_date))
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_categories = [
        {"name": name, "amount": float(amount) if amount else 0.0}
        for name, amount in session.exec(categories_query).all()
    ]

    # Calculate health score
    score, status, status_color = calculate_health_score(
        total_income, total_expenses, transaction_count
    )

    # Generate AI analysis
    ai_summary, ai_recommendations = await generate_ai_analysis(
        total_income,
        total_expenses,
        balance,
        savings_rate,
        top_categories,
        transaction_count,
        period_days,
    )

    return FinancialHealthResponse(
        score=score,
        status=status,
        status_color=status_color,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        savings_rate=round(savings_rate, 1),
        transaction_count=transaction_count,
        top_expense_categories=top_categories,
        ai_summary=ai_summary,
        ai_recommendations=ai_recommendations,
        period_days=period_days,
    )
