"""
Report Schemas

Request/response models for financial reports.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request to generate a new report."""

    report_type: str = Field(default="monthly_summary")
    period_start: datetime
    period_end: datetime
    format: str = Field(default="json")
    title: str | None = None
    include_ai_summary: bool = Field(default=True)


class CategoryBreakdown(BaseModel):
    """Spending breakdown by category."""

    category_id: int
    category_name: str
    total_amount: float
    percentage: float
    transaction_count: int


class MonthlyTrend(BaseModel):
    """Monthly trend data point."""

    month: str
    year: int
    income: float
    expenses: float
    balance: float


class ReportData(BaseModel):
    """Full report data structure."""

    period_start: str
    period_end: str
    total_income: float
    total_expenses: float
    net_balance: float
    savings_rate: float
    transaction_count: int
    category_breakdown: list[CategoryBreakdown]
    monthly_trends: list[MonthlyTrend]
    top_expenses: list[dict]
    income_sources: list[dict]


class ReportResponse(BaseModel):
    """Response with generated report."""

    id: int
    user_id: int
    title: str
    report_type: str
    format: str
    status: str
    period_start: datetime
    period_end: datetime
    data: ReportData | None = None
    ai_summary: str | None = None
    file_path: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    """Brief report info for listing."""

    id: int
    title: str
    report_type: str
    format: str
    status: str
    period_start: datetime
    period_end: datetime
    created_at: datetime

    class Config:
        from_attributes = True
