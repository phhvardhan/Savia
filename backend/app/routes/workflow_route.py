import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.export import artifact_to_xlsx
from app.brand import fonts as brand_fonts
from app.brand import jnj_tokens as brand_tokens
from app.brand.adapter import to_brand_document
from app.brand.renderer_docx import render_artifact_docx, render_docx_bytes, resolved_styles
from app.brand.validator import BrandViolation
from app.core.deck import solution_to_pptx
from app.agents import AGENT_MAP
from app.core.llm import call_llm
from app.core.quality import assess
from app.core.security import get_current_user
from app.core.text import fit_text
from app.models.workflow import ApprovalStatus, Artifact, StageEnum
from app.orchestration.handoff import next_agent
from app.orchestration.runner import artifact_response
from app.orchestration.stage_manager import GateError, stage_manager
from app.orchestration.workflow_engine import workflow_engine
from app.schemas.workflow_schema import AdvanceStageRequest, ApproveStageRequest, WorkflowCreateRequest

router = APIRouter()
fonts_router = APIRouter()


@router.post("", tags=["Workflows"])
async def create_workflow(payload: WorkflowCreateRequest):
    session = workflow_engine.create_workflow(
        title=payload.title or "SAVIA SDLC Session",
        source_documents=payload.source_documents or [],
        normalized_input=payload.normalized_input or "",
        input_type=payload.input_type or "unknown"
    )
    return session


@router.get("/{workflow_id}", tags=["Workflows"])
async def get_workflow(workflow_id: str):
    return _workflow(workflow_id)


def _workflow(workflow_id: str):
    session = workflow_engine.get_workflow(workflow_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return session


@router.post("/{workflow_id}/approve", tags=["Workflows"])
async def approve_output(workflow_id: str, payload: ApproveStageRequest, user=Depends(get_current_user)):
    session = _workflow(workflow_id)
    if payload.artifact_id:
        artifact = workflow_engine.get_artifact(payload.artifact_id)
    else:
        pending = stage_manager.pending_artifacts(session)
        artifact = max(pending, key=lambda a: a.created_at) if pending else None
    try:
        decision = ApprovalStatus(payload.decision)
    except ValueError:
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'.")
    if decision not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'.")
    approver = user.username if user.id != "usr-local" else (payload.user_id or user.username)
    try:
        artifact = stage_manager.approve(session, artifact, approver, payload.comments, decision)
    except GateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    updated = workflow_engine.get_workflow(workflow_id)
    return {
        "status": decision.value,
        "stage": artifact.stage.value,
        "artifact_id": artifact.artifact_id,
        "version": artifact.version,
        "workflow": updated,
    }


@router.post("/{workflow_id}/advance", tags=["Workflows"])
async def advance_stage(workflow_id: str, payload: AdvanceStageRequest):
    session = _workflow(workflow_id)
    try:
        target_stage = StageEnum(payload.target_stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid target stage '{payload.target_stage}'. Valid stages: {[s.value for s in StageEnum]}")
    try:
        stage_manager.move_to(session, target_stage, require_approved=True)
    except GateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    updated = workflow_engine.update_workflow(session)
    return {"status": "advanced", "current_stage": updated.current_stage.value, "workflow": updated}


class NextAgentRequest(BaseModel):
    artifact_id: str | None = None


@router.post("/{workflow_id}/next-agent", tags=["Workflows"])
async def route_next_agent(workflow_id: str, payload: NextAgentRequest):
    """Orchestration: reads a generated output and names the agent that should take it next."""
    session = _workflow(workflow_id)
    if payload.artifact_id:
        artifact = workflow_engine.get_artifact(payload.artifact_id)
    else:
        artifacts = workflow_engine.get_workflow_artifacts(workflow_id)
        artifact = max(artifacts, key=lambda a: a.created_at) if artifacts else None
    if not artifact or artifact.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="No generated output in this workflow to hand over.")
    return await next_agent(session, artifact)


@router.get("/{workflow_id}/artifacts", tags=["Artifacts"])
async def list_workflow_artifacts(workflow_id: str):
    artifacts = workflow_engine.get_workflow_artifacts(workflow_id)
    return artifacts


@router.get("/artifacts/{artifact_id}", tags=["Artifacts"])
async def get_artifact(artifact_id: str):
    artifact = workflow_engine.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    return artifact


AGENT_NAMES = {aid: agent.name for aid, agent in AGENT_MAP.items()}

EXPORT_TYPES = {
    "docx": (render_artifact_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "xlsx": (artifact_to_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
}


@router.get("/artifacts/{artifact_id}/export.{fmt}", tags=["Artifacts"])
async def export_artifact(artifact_id: str, fmt: str):
    if fmt not in EXPORT_TYPES and fmt != "pptx":
        raise HTTPException(status_code=400, detail="Format must be docx, xlsx or pptx.")
    artifact = workflow_engine.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    agent_name = AGENT_NAMES.get(artifact.agent_name, artifact.agent_name)

    if fmt == "pptx":
        if artifact.agent_name != "solution-analyzer":
            raise HTTPException(status_code=400, detail="PowerPoint export is only available for the Solution Analyzer.")
        subtitle = f"Prepared with SAVIA · {agent_name} · version {artifact.version}"
        try:
            data = solution_to_pptx(artifact.content, subtitle)
        except BrandViolation as e:
            raise HTTPException(status_code=500, detail=str(e))
        filename = f"savia-solution-blueprint-v{artifact.version}.pptx"
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    build, media_type = EXPORT_TYPES[fmt]
    title, subtitle = _document_titles(artifact, agent_name)
    try:
        data = build(title, subtitle, artifact.content)
    except BrandViolation as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    filename = f"savia-{artifact.agent_name}-v{artifact.version}.{fmt}"
    return Response(data, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _document_titles(artifact, agent_name: str) -> tuple[str, str]:
    title = str(artifact.content.get("title") or agent_name)
    subtitle = f"Generated by SAVIA · {agent_name} · version {artifact.version} · {artifact.created_at[:10]}"
    return title, subtitle


@router.get("/artifacts/{artifact_id}/brand-document", tags=["Artifacts"])
async def brand_document(artifact_id: str):
    artifact = workflow_engine.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    doc = to_brand_document(*_document_titles(artifact, AGENT_NAMES.get(artifact.agent_name, artifact.agent_name)),
                            artifact.content)
    try:
        render_docx_bytes(doc)
    except BrandViolation as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"document": doc.model_dump(), "styles": resolved_styles(), "fonts": brand_fonts.font_faces(),
            "page_background": brand_tokens.hex_for(brand_tokens.PAGE_BACKGROUND),
            "rule_color": brand_tokens.hex_for(brand_tokens.RULE_COLOR)}


@fonts_router.get("/brand/fonts/{filename}", tags=["Artifacts"])
async def brand_font(filename: str):
    match = next((p for p in brand_fonts.font_files() if p.name == filename), None)
    if not match:
        raise HTTPException(status_code=404, detail="Font not found.")
    return FileResponse(match)


SOURCE_CHARS = 24000


def _artifact_and_source(artifact_id: str):
    artifact = workflow_engine.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    session = workflow_engine.get_workflow(artifact.workflow_id)
    source = (session.normalized_input if session else "") or ""
    return artifact, fit_text(source, SOURCE_CHARS)


def _revise(artifact: Artifact, content: Dict[str, Any], event: str) -> Dict[str, Any]:
    session = workflow_engine.get_workflow(artifact.workflow_id)
    source = session.normalized_input if session else ""
    upstream = {
        a.agent_name: a.content
        for a in (workflow_engine.get_artifact(i) for i in artifact.traceability.upstream_artifact_ids)
        if a
    }
    revised = workflow_engine.save_artifact(
        workflow_id=artifact.workflow_id,
        agent_name=artifact.agent_name,
        stage=artifact.stage,
        content=content,
        traceability=artifact.traceability,
        quality=assess(content, source, upstream, AGENT_MAP[artifact.agent_name].defines if artifact.agent_name in AGENT_MAP else ()),
        meta={**artifact.meta, "revision_of": artifact.artifact_id, "revision": event},
    )
    return artifact_response(revised, {"artifact_ids": artifact.traceability.upstream_artifact_ids})


class SuggestEditRequest(BaseModel):
    section: str
    instruction: str


class ApplyEditRequest(BaseModel):
    section: str
    value: object


SUGGEST_SYSTEM = (
    "You revise ONE section of an SDLC deliverable, following the user's instruction.\n"
    "RULES:\n"
    "1. Change only this section. Keep its JSON type and shape: a string stays a string; a list of "
    "objects stays a list of objects with the same keys.\n"
    "2. Ground every statement in the SOURCE INPUT, the CURRENT SECTION or the INSTRUCTION (facts the user "
    "states in the instruction, such as a decision they made, count as provided). Do not invent names, "
    "numbers, dates, systems or decisions.\n"
    "3. If the instruction needs facts that are not in the source, do not guess: return the section "
    "unchanged and list the questions in needs_info.\n"
    "4. unsupported_claims: any statement in your revision that the source does not directly support "
    "(empty list if none).\n"
    "5. summary: one plain sentence saying what you changed.\n"
    'Return only JSON: {"revised": <section value>, "summary": "...", '
    '"unsupported_claims": ["..."], "needs_info": ["..."]}'
)


@router.post("/artifacts/{artifact_id}/suggest-edit", tags=["Artifacts"])
async def suggest_edit(artifact_id: str, payload: SuggestEditRequest):
    artifact, source = _artifact_and_source(artifact_id)
    if payload.section not in artifact.content:
        raise HTTPException(status_code=404, detail=f"Section '{payload.section}' not in this output.")
    if not payload.instruction.strip():
        raise HTTPException(status_code=400, detail="Tell Savia what to change.")

    current = artifact.content[payload.section]
    user = (
        f"SECTION: {payload.section}\n"
        f"CURRENT SECTION (JSON):\n{json.dumps(current, indent=2)}\n\n"
        f"INSTRUCTION: {payload.instruction}\n\n"
        f"SOURCE INPUT:\n{source or '(none)'}"
    )
    try:
        data = await call_llm(SUGGEST_SYSTEM, user, expected_type=dict)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Savia could not draft the change: {e}")

    needs_info = [str(q) for q in data.get("needs_info") or [] if str(q).strip()]
    revised = data.get("revised", current)
    if needs_info or type(revised) is not type(current):
        revised = current
    return {
        "section": payload.section,
        "original": current,
        "revised": revised,
        "summary": "" if needs_info else str(data.get("summary") or "").strip(),
        "unsupported_claims": [] if needs_info else [str(c) for c in data.get("unsupported_claims") or [] if str(c).strip()],
        "needs_info": needs_info,
    }


@router.post("/artifacts/{artifact_id}/apply-edit", tags=["Artifacts"])
async def apply_edit(artifact_id: str, payload: ApplyEditRequest):
    artifact, _ = _artifact_and_source(artifact_id)
    if payload.section not in artifact.content:
        raise HTTPException(status_code=404, detail=f"Section '{payload.section}' not in this output.")
    return _revise(artifact, {**artifact.content, payload.section: payload.value}, "edit")


DECISIONS_SYSTEM = (
    "You review an SDLC deliverable and its source input for decisions that are still OPEN: things the "
    "team discussed or must settle but did not decide (e.g. a threshold, retention period, approach, owner).\n"
    "RULES:\n"
    "1. Only real open decisions evidenced by the text. If none, return an empty list. At most 3.\n"
    "2. For each, give exactly 2 realistic options grounded in the text, each with a one-line trade-off "
    "(cost). Do not invent facts.\n"
    "3. section: the key of the deliverable section the decision belongs in (must be one of SECTION KEYS).\n"
    "4. leaning: 0 or 1 for the option the text points towards, with a short leaning_reason; "
    "null if the text gives no lean.\n"
    'Return only JSON: {"decisions": [{"question": "...", "evidence": "short quote", "section": "<key>", '
    '"options": [{"title": "...", "text": "...", "cost": "..."}, {"title": "...", "text": "...", "cost": "..."}], '
    '"leaning": 0, "leaning_reason": "..."}]}'
)


@router.post("/artifacts/{artifact_id}/open-decisions", tags=["Artifacts"])
async def open_decisions(artifact_id: str):
    artifact, source = _artifact_and_source(artifact_id)
    keys = list(artifact.content.keys())
    user = (
        f"SECTION KEYS: {keys}\n\n"
        f"DELIVERABLE (JSON):\n{json.dumps(artifact.content)[:SOURCE_CHARS]}\n\n"
        f"SOURCE INPUT:\n{source or '(none)'}"
    )
    try:
        data = await call_llm(DECISIONS_SYSTEM, user, expected_type=dict)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Savia could not review the document: {e}")

    decisions = []
    for d in data.get("decisions") or []:
        options = [o for o in d.get("options") or [] if isinstance(o, dict) and o.get("title")][:2]
        if not d.get("question") or len(options) < 2:
            continue
        leaning = d.get("leaning")
        decisions.append({
            "question": str(d["question"]),
            "evidence": str(d.get("evidence") or ""),
            "section": d.get("section") if d.get("section") in artifact.content else keys[0],
            "options": [{k: str(o.get(k) or "") for k in ("title", "text", "cost")} for o in options],
            "leaning": leaning if leaning in (0, 1) else None,
            "leaning_reason": str(d.get("leaning_reason") or ""),
        })
    return {"decisions": decisions[:3]}


class RecordDecisionRequest(BaseModel):
    question: str
    chosen_title: str
    chosen_text: str = ""


RECORD_DECISION_SYSTEM = (
    "You record a decision the user just made into an SDLC deliverable (JSON).\\n"
    "RULES:\\n"
    "1. Add the decision where decisions belong (e.g. a decisions list), copying the shape of existing "
    "entries (same keys, next id). If there is no decisions section, put it in the most fitting section.\\n"
    "2. Resolve the question wherever it is listed as open (e.g. remove it from open questions). Do not add "
    "new questions.\\n"
    "3. Change nothing else. Return ONLY the sections you changed, each with the same JSON type and shape.\\n"
    'Return only JSON: {"updates": {"<section key>": <new value>, ...}}'
)


@router.post("/artifacts/{artifact_id}/record-decision", tags=["Artifacts"])
async def record_decision(artifact_id: str, payload: RecordDecisionRequest):
    artifact, _ = _artifact_and_source(artifact_id)
    user = (
        f"QUESTION: {payload.question}\\n"
        f"DECISION MADE BY THE USER: {payload.chosen_title}. {payload.chosen_text}\\n\\n"
        f"DELIVERABLE (JSON):\\n{json.dumps(artifact.content, indent=2)}"
    )
    try:
        data = await call_llm(RECORD_DECISION_SYSTEM, user, expected_type=dict)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Savia could not record the decision: {e}")

    updates = {
        key: value
        for key, value in (data.get("updates") or {}).items()
        if key in artifact.content and type(value) is type(artifact.content[key])
    }
    if not updates:
        raise HTTPException(status_code=502, detail="Savia could not work out where to record this decision.")
    return _revise(artifact, {**artifact.content, **updates}, "decision")
