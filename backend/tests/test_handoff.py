import asyncio
from app.agents import AGENT_MAP
from app.models.workflow import Artifact, StageEnum
from app.orchestration import handoff
from app.orchestration.workflow_engine import workflow_engine

GOOD = {
    "epics": ["Onboarding", "Reporting"],
    "user_stories": [{"user_story_id": "US-001", "title": "Register", "requirement_ids": ["REQ-001"],
                      "description": "Vendors register with company details so procurement can review them."}] * 3,
    "open_questions": ["Which tax formats are accepted?"],
}


def test_document_text_matches_the_ui_flattening():
    text = handoff.document_text({"summary": "Hi", "key_points": ["a", "b"], "empty": [], "none": None})
    assert text == "Summary: Hi\nKey points:\n• a\n• b"


def test_readiness_holds_every_iteration_to_the_same_bar():
    agent = AGENT_MAP["agile-stories"]
    ok = handoff.readiness(agent, GOOD, {}, "REQ-001: vendor portal", {})
    assert ok["ready"] and ok["score"] == 1.0
    thin = handoff.readiness(agent, {"epics": [], "user_stories": []}, {}, "", {})
    assert not thin["ready"] and any("empty" in i for i in thin["issues"])
    untraced = handoff.readiness(agent, {**GOOD, "user_stories": [{"title": "x" * 400, "requirement_ids": []}]}, {}, "REQ-001: x", {})
    assert any("IDs the input defines" in i for i in untraced["issues"])
    bad = handoff.readiness(agent, GOOD, {"unsupported_figures": ["$5"], "dangling_references": ["REQ-9"]}, "REQ-001", {})
    assert len(bad["issues"]) == 2


def test_next_agent_prefers_the_agent_that_builds_on_the_output(monkeypatch):
    session = workflow_engine.create_workflow(title="handoff test", normalized_input="notes")
    mom = workflow_engine.save_artifact(session.workflow_id, "mom", StageEnum.MOM, {"summary": "Vendor portal"})

    async def fake_recommend(session, raw_text=None, input_type=None, filename=None):
        # The model rates readiness-audit a hair above agile-stories; the hand-off graph must still win.
        recs = [{"agent": a, "agent_name": a, "reason": "", "confidence": 0.0, "matched": False, "required_inputs": []} for a in AGENT_MAP]
        for r in recs:
            r["confidence"] = {"readiness-audit": 0.5, "agile-stories": 0.45}.get(r["agent"], 0.0)
        return {"recommended_agents": recs, "source": "llm"}

    monkeypatch.setattr(handoff.savia_orchestrator, "recommend", fake_recommend)
    decision = asyncio.run(handoff.next_agent(session, mom))
    assert decision["agent"] == "agile-stories" and decision["builds_on_output"]
    assert decision["recommendation"]["primary_agent"] == "agile-stories"
    assert "mom" not in decision["alternatives"]


def test_handoff_refuses_the_source_agent_and_agents_that_already_ran():
    session = workflow_engine.create_workflow(title="handoff guard", normalized_input="notes")
    mom = workflow_engine.save_artifact(session.workflow_id, "mom", StageEnum.MOM, {"summary": "x"})
    assert handoff.check_handoff(session, mom, AGENT_MAP["agile-stories"]) is None
    assert "different agent" in handoff.check_handoff(session, mom, AGENT_MAP["mom"])
    workflow_engine.save_artifact(session.workflow_id, "agile-stories", StageEnum.USER_STORY, {"epics": ["a"]})
    assert "already run" in handoff.check_handoff(session, mom, AGENT_MAP["agile-stories"])


def test_next_agent_does_not_skip_a_lifecycle_stage(monkeypatch):
    session = workflow_engine.create_workflow(title="stage order", normalized_input="notes")
    stories = workflow_engine.save_artifact(session.workflow_id, "agile-stories", StageEnum.USER_STORY, {"epics": ["a"]})

    async def fake_recommend(session, raw_text=None, input_type=None, filename=None):
        # The model likes TEST better than DDL3, but DDL3 is the stage that comes next.
        conf = {"test": 0.8, "ddl3": 0.6}
        recs = [{"agent": a, "agent_name": a, "reason": "", "confidence": conf.get(a, 0.0), "matched": True, "required_inputs": []} for a in AGENT_MAP]
        return {"recommended_agents": recs, "source": "llm"}

    monkeypatch.setattr(handoff.savia_orchestrator, "recommend", fake_recommend)
    assert asyncio.run(handoff.next_agent(session, stories))["agent"] == "ddl3"
