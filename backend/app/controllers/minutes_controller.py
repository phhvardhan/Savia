from fastapi import HTTPException, status

from app.services.minutes_service import MinutesService
from app.schemas.requests.minutes_request import (
    ActionItemCreateRequest, ActionItemUpdateRequest, DecisionCreateRequest, DecisionUpdateRequest
)
from app.utils.response import success_response, error_response


minutes_service = MinutesService()


class MinutesController:

    async def get_summary(self, meeting_id: str):
        return await minutes_service.get_summary(meeting_id)

    async def update_summary(self, meeting_id: str, content: str):
        return await minutes_service.update_summary(meeting_id, content)

    async def get_transcript(self, meeting_id: str):
        return await minutes_service.get_transcript(meeting_id)

    async def get_decisions(self, meeting_id: str):
        return await minutes_service.get_decisions(meeting_id)

    async def add_decision(self, meeting_id: str, payload: DecisionCreateRequest):
        return await minutes_service.add_decision(meeting_id, payload)

    async def update_decision(self, meeting_id: str, decision_id: str, payload: DecisionUpdateRequest):
        return await minutes_service.update_decision(meeting_id, decision_id, payload)

    async def delete_decision(self, meeting_id: str, decision_id: str):
        await minutes_service.delete_decision(meeting_id, decision_id)

    async def list_action_items(self, meeting_id: str):
        return await minutes_service.list_action_items(meeting_id)

    async def add_action_item(self, meeting_id: str, payload: ActionItemCreateRequest):
        return await minutes_service.add_action_item(meeting_id, payload)

    async def update_action_item(self, meeting_id: str, item_id: str, payload: ActionItemUpdateRequest):
        return await minutes_service.update_action_item(meeting_id, item_id, payload)

    async def delete_action_item(self, meeting_id: str, item_id: str):
        await minutes_service.delete_action_item(meeting_id, item_id)

    async def approve_minutes(self, meeting_id: str, user_id: str):
        return await minutes_service.approve_minutes(meeting_id, user_id)

    async def get_questions(self, meeting_id: str):
        return await minutes_service.get_questions(meeting_id)

    async def answer_questions(self, meeting_id: str, payload: dict):
        return await minutes_service.answer_questions(meeting_id, payload)

    async def export_excel(self, meeting_id: str) -> bytes:
        return await minutes_service.export_excel(meeting_id)
