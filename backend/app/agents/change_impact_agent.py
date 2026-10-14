import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


class ChangeImpactAgent(BaseAgent):
    """
    Change Impact Assessment & Interdependency Matrix Agent.
    Evaluates cross-platform impacts (legacy vs target), cross-workstream dependencies,
    operational readiness, and formats an interdependency matrix.
    """
    @property
    def agent_name(self) -> str:
        return "change-impact"

    @property
    def stage(self) -> str:
        return "change_impact"

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        text_input = input_data.get("normalized_input") or input_data.get("text") or ""
        ddl3_input = input_data.get("ddl3") or input_data.get("outputs", {}).get("ddl3") or {}

        context_str = f"ARCHITECTURE & SYSTEM CONTEXT:\n{fit_text(text_input, 4000)}\n\n"
        if ddl3_input:
            context_str += f"DESIGN SPECIFICATION:\n{json.dumps(ddl3_input)[:3000]}\n\n"

        if not context_str.strip():
            raise ValueError("Input text cannot be empty for Change Impact Assessment Agent.")

        logger.info(f"[ChangeImpactAgent] Performing change impact assessment from context length {len(context_str)}...")

        system = (
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
            '    "readiness_score_pct": 82,\n'
            '    "cutover_strategy": "Zero-downtime blue/green deployment",\n'
            '    "rollback_protocol": "Instant DNS fallback",\n'
            '    "hypercare_requirements": ["24/7 Monitoring for 14 days"]\n'
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

        impact_data = await call_llm(system, context_str, api_key=api_key, expected_type=dict)

        if "cross_workstream_dependencies" not in impact_data:
            impact_data["cross_workstream_dependencies"] = []
        if "interdependency_matrix" not in impact_data:
            impact_data["interdependency_matrix"] = []

        return impact_data


change_impact_agent = ChangeImpactAgent()
