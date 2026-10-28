from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.schemas import GapOutput
from app.models.workflow import StageEnum
from app.utils.logger import logger

SYSTEM = (
    "You are an Enterprise Lead Business Systems Analyst and RTM Specialist. "
    "Perform Requirement Gap Analysis & generate a Traceability Matrix (RTM).\n\n"
    "REQUIREMENTS & CAPABILITIES:\n"
    "1. Build End-to-End Traceability mapping: Business Objective -> Requirement -> User Story -> Technical Component -> Test Case.\n"
    "2. Identify Standard vs. Custom Gaps in the requirements.\n"
    "3. Highlight Unmet Requirements and state their impact on timelines and budget only where the input gives it.\n\n"
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


class GapAnalysisAgent(BaseAgent):
    id = "gap-analysis"
    name = "Requirement Gap Analysis & RTM"
    purpose = "Compares requirements against what exists or is specified, producing a gap list and requirements traceability matrix (RTM)."
    stage = StageEnum.REQUIREMENTS
    required_inputs = ["business_objectives_and_specs"]
    consumes = ("agile-stories", "ddl3", "test")
    defines = ("GAP",)
    output_model = GapOutput

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        source = await self.source(input_data)
        upstream = self.upstream_block(
            input_data, {"agile-stories": "USER STORIES", "ddl3": "DESIGN SPECIFICATION", "test": "TEST CASES"}
        )
        if not (source.strip() or upstream):
            raise ValueError("Input text cannot be empty for Requirement Gap Analysis & RTM Agent.")
        user = f"BUSINESS REQUIREMENTS:\n{source}\n\n{upstream}".strip()
        logger.info(f"[GapAnalysisAgent] Building the RTM from {len(user)} chars")
        return await self.generate(SYSTEM, user)


gap_analysis_agent = GapAnalysisAgent()
