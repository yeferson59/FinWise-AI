"""
Financial Health API Endpoint

Provides AI-powered financial health analysis for users.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.db.session import SessionDep
from app.services.financial_health import get_financial_health, FinancialHealthResponse

router = APIRouter()


class FinancialHealthRequest(BaseModel):
    """Request model for financial health analysis."""

    user_id: int
    period_days: int = 30


@router.post("", response_model=FinancialHealthResponse)
async def analyze_financial_health(
    session: SessionDep,
    request: FinancialHealthRequest,
) -> FinancialHealthResponse:
    """
    Analyze user's financial health with AI-powered insights.

    This endpoint calculates a financial health score based on the user's
    income and expenses, and provides AI-generated analysis and recommendations.

    Parameters:
    - user_id: The ID of the user to analyze
    - period_days: Number of days to analyze (default 30, max 365)

    Returns:
    - FinancialHealthResponse with score, status, and AI recommendations

    The health score is calculated based on:
    - Savings rate (income - expenses) / income
    - Transaction activity
    - Spending patterns

    Score ranges:
    - 85-100: Excellent (green)
    - 70-84: Good (light green)
    - 55-69: Fair (orange)
    - 40-54: Needs attention (dark orange)
    - 0-39: Critical (red)
    """
    period_days = min(max(request.period_days, 7), 365)  # Clamp between 7 and 365

    return await get_financial_health(
        session=session,
        user_id=request.user_id,
        period_days=period_days,
    )


@router.get("/{user_id}", response_model=FinancialHealthResponse)
async def get_user_financial_health(
    session: SessionDep,
    user_id: int,
    period_days: int = Query(default=30, ge=7, le=365),
) -> FinancialHealthResponse:
    """
    Get financial health analysis for a specific user.

    This is a convenience GET endpoint for retrieving financial health.

    Parameters:
    - user_id: The ID of the user (path parameter)
    - period_days: Number of days to analyze (query parameter, default 30)

    Returns:
    - FinancialHealthResponse with score, status, and AI recommendations
    """
    return await get_financial_health(
        session=session,
        user_id=user_id,
        period_days=period_days,
    )
