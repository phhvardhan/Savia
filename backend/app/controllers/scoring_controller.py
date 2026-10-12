from typing import Optional, List
from fastapi import HTTPException, status

from app.services.scoring_service import ScoringService
from app.schemas.requests.document_request import ApplyGapSuggestionRequest

scoring_service = ScoringService()


class ScoringController:
    async def evaluate_document(
        self,
        document_text: str,
        document_name: str = "Uploaded Document",
        rubric: str = "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)",
        dimensions: Optional[List[str]] = None,
        user_id: str = "user-1",
    ):
        return await scoring_service.evaluate_document(
            document_text=document_text,
            document_name=document_name,
            rubric=rubric,
            dimensions=dimensions,
            user_id=user_id,
        )

    async def get_review(self, review_id: str):
        return await scoring_service.get_review(review_id)

    async def get_criteria(self, review_id: str):
        return await scoring_service.get_criteria(review_id)

    async def get_gaps(self, review_id: str):
        return await scoring_service.get_gaps(review_id)

    async def get_recommendations(self, review_id: str):
        return await scoring_service.get_recommendations(review_id)

    def apply_suggestion(self, gap_id: str, payload: ApplyGapSuggestionRequest):
        return scoring_service.apply_suggestion(gap_id, payload)

    def dismiss(self, gap_id: str):
        return scoring_service.dismiss(gap_id)
