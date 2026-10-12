import os
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.orchestration.workflow_engine import workflow_engine
from app.orchestration.stage_manager import stage_manager
from app.agents import (
    mom_agent, user_story_agent, ddl3_agent, test_agent,
    readiness_scoring_agent, gap_analysis_agent, change_impact_agent, kdd_package_agent
)
from app.models.workflow import StageEnum

client = TestClient(app)


# 1. Test TXT Ingestion
def test_01_txt_ingestion():
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("requirements.txt", b"System must allow users to log in using OAuth2.", "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "workflow_id" in data
    assert data["input_type"] == "txt"
    assert "OAuth2" in data["full_normalized_text"]


# 2. Test DOCX Ingestion Mock
def test_02_docx_ingestion():
    with patch("app.services.document_parser.extract_text_from_file", return_value="Functional design spec for invoice processing."):
        response = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("spec.docx", b"mock docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        assert response.status_code == 200
        assert response.json()["input_type"] == "doc"


# 3. Test PDF Ingestion Mock
def test_03_pdf_ingestion():
    with patch("app.services.document_parser.extract_text_from_file", return_value="PDF Content Mock: Architecture Blueprint"):
        response = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("doc.pdf", b"pdf bytes", "application/pdf")}
        )
        assert response.status_code == 200
        assert response.json()["input_type"] == "pdf"


# 4. Test Audio Ingestion Mock
def test_04_audio_ingestion():
    with patch("app.services.document_parser.extract_text_from_file", return_value="Speaker 1: Meeting transcript notes."):
        response = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("meeting.wav", b"audio bytes", "audio/wav")}
        )
        assert response.status_code == 200
        assert response.json()["input_type"] == "audio"


# 5. Test Video Ingestion Mock
def test_05_video_ingestion():
    with patch("app.services.document_parser.extract_text_from_file", return_value="Speaker 1: Video conference discussion."):
        response = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("recording.mp4", b"video bytes", "video/mp4")}
        )
        assert response.status_code == 200
        assert response.json()["input_type"] == "video"


# MOCK RESPONSES FOR OFFLINE TESTS
MOCK_MOM_RESPONSE = {
    "discussion_summary": "AWS Deployment planning discussion.",
    "decisions_finalized": ["Deploy to AWS on Friday"],
    "action_items": ["John will configure S3 bucket"],
    "key_points": ["Deployment timing"],
    "requirements_identified": ["AWS S3"],
    "open_questions": []
}

MOCK_USER_STORY_RESPONSE = {
    "epics": ["User Management"],
    "user_stories": [
        {
            "user_story_id": "US-001",
            "epic": "User Management",
            "title": "Manage user roles",
            "description": "Admin capability to manage access roles",
            "as_a": "admin",
            "i_want": "manage user roles",
            "so_that": "access is secured",
            "acceptance_criteria": [
                {"given": "Admin logged in", "when": "Role created", "then": "Role is saved"}
            ],
            "story_points": 3,
            "priority": "High",
            "dependencies": []
        }
    ]
}

MOCK_DDL3_FUNC_RESPONSE = {
    "design_id": "DES-001",
    "document_type": "functional_design",
    "title": "Email Notification Functional Design",
    "purpose": "Send password reset notification",
    "scope": "In-scope",
    "functional_requirements": [{"req_id": "REQ-001", "traceability": "US-001"}],
    "business_rules": [],
    "process_flow": [],
    "interfaces": [],
    "data_requirements": [],
    "non_functional_requirements": [],
    "assumptions": [],
    "dependencies": [],
    "open_questions": []
}

MOCK_TEST_RESPONSE = {
    "test_inventory": [{"inventory_id": "INV-001", "type": "FIT", "category": "MFA"}],
    "test_cases": [
        {
            "test_case_id": "TC-001",
            "title": "Log in with MFA",
            "type": "UAT",
            "requirement_id": "REQ-001",
            "user_story_id": "US-001",
            "design_id": "DES-001",
            "preconditions": [],
            "test_steps": ["Enter OTP"],
            "test_data": [],
            "expected_result": "Logged in",
            "priority": "High",
            "status": "Not Executed"
        }
    ],
    "test_plan": {"plan_id": "TP-001", "title": "Test Plan", "scenarios": []}
}

MOCK_SCORE_RESPONSE = {
    "overallScore": 88,
    "grade": "88/100 · Strong Enterprise Specification",
    "dimensions": [{"id": "dim-1", "name": "Completeness", "score": 90, "summary": "Complete"}],
    "gaps": [],
    "recommendations": [],
    "sectionRatings": []
}


# 6. Test MOM Generation
def test_06_mom_generation():
    with patch("app.agents.mom_agent.generate_mom", new_callable=AsyncMock, return_value=MOCK_MOM_RESPONSE):
        result = asyncio.run(mom_agent.run({"text": "Speaker 1: We decided to deploy to AWS on Friday."}))
        assert "summary" in result
        assert len(result.get("decisions_finalized", result.get("decisions", []))) >= 1


# 7. Test User Story Generation
def test_07_user_story_generation():
    with patch("app.agents.user_story_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_USER_STORY_RESPONSE):
        result = asyncio.run(user_story_agent.run({"text": "As an admin, I want to manage user roles so that access is secured."}))
        assert "epics" in result
        assert len(result["user_stories"]) >= 1


# 8. Test DDL3 Functional Design
def test_08_ddl3_functional_design():
    with patch("app.agents.ddl3_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_DDL3_FUNC_RESPONSE):
        result = asyncio.run(ddl3_agent.run({"text": "Functional requirement: System must send email notification.", "document_type": "functional_design"}))
        assert result["document_type"] == "functional_design"


# 9. Test Test Case Generation
def test_09_test_case_generation():
    with patch("app.agents.test_agent.call_llm", new_callable=AsyncMock, return_value=MOCK_TEST_RESPONSE):
        result = asyncio.run(test_agent.run({"text": "User Story: Log in with MFA."}))
        assert "test_cases" in result


# 10. Test Readiness Scoring Agent
def test_10_readiness_scoring_agent():
    with patch("app.agents.readiness_scoring_agent.score_document_ai", new_callable=AsyncMock, return_value=MOCK_SCORE_RESPONSE):
        result = asyncio.run(readiness_scoring_agent.run({"text": "Enterprise Specification Document for Audit"}))
        assert result["agent"] == "readiness-scoring"
        assert result["overall_score"] == 88


# 11. Test Gap Analysis Agent
def test_11_gap_analysis_agent():
    mock_gap = {
        "title": "Gap Analysis Report",
        "traceability_matrix": [{"req_id": "REQ-001", "status": "Fully Covered"}],
        "gap_classification": [],
        "unmet_requirements_and_impact": []
    }
    with patch("app.agents.gap_analysis_agent.call_llm", new_callable=AsyncMock, return_value=mock_gap):
        result = asyncio.run(gap_analysis_agent.run({"text": "Requirement gap analysis for legacy system vs target."}))
        assert "traceability_matrix" in result


# 12. Test Change Impact Agent
def test_12_change_impact_agent():
    mock_impact = {
        "title": "Change Impact Matrix",
        "cross_platform_impact_analysis": {"impact_level": "High"},
        "cross_workstream_dependencies": [],
        "interdependency_matrix": []
    }
    with patch("app.agents.change_impact_agent.call_llm", new_callable=AsyncMock, return_value=mock_impact):
        result = asyncio.run(change_impact_agent.run({"text": "Change impact evaluation for cloud migration."}))
        assert "cross_platform_impact_analysis" in result


# 13. Test KDD Package Agent
def test_13_kdd_package_agent():
    mock_kdd = {
        "title": "KDD Package for DAB",
        "dab_submission_id": "DAB-KDD-001",
        "architectural_governance": {"governance_status": "Ready"},
        "decision_making_framework": []
    }
    with patch("app.agents.kdd_package_agent.call_llm", new_callable=AsyncMock, return_value=mock_kdd):
        result = asyncio.run(kdd_package_agent.run({"text": "Architecture dossier for Design Authority Board review."}))
        assert result["dab_submission_id"] == "DAB-KDD-001"


# 14. Test SAVIA Agent Recommendations for All Agents
def test_14_savia_recommendations():
    res_mom = client.post("/api/v1/savia/recommend", json={"raw_text": "Meeting transcript discussion", "input_type": "audio"})
    assert res_mom.json()["primary_agent"] == "mom"

    res_audit = client.post("/api/v1/savia/recommend", json={"raw_text": "SDLC audit report for GxP compliance and delivery readiness scoring", "input_type": "txt"})
    assert res_audit.json()["primary_agent"] == "readiness-scoring"

    res_gap = client.post("/api/v1/savia/recommend", json={"raw_text": "Requirement gap analysis and traceability matrix (RTM)", "input_type": "txt"})
    assert res_gap.json()["primary_agent"] == "gap-analysis"

    res_change = client.post("/api/v1/savia/recommend", json={"raw_text": "Cross-platform change impact assessment and interdependency matrix", "input_type": "txt"})
    assert res_change.json()["primary_agent"] == "change-impact"

    res_kdd = client.post("/api/v1/savia/recommend", json={"raw_text": "Architecture dossier for KDD package and Design Authority Board (DAB) review", "input_type": "txt"})
    assert res_kdd.json()["primary_agent"] == "kdd-package"


# 15. Test Approval Gates
def test_15_approval_gates():
    session = workflow_engine.create_workflow(title="Approval Test")
    stage_manager.approve_stage(session, StageEnum.REQUIREMENTS, user_id="lead_ba")
    refreshed = workflow_engine.get_workflow(session.workflow_id)
    assert refreshed.approvals["requirements"]["status"] == "approved"


# 16. Test Workflow Progression
def test_16_workflow_progression():
    session = workflow_engine.create_workflow(title="Progression Test")
    stage_manager.approve_stage(session, StageEnum.REQUIREMENTS)
    success, reason, updated = stage_manager.advance_stage(session, StageEnum.MOM)
    assert success is True
    assert updated.current_stage == StageEnum.MOM


# 17. Test Invalid Workflow Transition Block
def test_17_invalid_workflow_transition():
    session = workflow_engine.create_workflow(title="Invalid Transition Test")
    can_adv, reason = stage_manager.can_advance(session, StageEnum.TESTING, bypass_approval=False)
    assert can_adv is False


# 18. Test Missing Input Handling
def test_18_missing_input_handling():
    result = asyncio.run(ddl3_agent.run({"text": ""}))
    assert result.get("status") == "clarification_required" or "title" in result


# 19. Test LLM Malformed JSON Handling
def test_19_malformed_json_handling():
    from app.core.agent import parse_json
    raw_json_with_markdown = "```json\n{\"summary\": \"Test summary\"}\n```"
    parsed = asyncio.run(parse_json(raw_json_with_markdown))
    assert parsed["summary"] == "Test summary"


# 20. Test Artifact Traceability Links
def test_20_artifact_traceability():
    session = workflow_engine.create_workflow(title="Traceability Session")
    artifact = workflow_engine.save_artifact(
        workflow_id=session.workflow_id,
        agent_name="user-stories",
        stage=StageEnum.USER_STORY,
        content={"user_stories": []}
    )
    retrieved = workflow_engine.get_artifact(artifact.artifact_id)
    assert retrieved.workflow_id == session.workflow_id
    assert retrieved.agent_name == "user-stories"
