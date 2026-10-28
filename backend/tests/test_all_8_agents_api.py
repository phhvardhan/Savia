import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_TEXT = "REQ-001 Orders must be routed to the nearest warehouse. REQ-002 Stock is checked before routing."

MOM = {"discussion_summary": "Routing review", "attendees": [], "key_points": [], "requirements_identified": [],
       "decisions_finalized": ["Route by distance"], "action_items": [], "open_questions": []}
STORIES = {"epics": ["Fulfilment"], "user_stories": [{"user_story_id": "US-001", "title": "Route orders",
           "requirement_ids": ["REQ-001"], "acceptance_criteria": []}]}
SOLUTION = {"title": "Blueprint", "components": [{"name": "Router"}]}
GAP = {"title": "Gaps", "traceability_matrix": [{"req_id": "REQ-001"}], "gap_classification": []}
DDL3 = {"title": "Routing design", "functional_flow": [{"title": "Receive order", "description": "..."}]}
KDD = {"title": "KDD", "decision_making_framework": []}
IMPACT = {"title": "Impact", "cross_workstream_dependencies": [], "interdependency_matrix": []}
TEST = {"test_cases": [{"title": "Route to nearest", "test_steps": ["Place order"], "requirement_id": "REQ-001"}]}
AUDIT = {
    "dimensions": [{"name": "Completeness & Scope", "score": 70, "weight": 50},
                   {"name": "GxP / Regulatory Audit", "score": 90, "weight": 50}],
    "sdlc_score_justification": {"overall_summary": "Reasonable",
                                 "sdlc_stage_breakdown": [{"sdlc_stage": "1. Requirements", "justification": "IDs present"}]},
}

CASES = [
    ("mom", MOM, "decisions_finalized"),
    ("agile-stories", STORIES, "user_stories"),
    ("solution-analyzer", SOLUTION, "components"),
    ("gap-analysis", GAP, "traceability_matrix"),
    ("ddl3", DDL3, "functional_flow"),
    ("kdd-dab", KDD, "decision_making_framework"),
    ("change-impact", IMPACT, "interdependency_matrix"),
    ("test", TEST, "test_cases"),
    ("readiness-audit", AUDIT, "dimensions"),
]


@pytest.mark.parametrize("agent_id, reply, key", CASES)
def test_every_agent_runs_through_the_api(fake_llm, agent_id, reply, key):
    fake_llm.reply(reply)
    res = client.post(f"/api/v1/agents/{agent_id}", json={"input_text": SAMPLE_TEXT})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["agent_name"] == agent_id
    assert key in body["content"]
    assert body["approval_status"] == "pending"
    assert body["quality"]["checked"] is True


def test_readiness_score_is_computed_from_dimensions(fake_llm):
    fake_llm.reply(AUDIT)
    content = client.post("/api/v1/agents/readiness-audit", json={"input_text": SAMPLE_TEXT}).json()["content"]
    assert content["overall_score"] == 80
    assert content["grade"].startswith("80/100")


def test_audit_without_dimensions_is_rejected_not_invented(fake_llm):
    fake_llm.reply({"dimensions": [], "sdlc_score_justification": {"overall_summary": "x", "sdlc_stage_breakdown": []}})
    res = client.post("/api/v1/agents/readiness-audit", json={"input_text": SAMPLE_TEXT})
    assert res.status_code == 502
