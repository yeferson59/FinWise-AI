from datetime import datetime
from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""

    title: str = Field(max_length=150)
    body: str = Field(max_length=500)
    notification_type: str = Field(default="system")
    priority: str = Field(default="medium")
    icon: str = Field(default="bell", max_length=50)
    scheduled_at: datetime | None = None
    action_url: str | None = Field(default=None, max_length=255)
    metadata: str | None = None


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    title: str | None = Field(default=None, max_length=150)
    body: str | None = Field(default=None, max_length=500)
    is_read: bool | None = None
    scheduled_at: datetime | None = None


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    id: int
    user_id: int
    title: str
    body: str
    notification_type: str
    priority: str
    icon: str
    is_read: bool
    scheduled_at: datetime | None
    action_url: str | None
    metadata: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReminderCreate(BaseModel):
    """Schema for creating a reminder with natural language."""

    message: str = Field(description="Natural language description of the reminder")
    scheduled_at: datetime | None = Field(
        default=None,
        description="When to send the reminder (optional, can be parsed from message)",
    )


class NotificationStats(BaseModel):
    """Stats about user's notifications."""

    total: int
    unread: int
    by_type: dict[str, int]
