"""
Report Model

Stores generated financial reports for users.
"""

from datetime import datetime
from enum import Enum

from sqlmodel import Field

from app.models.base import Base


class ReportType(str, Enum):
    """Types of financial reports."""

    MONTHLY_SUMMARY = "monthly_summary"
    CATEGORY_BREAKDOWN = "category_breakdown"
    INCOME_VS_EXPENSES = "income_vs_expenses"
    TRANSACTION_HISTORY = "transaction_history"
    SAVINGS_ANALYSIS = "savings_analysis"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Export formats for reports."""

    JSON = "json"
    PDF = "pdf"
    CSV = "csv"


class ReportStatus(str, Enum):
    """Status of report generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base, table=True):
    """Financial report model."""

    user_id: int = Field(
        description="User ID",
        foreign_key="user.id",
        index=True,
        nullable=False,
    )
    title: str = Field(
        description="Report title",
        max_length=200,
        nullable=False,
    )
    report_type: str = Field(
        default=ReportType.MONTHLY_SUMMARY.value,
        description="Type of report",
        index=True,
        nullable=False,
    )
    format: str = Field(
        default=ReportFormat.JSON.value,
        description="Export format",
        nullable=False,
    )
    status: str = Field(
        default=ReportStatus.PENDING.value,
        description="Generation status",
        index=True,
        nullable=False,
    )
    period_start: datetime = Field(
        description="Start of the reporting period",
        nullable=False,
    )
    period_end: datetime = Field(
        description="End of the reporting period",
        nullable=False,
    )
    data: str | None = Field(
        default=None,
        description="JSON data of the report",
    )
    ai_summary: str | None = Field(
        default=None,
        description="AI-generated summary of the report",
    )
    file_path: str | None = Field(
        default=None,
        description="Path to exported file (PDF/CSV)",
        max_length=500,
    )
