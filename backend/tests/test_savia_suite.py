import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agents import agile_stories_agent, ddl3_agent, mom_agent, test_agent
from app.core.llm import LLMError, LLMTruncated, call_structured, parse_json
from app.core.quality import assess, unsupported_figures
from app.agents.schemas import AgileStoriesOutput
from app.main import app
from app.models.workflow import ApprovalStatus, StageEnum
from app.orchestration.orchestrator import build_plan
from app.orchestration.stage_manager import GateError, stage_manager
from app.orchestration.workflow_engine import workflow_engine

client = TestClient(app)

STORIES = {
    "epics": ["User Management"],
    "user_stories": [{"user_story_id": "US-001", "title": "Manage user roles", "acceptance_criteria": [],
                      "story_points": "3", "requirement_ids": ["REQ-001"]}],
}


@pytest.mark.parametrize("filename, kind", [
    ("requirements.txt", "txt"), ("spec.docx", "doc"), ("doc.pdf", "pdf"), ("meeting.wav", "audio"), ("call.mp4", "video"),
])
def test_ingestion_detects_type(filename, kind):
    with patch("app.services.document_parser.extract_text_from_file", return_value="System must allow OAuth2 login."):
        res = client.post("/api/v1/ingestion/upload", files={"file": (filename, b"bytes", "application/octet-stream")})
    assert res.status_code == 200, res.text
    assert res.json()["input_type"] == kind
    assert "OAuth2" in res.json()["full_normalized_text"]


def test_upload_size_limit(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    res = client.post("/api/v1/ingestion/upload", files={"file": ("big.txt", b"x", "text/plain")})
    assert res.status_code == 413


def test_mom_numbers_decisions_and_actions(fake_llm):
    fake_llm.reply({"discussion_summary": "Deploy plan", "attendees": ["Ana"], "key_points": [],
                    "requirements_identified": [], "decisions_finalized": ["Deploy Friday"],
                    "action_items": [{"action": "Configure S3", "owner": "John"}], "open_questions": []})
    result = asyncio.run(mom_agent.run({"text": "We decided to deploy on Friday. John configures S3."}))
    assert result["decisions_finalized"][0]["decision_id"] == "DEC-001"
    assert result["action_items"][0]["assignee"] == "John"
    assert result["attendees"] == [{"name": "Ana", "role": None}]


def test_stories_are_not_padded_with_invented_criteria(fake_llm):
    fake_llm.reply(STORIES)
    result = asyncio.run(agile_stories_agent.run({"text": "REQ-001 Admins manage roles."}))
    story = result["user_stories"][0]
    assert story["acceptance_criteria"] == []
    assert story["story_points"] == 3


def test_invalid_output_is_retried_with_the_errors(fake_llm):
    fake_llm.reply({"epics": "not a list"}, STORIES)
    result = asyncio.run(call_structured("system", "user", AgileStoriesOutput))
    assert result["user_stories"][0]["title"] == "Manage user roles"
    assert len(fake_llm.calls) == 2
    assert "DID NOT MATCH THE REQUIRED SCHEMA" in fake_llm.calls[1][1]


def test_output_that_never_validates_raises(fake_llm):
    fake_llm.reply({"epics": "still wrong"})
    with pytest.raises(LLMError):
        asyncio.run(call_structured("system", "user", AgileStoriesOutput, retries=1))


def test_truncated_answer_is_an_error_not_a_repair(monkeypatch):
    from app.core import llm

    async def post(target, system, user, max_tokens, json_mode):
        return llm.Completion('{"a": [1, 2', "fake", "fake", "length", 1, 1)

    monkeypatch.setattr(llm, "targets", lambda: [llm.Target("fake", "http://x", {}, "fake")])
    monkeypatch.setattr(llm, "_post", post)
    with pytest.raises(LLMTruncated):
        asyncio.run(llm.complete("s", "u"))


def test_pinned_provider_has_no_fallback(monkeypatch):
    from app.core import llm
    monkeypatch.setenv("LLM_PROVIDER", "azure_openai")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_x")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://apim.example.com")
    assert [t.provider for t in llm.targets()] == ["azure_openai"]


def test_ddl3_refuses_empty_input():
    with pytest.raises(ValueError):
        asyncio.run(ddl3_agent.run({"text": ""}))


def test_ddl3_does_not_invent_methods_or_codes(fake_llm):
    fake_llm.reply({"title": "Spec", "functional_flow": ["Receive: order arrives"],
                    "validation_rules": ["Qty must be positive"], "api_requirements": ["POST /orders"]})
    doc = asyncio.run(ddl3_agent.run({"text": "Orders arrive and must have positive quantity."}))
    assert doc["functional_flow"][0] == {"title": "Receive", "description": "order arrives", "step": 1}
    assert doc["validation_rules"][0] == {"condition": "Qty must be positive", "rule_id": "VAL-001"}
    assert doc["api_requirements"][0]["method"] == "POST"
    assert doc["design_id"] == "DES-FD-001"


def test_test_coverage_is_computed(fake_llm):
    fake_llm.reply({"test_cases": [{"title": "t", "test_steps": ["s"], "requirement_id": "REQ-001", "type": "uat"}]})
    result = asyncio.run(test_agent.run({"text": "REQ-001 login. REQ-002 logout."}))
    assert result["test_summary"]["coverage_percentage"] == 50
    assert result["test_summary"]["untested_ids"] == ["REQ-002"]
    assert result["test_cases"][0]["type"] == "UAT"


def test_long_input_is_condensed_not_truncated(fake_llm, monkeypatch):
    monkeypatch.setenv("LLM_INPUT_CHARS", "200")
    monkeypatch.setenv("LLM_CHUNK_CHARS", "150")
    tail_fact = "REQ-099 The archive must be kept for 7 years."
    text = ("Filler sentence about nothing. " * 20) + tail_fact
    fake_llm.reply({"notes": [tail_fact]}, {"notes": [tail_fact]}, {"notes": [tail_fact]},
                   {"notes": [tail_fact]}, {"notes": [tail_fact]}, STORIES)
    asyncio.run(agile_stories_agent.run({"text": text}))
    assert "REQ-099" in fake_llm.calls[-1][1]


def test_quality_flags_invented_figures_and_dangling_ids():
    content = {"summary": "Latency under 200 ms for 5,000 users", "links": ["US-007"]}
    report = assess(content, "Latency must stay under 200 ms. US-001 login.", {}, ("TC",))
    assert report["unsupported_figures"] == ["5,000 users"]
    assert report["dangling_references"] == ["US-007"]
    assert unsupported_figures({"x": "Due 2026-01-31"}, "deadline 2026-01-31") == []


def test_parse_json_strips_fences():
    assert asyncio.run(parse_json('```json\n{"summary": "ok"}\n```'))["summary"] == "ok"


def test_only_approved_upstream_is_consumed(fake_llm):
    session = workflow_engine.create_workflow(title="Chain", normalized_input="REQ-001 Admins manage roles.")
    fake_llm.reply(STORIES)
    first = client.post("/api/v1/agents/agile-stories", json={"workflow_id": session.workflow_id}).json()

    fake_llm.reply({"test_cases": [{"title": "t", "test_steps": ["s"], "user_story_id": "US-001"}]})
    unapproved = client.post("/api/v1/agents/test", json={"workflow_id": session.workflow_id}).json()
    assert unapproved["upstream_unapproved"] == ["agile-stories"]
    assert "US-001" in unapproved["quality"]["dangling_references"]
    assert "USER STORIES" not in fake_llm.calls[-1][1]

    res = client.post(f"/api/v1/workflows/{session.workflow_id}/approve",
                      json={"artifact_id": first["artifact_id"], "user_id": "lead"})
    assert res.status_code == 200 and res.json()["status"] == "approved"

    fake_llm.reply({"test_cases": [{"title": "t", "test_steps": ["s"], "user_story_id": "US-001"}]})
    approved = client.post("/api/v1/agents/test", json={"workflow_id": session.workflow_id}).json()
    assert approved["upstream_used"] == [first["artifact_id"]]
    assert approved["quality"]["dangling_references"] == []
    assert "USER STORIES" in fake_llm.calls[-1][1]
    artifact = workflow_engine.get_artifact(approved["artifact_id"])
    assert artifact.traceability.user_story_ids == ["US-001"]
    assert artifact.traceability.upstream_artifact_ids == [first["artifact_id"]]


def test_advance_is_blocked_until_outputs_are_approved(fake_llm):
    session = workflow_engine.create_workflow(title="Gate", normalized_input="REQ-001 x")
    fake_llm.reply(STORIES)
    run = client.post("/api/v1/agents/agile-stories", json={"workflow_id": session.workflow_id}).json()
    blocked = client.post(f"/api/v1/workflows/{session.workflow_id}/advance", json={"target_stage": "ddl3"})
    assert blocked.status_code == 409
    client.post(f"/api/v1/workflows/{session.workflow_id}/approve", json={"artifact_id": run["artifact_id"]})
    moved = client.post(f"/api/v1/workflows/{session.workflow_id}/advance", json={"target_stage": "ddl3"})
    assert moved.status_code == 200 and moved.json()["current_stage"] == "ddl3"


def test_edit_creates_a_pending_version(fake_llm):
    session = workflow_engine.create_workflow(title="Edit", normalized_input="REQ-001 x")
    fake_llm.reply(STORIES)
    run = client.post("/api/v1/agents/agile-stories", json={"workflow_id": session.workflow_id}).json()
    client.post(f"/api/v1/workflows/{session.workflow_id}/approve", json={"artifact_id": run["artifact_id"]})
    edited = client.post(f"/api/v1/workflows/artifacts/{run['artifact_id']}/apply-edit",
                         json={"section": "epics", "value": ["Access"]}).json()
    assert edited["version"] == 2
    assert edited["approval_status"] == "pending"
    assert edited["content"]["epics"] == ["Access"]


def test_approve_without_outputs_is_a_conflict():
    session = workflow_engine.create_workflow(title="Empty")
    res = client.post(f"/api/v1/workflows/{session.workflow_id}/approve", json={})
    assert res.status_code == 409


def test_versions_are_sequential():
    session = workflow_engine.create_workflow(title="Versions")
    a = workflow_engine.save_artifact(session.workflow_id, "mom", StageEnum.MOM, {"summary": "1"})
    b = workflow_engine.save_artifact(session.workflow_id, "mom", StageEnum.MOM, {"summary": "2"})
    assert (a.version, b.version) == (1, 2)
    assert workflow_engine.get_workflow(session.workflow_id).outputs["mom"] == {"summary": "2"}


def test_background_run_completes(fake_llm):
    fake_llm.reply(STORIES)
    with TestClient(app) as live:
        started = live.post("/api/v1/agents/agile-stories/runs", json={"input_text": "REQ-001 Admins manage roles."})
        assert started.status_code == 202
        run_id = started.json()["id"]
        for _ in range(100):
            run = live.get(f"/api/v1/agents/runs/{run_id}").json()
            if run["status"] in ("done", "failed"):
                break
            time.sleep(0.05)
    assert run["status"] == "done", run
    assert run["result"]["content"]["user_stories"][0]["user_story_id"] == "US-001"


def test_background_run_reports_failure(fake_llm):
    fake_llm.reply(LLMError("provider down"))
    with TestClient(app) as live:
        run_id = live.post("/api/v1/agents/mom/runs", json={"input_text": "notes"}).json()["id"]
        for _ in range(100):
            run = live.get(f"/api/v1/agents/runs/{run_id}").json()
            if run["status"] in ("done", "failed"):
                break
            time.sleep(0.05)
    assert run["status"] == "failed"
    assert "provider down" in run["error"]


@patch("app.orchestration.orchestrator.call_llm", new_callable=AsyncMock, side_effect=RuntimeError("offline"))
def test_keyword_fallback_recommendations(_llm):
    cases = {
        ("Meeting transcript discussion", "audio"): "mom",
        ("SDLC audit report for GxP compliance and delivery readiness scoring", "txt"): "readiness-audit",
        ("Requirement gap analysis and traceability matrix (RTM)", "txt"): "gap-analysis",
        ("Cross-platform change impact assessment and interdependency matrix", "txt"): "change-impact",
        ("Architecture dossier for KDD package and Design Authority Board (DAB) review", "txt"): "kdd-dab",
    }
    for (text, kind), expected in cases.items():
        body = client.post("/api/v1/savia/recommend", json={"raw_text": text, "input_type": kind}).json()
        assert body["primary_agent"] == expected
        assert body["source"] == "keyword"
        assert isinstance(body["plan"], list)


def test_plan_orders_by_dependencies():
    recommended = [
        {"agent": "test", "confidence": 0.9, "matched": True},
        {"agent": "agile-stories", "confidence": 0.8, "matched": True},
        {"agent": "mom", "confidence": 0.7, "matched": True},
    ]
    plan = build_plan(recommended, [])
    assert [p["agent"] for p in plan] == ["mom", "agile-stories", "test"]
    assert plan[0]["approval_needed_before_next"] is True
    assert plan[2]["after"] == ["agile-stories"]


def test_dashboard_reports_real_counts():
    body = client.get("/api/v1/savia/dashboard").json()
    assert body["total_workflows"] == len(workflow_engine.list_workflows())
    assert all(c["value"].isdigit() for c in body["counters"])


def test_auth_required_blocks_anonymous_calls(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    assert client.get("/api/v1/agents").status_code == 401
    assert client.get("/api/v1/workflows/brand/fonts/none.otf").status_code == 404


def test_gate_error_on_foreign_artifact():
    one = workflow_engine.create_workflow(title="A")
    two = workflow_engine.create_workflow(title="B")
    art = workflow_engine.save_artifact(two.workflow_id, "mom", StageEnum.MOM, {"summary": "x"})
    with pytest.raises(GateError):
        stage_manager.approve(one, art, "lead")
    assert workflow_engine.get_artifact(art.artifact_id).approval_status == ApprovalStatus.PENDING
