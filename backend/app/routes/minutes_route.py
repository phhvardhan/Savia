

# GET    /meetings/{id}/summary
# GET    /meetings/{id}/transcript
# GET    /meetings/{id}/decisions
# GET    /meetings/{id}/action-items
# PATCH  /meetings/{id}/action-items/{item_id}     # edit text/owner/due-date/priority
# POST   /meetings/{id}/action-items               # add manual item
# DELETE /meetings/{id}/action-items/{item_id}
# GET    /meetings/{id}/stories-draft              # SAVIA-suggested story stubs pre-Jira-agent
# POST   /meetings/{id}/approve                    # "Approve minutes" — locks + unblocks downstream agents









from fastapi import APIRouter, Depends, Response

from app.core.security import get_current_user
from app.controllers.minutes_controller import MinutesController
from app.schemas.entities.minutes_entity import ( TranscriptSegment, MeetingSummary, Decision, ActionItem, ClarificationQuestion)
from app.schemas.requests.minutes_request import (
    ActionItemCreateRequest, ActionItemUpdateRequest, SummaryUpdateRequest,
    DecisionCreateRequest, DecisionUpdateRequest
)

router = APIRouter()
minutes_controller = MinutesController()


@router.get("/{meeting_id}/summary", response_model=MeetingSummary | None)
async def get_summary(meeting_id: str, current_user=Depends(get_current_user)):
    return await minutes_controller.get_summary(meeting_id)


@router.patch("/{meeting_id}/summary", response_model=MeetingSummary)
async def update_summary(meeting_id: str, payload: SummaryUpdateRequest, current_user=Depends(get_current_user)):
    return await minutes_controller.update_summary(meeting_id, payload.content)


@router.get("/{meeting_id}/transcript", response_model=list[TranscriptSegment])
async def get_transcript(meeting_id: str, current_user=Depends(get_current_user)):
    return await minutes_controller.get_transcript(meeting_id)


@router.get("/{meeting_id}/decisions", response_model=list[Decision])
async def get_decisions(meeting_id: str, current_user=Depends(get_current_user)):
    return await minutes_controller.get_decisions(meeting_id)


@router.post("/{meeting_id}/decisions", response_model=Decision)
async def add_decision(meeting_id: str, payload: DecisionCreateRequest, current_user=Depends(get_current_user)):
    return await minutes_controller.add_decision(meeting_id, payload)


@router.patch("/{meeting_id}/decisions/{decision_id}", response_model=Decision)
async def update_decision(
    meeting_id: str, decision_id: str, payload: DecisionUpdateRequest,
    current_user=Depends(get_current_user),
):
    return await minutes_controller.update_decision(meeting_id, decision_id, payload)


@router.delete("/{meeting_id}/decisions/{decision_id}", status_code=204)
async def delete_decision(meeting_id: str, decision_id: str, current_user=Depends(get_current_user)):
    await minutes_controller.delete_decision(meeting_id, decision_id)


@router.get("/{meeting_id}/action-items", response_model=list[ActionItem])
async def list_action_items(meeting_id: str, current_user=Depends(get_current_user)):
    return await minutes_controller.list_action_items(meeting_id)


@router.post("/{meeting_id}/action-items", response_model=ActionItem)
async def add_action_item(meeting_id: str, payload: ActionItemCreateRequest, current_user=Depends(get_current_user)):
    return await minutes_controller.add_action_item(meeting_id, payload)


@router.patch("/{meeting_id}/action-items/{item_id}", response_model=ActionItem)
async def update_action_item(
    meeting_id: str, item_id: str, payload: ActionItemUpdateRequest,
    current_user=Depends(get_current_user),
):
    return await minutes_controller.update_action_item(meeting_id, item_id, payload)


@router.delete("/{meeting_id}/action-items/{item_id}", status_code=204)
async def delete_action_item(meeting_id: str, item_id: str, current_user=Depends(get_current_user)):
    await minutes_controller.delete_action_item(meeting_id, item_id)


@router.post("/{meeting_id}/approve")
async def approve_minutes(meeting_id: str, current_user=Depends(get_current_user)):
    return await minutes_controller.approve_minutes(meeting_id, current_user.id)


@router.get("/{meeting_id}/questions", response_model=list[ClarificationQuestion])
async def get_questions(meeting_id: str, current_user=Depends(get_current_user)):
    return await minutes_controller.get_questions(meeting_id)


@router.post("/{meeting_id}/questions/answer")
async def answer_questions(meeting_id: str, payload: dict, current_user=Depends(get_current_user)):
    return await minutes_controller.answer_questions(meeting_id, payload)


@router.get("/{meeting_id}/export-excel")
async def export_excel(meeting_id: str, current_user=Depends(get_current_user)):
    content = await minutes_controller.export_excel(meeting_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="meeting_minutes.xlsx"',
        },
    )
