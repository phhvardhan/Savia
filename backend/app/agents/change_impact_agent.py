from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.schemas import ChangeImpactOutput
from app.models.workflow import StageEnum
from app.utils.logger import logger

SYSTEM = (
    "You are an Enterprise Lead Change Architect & Transformation Director. "
    "Perform Change Impact Assessment & build an Interdependency Matrix.\n\n"
    "CAPABILITIES & INSTRUCTIONS:\n"
    "1. Cross-Platform Impact Analysis: Compare the current legacy platform against target architecture.\n"
    "2. Identify Cross-Workstream Dependencies & Potential Risks (Engineering, Data, Security, Ops, Business).\n"
    "3. Operational Readiness Evaluation to ensure seamless transition without downtime.\n"
    "4. Construct an Interdependency Matrix formatted for executive alignment.\n\n"
    "Return valid JSON matching this exact schema:\n"
    "{\n"
    '  "title": "Change Impact Assessment & Interdependency Matrix",\n'
    '  "executive_summary": "High-level summary of change scope and migration complexity",\n'
    '  "cross_platform_impact_analysis": {\n'
    '    "current_platform_state": "...",\n'
    '    "target_architecture_state": "...",\n'
    '    "impact_level": "High" | "Medium" | "Low",\n'
    '    "key_architectural_deltas": ["..."]\n'
    '  },\n'
    '  "cross_workstream_dependencies": [\n'
    '    {\n'
    '      "dep_id": "DEP-001",\n'
    '      "source_workstream": "Backend API",\n'
    '      "target_workstream": "Frontend React UI",\n'
    '      "dependency_description": "...",\n'
    '      "potential_risk": "...",\n'
    '      "risk_level": "High" | "Medium" | "Low"\n'
    '    }\n'
    '  ],\n'
    '  "operational_readiness_evaluation": {\n'
    '    "readiness_score_pct": <integer 0-100 only if the input gives readiness evidence, else null>,\n'
    '    "cutover_strategy": "<as stated in the input, else null>",\n'
    '    "rollback_protocol": "<as stated in the input, else null>",\n'
    '    "hypercare_requirements": ["<as stated in the input>"]\n'
    '  },\n'
    '  "interdependency_matrix": [\n'
    '    {\n'
    '      "component": "Authentication Gateway",\n'
    '      "depends_on": ["LDAP Service", "OAuth Provider"],\n'
    '      "impacted_by": ["Mobile App", "Web Dashboard"],\n'
    '      "criticality": "Critical"\n'
    '    }\n'
    '  ]\n'
    "}"
)


class ChangeImpactAgent(BaseAgent):
    id = "change-impact"
    name = "Change Impact Assessment & Interdependency Matrix"
    purpose = "Assesses the impact of a proposed change across systems and workstreams, producing an interdependency matrix."
    stage = StageEnum.DDL3
    required_inputs = ["current_and_target_architecture"]
    consumes = ("ddl3", "solution-analyzer")
    defines = ("DEP",)
    output_model = ChangeImpactOutput

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        source = await self.source(input_data)
        upstream = self.upstream_block(
            input_data, {"ddl3": "DESIGN SPECIFICATION", "solution-analyzer": "SOLUTION BLUEPRINT"}
        )
        if not (source.strip() or upstream):
            raise ValueError("Input text cannot be empty for Change Impact Assessment Agent.")
        user = f"ARCHITECTURE & SYSTEM CONTEXT:\n{source}\n\n{upstream}".strip()
        logger.info(f"[ChangeImpactAgent] Assessing change impact from {len(user)} chars")
        return await self.generate(SYSTEM, user)


change_impact_agent = ChangeImpactAgent()
