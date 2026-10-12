"""services/notification_service.py"""

from typing import List, Optional

from fastapi import HTTPException, status

from app.core.repositories import notification_repo
from app.schemas.entities.notification_entity import Notification, NotificationType


class NotificationService:

    async def notify(self, user_id: str, type_: NotificationType, title: str, message: str,
               related_entity_type: Optional[str] = None, related_entity_id: Optional[str] = None) -> Notification:
        """Called by other services (e.g. after a Run completes) to push a notification."""
        return notification_repo.add(Notification(
            user_id=user_id, type=type_, title=title, message=message,
            related_entity_type=related_entity_type, related_entity_id=related_entity_id,
        ))

    async def list_for_user(self, user_id: str) -> List[Notification]:
        notes = notification_repo.list(filter_fn=lambda n: n.user_id == user_id)
        return sorted(notes, key=lambda n: n.created_at, reverse=True)

    async def mark_read(self, notification_id: str) -> Notification:
        note = notification_repo.get(notification_id)
        if not note:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
        return notification_repo.update(notification_id, is_read=True)
