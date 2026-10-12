
from typing import Optional
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.controllers.search_controller import SearchController

router = APIRouter()
search_controller = SearchController()


@router.get("/")
def search(q: str, workspace_id: str, type: Optional[str] = None, current_user=Depends(get_current_user)):
    return search_controller.search(q, workspace_id, type)
