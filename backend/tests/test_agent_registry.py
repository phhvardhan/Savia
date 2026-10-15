from fastapi.testclient import TestClient
from app.agents import AGENTS, AGENT_MAP
from app.main import app
from app.models.workflow import StageEnum
from app.orchestration.orchestrator import AGENT_PURPOSES, ALL_AGENTS

client = TestClient(app)


def test_every_agent_declares_its_metadata():
    assert len(AGENT_MAP) == len(AGENTS), "duplicate agent id"
    for agent in AGENTS:
        assert agent.id and agent.name and agent.purpose, agent
        assert isinstance(agent.stage, StageEnum), agent.id


def test_recommender_sees_every_agent():
    assert [aid for aid, _, _ in ALL_AGENTS] == [a.id for a in AGENTS]
    assert set(AGENT_PURPOSES) == set(AGENT_MAP)


def test_agents_route_lists_and_guards():
    listed = client.get("/api/v1/agents").json()
    assert [a["id"] for a in listed] == [a.id for a in AGENTS]
    assert client.post("/api/v1/agents/nope", json={"input_text": "x"}).status_code == 404
    # Empty input is refused rather than invented.
    session = client.post("/api/v1/agents/mom", json={"input_text": " ", "bypass_approval": True})
    assert session.status_code in (400, 422), session.text


def test_names_match_the_frontend():
    """One nomenclature: ids and names come from the frontend's AGENT_META."""
    import re
    from pathlib import Path
    ts = (Path(__file__).parents[2] / "frontend/src/lib/savia.ts").read_text(encoding="utf-8")
    block = ts[ts.index("export const AGENT_META"):]
    frontend = dict(re.findall(r"\n  '?([a-z0-9-]+)'?: \{\s*label: '[^']*',\s*full: '([^']*)'", block))
    assert {a.id: a.name for a in AGENTS} == frontend
