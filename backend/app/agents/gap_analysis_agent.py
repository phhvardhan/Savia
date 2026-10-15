import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, GROUNDING_RULES
from app.models.workflow import StageEnum
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


class GapAnalysisAgent(BaseAgent):
    """
    Requirement Gap Analysis & RTM.
    Provides end-to-end traceability, standard vs custom gap identification,
    and highlights unmet requirements with timeline/budget impact analysis.
    """
    id = "gap-analysis"
    name = "Requirement Gap Analysis & RTM"
    purpose = "Compares requirements against what exists or is specified, producing a gap list and requirements traceability matrix (RTM)."
    stage = StageEnum.REQUIREMENTS
    required_inputs = ["business_objectives_and_specs"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        text_input = input_data.get("normalized_input") or input_data.get("text") or ""
        stories_input = input_data.get("agile_stories") or input_data.get("outputs", {}).get("agile_stories") or {}
        ddl3_input = input_data.get("ddl3") or input_data.get("outputs", {}).get("ddl3") or {}

        context_str = f"BUSINESS REQUIREMENTS:\n{fit_text(text_input, 4000)}\n\n"
        if stories_input:
            context_str += f"USER STORIES:\n{json.dumps(stories_input)[:3000]}\n\n"
        if ddl3_input:
            context_str += f"DDL3 DESIGN SPEC:\n{json.dumps(ddl3_input)[:3000]}\n\n"

        if not context_str.strip():
            raise ValueError("Input text cannot be empty for Requirement Gap Analysis & RTM Agent.")

        logger.info(f"[GapAnalysisAgent] Analyzing requirement gaps and building RTM from context length {len(context_str)}...")

        system = (
            "You are an Enterprise Lead Business Systems Analyst and RTM Specialist. "
            "Perform Requirement Gap Analysis & generate a Traceability Matrix (RTM).\n\n"
            "REQUIREMENTS & CAPABILITIES:\n"
            "1. Build End-to-End Traceability mapping: Business Objective -> Requirement -> User Story -> Technical Component -> Test Case.\n"
            "2. Identify Standard vs. Custom Gaps in the requirements.\n"
            "3. Highlight Unmet Requirements and estimate their potential impact on project timelines (in weeks) and budget (in $ / effort).\n\n"
            "Return valid JSON matching this exact schema:\n"
            "{\n"
            '  "title": "Requirement Gap Analysis & Requirements Traceability Matrix (RTM)",\n'
            '  "summary": "Executive summary of requirement coverage and gap findings",\n'
            '  "traceability_matrix": [\n'
            '    {\n'
            '      "req_id": "REQ-001",\n'
            '      "business_objective": "...",\n'
            '      "requirement_description": "...",\n'
            '      "user_story_id": "US-001",\n'
            '      "technical_component": "...",\n'
            '      "test_case_id": "TC-001",\n'
            '      "status": "Fully Covered" | "Partially Covered" | "Unmet"\n'
            '    }\n'
            '  ],\n'
            '  "gap_classification": [\n'
            '    {\n'
            '      "gap_id": "GAP-001",\n'
            '      "feature_area": "...",\n'
            '      "gap_type": "Standard Out-of-the-Box" | "Custom Extension",\n'
            '      "description": "...",\n'
            '      "recommendation": "..."\n'
            '    }\n'
            '  ],\n'
            '  "unmet_requirements_and_impact": [\n'
            '    {\n'
            '      "unmet_req_id": "REQ-002",\n'
            '      "description": "...",\n'
            '      "timeline_impact_weeks": <number only if the input states it, else null>,\n'
            '      "budget_impact_effort": "<only if the input states cost or effort, else null>",\n'
            '      "risk_level": "High" | "Medium" | "Low",\n'
            '      "mitigation_strategy": "..."\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        rtm_data = await call_llm(system + GROUNDING_RULES, context_str, api_key=api_key, expected_type=dict)

        if "traceability_matrix" not in rtm_data:
            rtm_data["traceability_matrix"] = []
        if "gap_classification" not in rtm_data:
            rtm_data["gap_classification"] = []
        if "unmet_requirements_and_impact" not in rtm_data:
            rtm_data["unmet_requirements_and_impact"] = []

        return rtm_data


gap_analysis_agent = GapAnalysisAgent()
