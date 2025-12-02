"""
Notification Service

Handles creation, retrieval, and management of user notifications and reminders.
"""

from datetime import datetime
from typing import Any, cast

from sqlmodel import and_, col, func, select

from app.db.session import SessionDep
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.schemas.notification import (
    NotificationCreate,
    NotificationStats,
)


async def create_notification(
    session: SessionDep,
    user_id: int,
    notification: NotificationCreate,
) -> Notification:
    """Create a new notification for a user."""
    db_notification = Notification(
        user_id=user_id,
        title=notification.title,
        body=notification.body,
        notification_type=notification.notification_type,
        priority=notification.priority,
        icon=notification.icon,
        scheduled_at=notification.scheduled_at,
        action_url=notification.action_url,
        metadata_json=notification.metadata,
    )
    session.add(db_notification)
    session.commit()
    session.refresh(db_notification)
    return db_notification


async def get_user_notifications(
    session: SessionDep,
    user_id: int,
    unread_only: bool = False,
    notification_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Notification]:
    """Get notifications for a user with optional filters."""
    query = select(Notification).where(Notification.user_id == user_id)

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    if notification_type:
        query = query.where(Notification.notification_type == notification_type)

    # Only show scheduled notifications that are due
    now = datetime.now()
    query = query.where(
        (Notification.scheduled_at == None)  # noqa: E711
        | (cast(Any, Notification.scheduled_at) <= now)
    )

    query = (
        query.order_by(col(Notification.created_at).desc()).offset(offset).limit(limit)
    )

    return list(session.exec(query).all())


async def get_notification_by_id(
    session: SessionDep,
    notification_id: int,
    user_id: int,
) -> Notification | None:
    """Get a specific notification by ID (scoped to user)."""
    query = select(Notification).where(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    return session.exec(query).first()


async def mark_as_read(
    session: SessionDep,
    notification_id: int,
    user_id: int,
) -> Notification | None:
    """Mark a notification as read."""
    notification = await get_notification_by_id(session, notification_id, user_id)
    if notification:
        notification.is_read = True
        notification.updated_at = datetime.now()
        session.add(notification)
        session.commit()
        session.refresh(notification)
    return notification


async def mark_all_as_read(
    session: SessionDep,
    user_id: int,
) -> int:
    """Mark all notifications as read for a user. Returns count of updated."""
    notifications = await get_user_notifications(
        session, user_id, unread_only=True, limit=1000
    )
    count = 0
    for notification in notifications:
        notification.is_read = True
        notification.updated_at = datetime.now()
        session.add(notification)
        count += 1
    session.commit()
    return count


async def delete_notification(
    session: SessionDep,
    notification_id: int,
    user_id: int,
) -> bool:
    """Delete a notification. Returns True if deleted."""
    notification = await get_notification_by_id(session, notification_id, user_id)
    if notification:
        session.delete(notification)
        session.commit()
        return True
    return False


async def get_notification_stats(
    session: SessionDep,
    user_id: int,
) -> NotificationStats:
    """Get notification statistics for a user."""
    # Total count
    total = session.exec(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
    ).one()

    # Unread count
    unread = session.exec(
        select(func.count())
        .select_from(Notification)
        .where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
    ).one()

    # Count by type
    type_query = (
        select(Notification.notification_type, func.count())
        .where(Notification.user_id == user_id)
        .group_by(Notification.notification_type)
    )
    type_results = session.exec(type_query).all()
    by_type = {str(t): int(c) for t, c in type_results}

    return NotificationStats(
        total=int(total) if total else 0,
        unread=int(unread) if unread else 0,
        by_type=by_type,
    )


# ==================== HELPER FUNCTIONS FOR AUTO-NOTIFICATIONS ====================


async def create_transaction_notification(
    session: SessionDep,
    user_id: int,
    transaction_type: str,
    amount: float,
    category_name: str,
    description: str,
) -> Notification:
    """Create a notification when a transaction is registered."""
    type_label = "Gasto" if transaction_type == "expense" else "Ingreso"
    icon = "arrow.up.circle" if transaction_type == "expense" else "arrow.down.circle"

    notification = NotificationCreate(
        title=f"{type_label} registrado",
        body=f"{description} - ${amount:.2f} en {category_name}",
        notification_type=NotificationType.TRANSACTION.value,
        priority=NotificationPriority.LOW.value,
        icon=icon,
    )
    return await create_notification(session, user_id, notification)


async def create_budget_alert(
    session: SessionDep,
    user_id: int,
    category_name: str,
    percentage: int,
) -> Notification:
    """Create a budget alert notification."""
    notification = NotificationCreate(
        title="⚠️ Alerta de presupuesto",
        body=f"Has usado el {percentage}% de tu presupuesto en {category_name}",
        notification_type=NotificationType.BUDGET_ALERT.value,
        priority=NotificationPriority.HIGH.value,
        icon="exclamationmark.triangle",
    )
    return await create_notification(session, user_id, notification)


async def create_reminder(
    session: SessionDep,
    user_id: int,
    title: str,
    body: str,
    scheduled_at: datetime | None = None,
) -> Notification:
    """Create a reminder notification."""
    notification = NotificationCreate(
        title=f"🔔 {title}",
        body=body,
        notification_type=NotificationType.REMINDER.value,
        priority=NotificationPriority.MEDIUM.value,
        icon="bell.badge",
        scheduled_at=scheduled_at,
    )
    return await create_notification(session, user_id, notification)


async def create_financial_tip(
    session: SessionDep,
    user_id: int,
    tip: str,
) -> Notification:
    """Create a financial tip notification."""
    notification = NotificationCreate(
        title="💡 Consejo financiero",
        body=tip,
        notification_type=NotificationType.TIP.value,
        priority=NotificationPriority.LOW.value,
        icon="lightbulb",
    )
    return await create_notification(session, user_id, notification)
