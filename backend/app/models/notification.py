from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column
from sqlmodel import Field

from app.models.base import Base


class NotificationType(str, Enum):
    """Types of notifications/reminders."""

    TRANSACTION = "transaction"  # New transaction registered
    BUDGET_ALERT = "budget_alert"  # Budget limit warning
    REMINDER = "reminder"  # User-created reminder
    REPORT = "report"  # Report ready
    TIP = "tip"  # Financial tip
    GOAL = "goal"  # Savings goal update
    SYSTEM = "system"  # System notification


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Notification(Base, table=True):
    """Notification/reminder model for users."""

    user_id: int = Field(
        description="User ID",
        foreign_key="user.id",
        index=True,
        nullable=False,
    )
    title: str = Field(
        description="Notification title",
        max_length=150,
        nullable=False,
    )
    body: str = Field(
        description="Notification body/message",
        max_length=500,
        nullable=False,
    )
    notification_type: str = Field(
        default=NotificationType.SYSTEM.value,
        description="Type of notification",
        index=True,
        nullable=False,
    )
    priority: str = Field(
        default=NotificationPriority.MEDIUM.value,
        description="Priority level",
        nullable=False,
    )
    icon: str = Field(
        default="bell",
        description="Icon name for the notification",
        max_length=50,
        nullable=False,
    )
    is_read: bool = Field(
        default=False,
        description="Whether the notification has been read",
        index=True,
        nullable=False,
    )
    scheduled_at: datetime | None = Field(
        default=None,
        description="When the notification should be shown (for reminders)",
        index=True,
    )
    action_url: str | None = Field(
        default=None,
        description="Optional URL/route to navigate to",
        max_length=255,
    )
    metadata_json: str | None = Field(
        default=None,
        description="JSON with additional data",
        sa_column=Column("metadata", JSON, nullable=True),
    )
