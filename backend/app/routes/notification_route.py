
# GET    /notifications
# POST   /notifications/{id}/read
# GET    /search?q=...&type=meeting|document|run









from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.controllers.notification_controller import NotificationController
from app.schemas.entities.notification_entity import Notification

router = APIRouter()
notification_controller = NotificationController()


@router.get("/", response_model=list[Notification])
def list_notifications(current_user=Depends(get_current_user)):
    return notification_controller.list_for_user(current_user.id)


@router.post("/{notification_id}/read", response_model=Notification)
def mark_read(notification_id: str, current_user=Depends(get_current_user)):
    return notification_controller.mark_read(notification_id)
