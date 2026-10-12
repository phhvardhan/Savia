
from typing import List

from app.core.repositories import meeting_repo, document_repo, run_repo


class SearchService:

    async def search(self, query: str, workspace_id: str, type_filter: str | None = None) -> dict:
        q = query.lower().strip()
        results = {"meetings": [], "documents": [], "runs": []}
        if not q:
            return results

        if type_filter in (None, "meeting"):
            results["meetings"] = [
                m for m in meeting_repo.list(filter_fn=lambda m: m.workspace_id == workspace_id)
                if q in m.title.lower()
            ]
        if type_filter in (None, "document"):
            results["documents"] = [
                d for d in document_repo.list(filter_fn=lambda d: d.workspace_id == workspace_id)
                if q in d.title.lower()
            ]
        if type_filter in (None, "run"):
            results["runs"] = [
                r for r in run_repo.list(filter_fn=lambda r: r.workspace_id == workspace_id)
                if q in r.type.value.lower()
            ]
        return results
