from fastapi import HTTPException, status

from app.services.search_service import SearchService
from app.utils.response import success_response, error_response

search_service = SearchService()


class SearchController:
    async def search(self, query: str, workspace_id: str, type_filter: str | None = None):
        return search_service.search(query, workspace_id, type_filter)
