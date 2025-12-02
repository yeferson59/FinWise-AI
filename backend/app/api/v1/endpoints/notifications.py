"""
Notifications API Endpoints

Provides CRUD operations for user notifications and reminders.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db.session import SessionDep
from app.services import notification as notification_service
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationStats,
)

router = APIRouter()


class MarkReadRequest(BaseModel):
    notification_id: int


class CreateReminderRequest(BaseModel):
    user_id: int
    title: str
    body: str
    scheduled_at: datetime | None = None


@router.get("/{user_id}", response_model=list[NotificationResponse])
async def get_notifications(
    session: SessionDep,
    user_id: int,
    unread_only: bool = Query(default=False),
    notification_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[NotificationResponse]:
    """
    Get notifications for a user.

    Parameters:
    - user_id: The user's ID
    - unread_only: If true, only return unread notifications
    - notification_type: Filter by type (transaction, reminder, etc.)
    - limit: Maximum notifications to return (default 50)
    - offset: Pagination offset

    Returns:
    - List of notifications ordered by creation date (newest first)
    """
    notifications = await notification_service.get_user_notifications(
        session=session,
        user_id=user_id,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        offset=offset,
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get("/{user_id}/stats", response_model=NotificationStats)
async def get_notification_stats(
    session: SessionDep,
    user_id: int,
) -> NotificationStats:
    """
    Get notification statistics for a user.

    Returns:
    - Total notification count
    - Unread count
    - Count by notification type
    """
    return await notification_service.get_notification_stats(session, user_id)


@router.post("/{user_id}", response_model=NotificationResponse)
async def create_notification(
    session: SessionDep,
    user_id: int,
    notification: NotificationCreate,
) -> NotificationResponse:
    """
    Create a new notification for a user.

    Parameters:
    - user_id: The user's ID
    - notification: Notification data

    Returns:
    - The created notification
    """
    result = await notification_service.create_notification(
        session=session,
        user_id=user_id,
        notification=notification,
    )
    return NotificationResponse.model_validate(result)


@router.post("/{user_id}/reminder", response_model=NotificationResponse)
async def create_reminder(
    session: SessionDep,
    user_id: int,
    request: CreateReminderRequest,
) -> NotificationResponse:
    """
    Create a reminder notification.

    Parameters:
    - user_id: The user's ID
    - request: Reminder data with title, body, and optional scheduled time

    Returns:
    - The created reminder notification
    """
    result = await notification_service.create_reminder(
        session=session,
        user_id=user_id,
        title=request.title,
        body=request.body,
        scheduled_at=request.scheduled_at,
    )
    return NotificationResponse.model_validate(result)


@router.patch("/{user_id}/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    session: SessionDep,
    user_id: int,
    notification_id: int,
) -> NotificationResponse:
    """
    Mark a notification as read.

    Parameters:
    - user_id: The user's ID
    - notification_id: The notification's ID

    Returns:
    - The updated notification
    """
    result = await notification_service.mark_as_read(
        session=session,
        notification_id=notification_id,
        user_id=user_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(result)


@router.patch("/{user_id}/read-all")
async def mark_all_read(
    session: SessionDep,
    user_id: int,
) -> dict:
    """
    Mark all notifications as read for a user.

    Returns:
    - Count of notifications marked as read
    """
    count = await notification_service.mark_all_as_read(session, user_id)
    return {"marked_as_read": count}


@router.delete("/{user_id}/{notification_id}")
async def delete_notification(
    session: SessionDep,
    user_id: int,
    notification_id: int,
) -> dict:
    """
    Delete a notification.

    Returns:
    - Success status
    """
    deleted = await notification_service.delete_notification(
        session=session,
        notification_id=notification_id,
        user_id=user_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"deleted": True}
