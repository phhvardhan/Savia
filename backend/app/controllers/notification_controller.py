from fastapi import HTTPException, status

from app.services.notification_service import NotificationService
from app.utils.response import success_response, error_response


notification_service = NotificationService()


class NotificationController:
    async def list_for_user(self, user_id: str):
        return notification_service.list_for_user(user_id)

    async def mark_read(self, notification_id: str):
        return notification_service.mark_read(notification_id)
