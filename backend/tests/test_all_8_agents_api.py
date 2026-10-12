import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_TEXT = "Enterprise software requirements and architecture specification for order fulfillment and inventory management."

MOCK_MOM = {"summary": "Meeting notes summary", "decisions": ["Approved"], "action_items": ["Action 1"], "key_points": ["Point 1"], "requirements_identified": ["Req 1"], "open_questions": []}
MOCK_STORIES = {"epics": ["Fulfillment"], "user_stories": [{"user_story_id": "US-001", "title": "Order Placement", "as_a": "user", "i_want": "place order", "so_that": "item is delivered", "acceptance_criteria": []}]}
MOCK_DDL3 = {"design_id": "DES-001", "document_type": "functional_design", "title": "Fulfillment Spec", "purpose": "Order routing"}
MOCK_TEST = {"test_inventory": [], "test_cases": [{"test_case_id": "TC-001", "title": "Place Order", "status": "Not Executed"}], "test_plan": {}}
MOCK_SCORE = {"overallScore": 85, "grade": "85/100", "dimensions": []}
MOCK_GAP = {"title": "Gap Analysis", "traceability_matrix": []}
MOCK_IMPACT = {"title": "Change Impact", "cross_platform_impact_analysis": {}}
MOCK_KDD = {"title": "KDD Package", "dab_submission_id": "DAB-001"}


def test_api_01_mom_agent():
    with patch("app.agents.mom_agent.generate_mom", new_callable=AsyncMock, return_value=MOCK_MOM):
        res = client.post("/api/v1/agents/mom", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "mom"


def test_api_02_user_stories_agent():
    with patch("app.agents.user_story_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_STORIES):
        res = client.post("/api/v1/agents/user-stories", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "user-stories"


def test_api_03_ddl3_agent():
    with patch("app.agents.ddl3_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_DDL3):
        res = client.post("/api/v1/agents/ddl3", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "ddl3"


def test_api_04_test_agent():
    with patch("app.agents.test_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_TEST):
        res = client.post("/api/v1/agents/test", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "test"


def test_api_05_readiness_scoring_agent():
    with patch("app.agents.readiness_scoring_agent.score_document_ai", new_callable=AsyncMock, return_value=MOCK_SCORE):
        res = client.post("/api/v1/agents/readiness-scoring", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "readiness-scoring"


def test_api_06_gap_analysis_agent():
    with patch("app.agents.gap_analysis_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_GAP):
        res = client.post("/api/v1/agents/gap-analysis", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "gap-analysis"


def test_api_07_change_impact_agent():
    with patch("app.agents.change_impact_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_IMPACT):
        res = client.post("/api/v1/agents/change-impact", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "change-impact"


def test_api_08_kdd_package_agent():
    with patch("app.agents.kdd_package_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_KDD):
        res = client.post("/api/v1/agents/kdd-package", json={"input_text": SAMPLE_TEXT, "bypass_approval": True})
        assert res.status_code == 200
        assert res.json()["agent_name"] == "kdd-package"
