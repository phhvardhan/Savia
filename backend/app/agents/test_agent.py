import re
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.schemas import TestOutput
from app.core.quality import ids_in
from app.models.workflow import StageEnum
from app.utils.logger import logger

SYSTEM = (
    "You are an Enterprise Lead QA Architect and Automated Testing Director. "
    "Your objective is to generate end-to-end test suites based strictly on the provided requirements, "
    "user stories, and DDL3 architecture design specifications.\n\n"
    "CRITICAL QUALITY & GROUNDING PRINCIPLES:\n"
    "1. Ground all test cases strictly in the supplied requirements, user stories, and DDL3 architecture specifications.\n"
    "2. Generate balanced test coverage:\n"
    "   - Positive / Happy Path: Verification of primary business journeys and successful state transitions.\n"
    "   - Negative / Exception Handling: Verification of validation error thresholds, missing inputs, and unauthorized actions.\n"
    "   - Boundary / Edge Conditions: Boundary checks (e.g. character limits, batch limits, timeouts).\n"
    "3. Every test step must be actionable, numbered, and specific. Preconditions and expected results must be crisp and verifiable.\n"
    "4. Organize test cases into an orchestrated scenario-stitched Test Plan (e.g. Customer Authentication -> Data Inquiry -> Exception Recovery).\n"
    "5. requirement_id, user_story_id and design_id must be IDs that appear in the input or the approved upstream outputs; use null when there is none.\n\n"
    "OUTPUT JSON SPECIFICATION:\n"
    "Return valid JSON matching this exact schema:\n"
    "{\n"
    '  "test_summary": {\n'
    '    "total_tests": int,\n'
    '    "fit_count": int,\n'
    '    "uat_count": int,\n'
    '    "focus_areas": ["Authentication & Authorization", "Data Retrieval", "Error Resilience"]\n'
    '  },\n'
    '  "test_inventory": [\n'
    '    {\n'
    '      "inventory_id": "INV-001",\n'
    '      "type": "FIT" | "UAT",\n'
    '      "category": "API Integration" | "Security & Auth" | "Business Workflow" | "UI Validation",\n'
    '      "description": "Specific coverage description",\n'
    '      "traceability": "REQ-001 / US-001 / DES-001"\n'
    '    }\n'
    '  ],\n'
    '  "test_cases": [\n'
    '    {\n'
    '      "test_case_id": "TC-001",\n'
    '      "title": "Descriptive test case title",\n'
    '      "type": "FIT" | "UAT",\n'
    '      "category": "Positive" | "Negative" | "Boundary",\n'
    '      "requirement_id": "REQ-001",\n'
    '      "user_story_id": "US-001",\n'
    '      "design_id": "DES-001",\n'
    '      "preconditions": ["System is active", "User has valid session"],\n'
    '      "test_steps": ["Submit request with valid identifier", "Verify response status 200 and schema validity"],\n'
    '      "test_data": "Concrete payload or query parameter example",\n'
    '      "expected_result": "Detailed observable and verifiable outcome",\n'
    '      "priority": "High" | "Medium" | "Low",\n'
    '      "status": "Not Executed"\n'
    '    }\n'
    '  ],\n'
    '  "test_plan": {\n'
    '    "plan_id": "TP-001",\n'
    '    "title": "End-to-End Orchestrated Test Execution Plan",\n'
    '    "scenarios": [\n'
    '      {\n'
    '        "scenario_id": "SC-001",\n'
    '        "name": "Scenario Title (e.g. End-to-End Order Lookup)",\n'
    '        "description": "Description of the end-to-end execution journey",\n'
    '        "execution_order": 1,\n'
    '        "stitched_test_cases": ["TC-001", "TC-002"]\n'
    '      }\n'
    '    ]\n'
    '  },\n'
    '  "open_questions": ["<Any test ambiguity, unstated preconditions, or missing SLA threshold from the input>"]\n'
    "}"
)


class TestAgent(BaseAgent):
    id = "test"
    name = "TEST — End-to-end Test Preparation"
    purpose = "Produces a test inventory and FIT/UAT test cases from approved designs or user stories."
    stage = StageEnum.TESTING
    required_inputs = ["approved_design_or_user_stories"]
    consumes = ("agile-stories", "ddl3")
    defines = ("TC", "INV", "TP", "SC")
    output_model = TestOutput

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        source = await self.source(input_data)
        upstream = self.upstream_block(
            input_data, {"agile-stories": "USER STORIES & ACCEPTANCE CRITERIA", "ddl3": "DDL3 DESIGN SPECIFICATION"}
        )
        if not (source.strip() or upstream):
            raise ValueError("No requirements, user stories, or design artifacts provided for Test Agent.")
        user = f"REQUIREMENTS TEXT:\n{source}\n\n{upstream}".strip()
        logger.info(f"[TestAgent] Writing test cases from {len(user)} chars")
        data = await self.generate(SYSTEM, user)

        fit_count = uat_count = 0
        for idx, tc in enumerate(data["test_cases"]):
            tc["test_case_id"] = tc.get("test_case_id") or f"TC-{idx + 1:03d}"
            tc.setdefault("status", "Not Executed")
            if "UAT" in str(tc.get("type") or "").upper():
                tc["type"] = "UAT"
                uat_count += 1
            else:
                tc["type"] = "FIT"
                fit_count += 1

        targets = {i for i in ids_in(user) if re.match(r"^(US|REQ)-", i)}
        traced = {tc.get(key) for tc in data["test_cases"] for key in ("user_story_id", "requirement_id")}
        summary = data.get("test_summary") if isinstance(data.get("test_summary"), dict) else {}
        summary.update({
            "total_tests": len(data["test_cases"]),
            "fit_count": fit_count,
            "uat_count": uat_count,
            "coverage_percentage": round(100 * len(targets & traced) / len(targets)) if targets else None,
            "untested_ids": sorted(targets - traced),
        })
        summary.setdefault("focus_areas", [])
        data["test_summary"] = summary
        if not isinstance(data.get("test_plan"), dict):
            data["test_plan"] = {"scenarios": []}
        return data


test_agent = TestAgent()
