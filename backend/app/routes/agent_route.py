from typing import Any, Dict, Tuple

from fastapi import APIRouter, HTTPException, status

from app.agents import AGENTS, AGENT_MAP
from app.agents.base import BaseAgent
from app.core.llm import LLMError
from app.models.workflow import WorkflowSession
from app.orchestration.handoff import check_handoff, document_text
from app.orchestration.runner import agent_runner
from app.orchestration.workflow_engine import workflow_engine
from app.schemas.agent_schema import AgentRunRequest, AgentRunResponse, AgentRunStatus

router = APIRouter()


def _prepare(agent_id: str, payload: AgentRunRequest) -> Tuple[BaseAgent, WorkflowSession, str, Dict[str, Any]]:
    agent = AGENT_MAP.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found. Known agents: {', '.join(AGENT_MAP)}.")
    session = None
    if payload.workflow_id:
        session = workflow_engine.get_workflow(payload.workflow_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Workflow '{payload.workflow_id}' not found.")
    options_extra: Dict[str, Any] = {}
    if payload.source_artifact_id:
        source = workflow_engine.get_artifact(payload.source_artifact_id)
        if not source or not session:
            raise HTTPException(status_code=404, detail="The output to hand over was not found in this workflow.")
        problem = check_handoff(session, source, agent)
        if problem:
            raise HTTPException(status_code=409, detail=problem)
        payload.input_text = document_text(source.content)  # the generated document itself is the input
        options_extra["handoff_from"] = source.artifact_id
    input_text = payload.input_text or (session.normalized_input if session else "")
    if not input_text.strip() and not (session and session.outputs):
        raise HTTPException(status_code=400, detail="Either workflow_id or input_text must be provided.")
    if not session:
        session = workflow_engine.create_workflow(title=f"Session for {agent.name}", normalized_input=input_text)
    options = {k: v for k, v in payload.model_dump(include={"document_type", "use_case", "rubric"}).items() if v}
    return agent, session, input_text, {**options, **options_extra}


@router.get("", tags=["SDLC Agents"])
async def list_agents():
    return [
        {
            "id": a.id,
            "name": a.name,
            "purpose": a.purpose,
            "stage": a.stage.value,
            "required_inputs": a.required_inputs,
            "consumes": list(a.consumes),
            "prompt_version": a.prompt_version,
        }
        for a in AGENTS
    ]


@router.get("/runs/{run_id}", response_model=AgentRunStatus, tags=["SDLC Agents"])
async def get_run(run_id: str):
    run = agent_runner.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run


@router.post("/{agent_id}/runs", response_model=AgentRunStatus, status_code=status.HTTP_202_ACCEPTED, tags=["SDLC Agents"])
async def start_run(agent_id: str, payload: AgentRunRequest):
    agent, session, input_text, options = _prepare(agent_id, payload)
    return agent_runner.submit(agent, session, input_text, options)


@router.post("/{agent_id}", response_model=AgentRunResponse, tags=["SDLC Agents"])
async def run_agent(agent_id: str, payload: AgentRunRequest):
    agent, session, input_text, options = _prepare(agent_id, payload)
    try:
        return await agent_runner.execute(agent, session, input_text, options)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"Agent '{agent_id}' could not get a valid answer: {e}")
