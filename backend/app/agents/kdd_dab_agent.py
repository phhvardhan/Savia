import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, GROUNDING_RULES
from app.models.workflow import StageEnum
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


class KddDabAgent(BaseAgent):
    """
    KDD Package (Knowledge Design Document) for DAB Agent.
    Generates architecture dossiers tailored for Design Authority Board (DAB) review,
    architectural governance, decision frameworks, and audit compliance.
    """
    id = "kdd-dab"
    name = "KDD Package for DAB"
    purpose = "Assembles a Knowledge Design Document package for Design Authority Board (DAB) review from an architecture/design doc."
    stage = StageEnum.DDL3
    required_inputs = ["architecture_design_doc"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        text_input = input_data.get("normalized_input") or input_data.get("text") or ""
        ddl3_input = input_data.get("ddl3") or input_data.get("outputs", {}).get("ddl3") or {}

        context_str = f"ARCHITECTURE SPECIFICATION:\n{fit_text(text_input, 4000)}\n\n"
        if ddl3_input:
            context_str += f"DESIGN SPECIFICATION:\n{json.dumps(ddl3_input)[:3000]}\n\n"

        if not context_str.strip():
            raise ValueError("Input text cannot be empty for KDD Package for DAB Agent.")

        logger.info(f"[KddDabAgent] Generating DAB Dossier and KDD package from context length {len(context_str)}...")

        system = (
            "You are an Enterprise Lead Architect & Governance Director for the Design Authority Board (DAB). "
            "Develop a comprehensive KDD Package (Knowledge Design Document) tailored for DAB review.\n\n"
            "REQUIREMENTS & CAPABILITIES:\n"
            "1. Architecture Dossier tailored for DAB review.\n"
            "2. Architectural Governance, Decision-Making Frameworks, and Solution Rationales.\n"
            "3. Structured Documentation meeting enterprise compliance, regulatory, and audit standards.\n\n"
            "Return valid JSON matching this exact schema:\n"
            "{\n"
            '  "title": "KDD Package (Knowledge Design Document) for DAB Review",\n'
            '  "dab_submission_id": "DAB-KDD-001",\n'
            '  "executive_dossier": "High-level architectural overview for DAB board members",\n'
            '  "architectural_governance": {\n'
            '    "governance_status": "<e.g. Ready for Board Sign-off | Pending Decisions, judged from the input>",\n'
            '    "architectural_principles_evaluated": [\n'
            '      {"principle": "Cloud First & Microservices", "compliance": "Compliant"},\n'
            '      {"principle": "Zero-Trust Security & Encryption", "compliance": "Compliant"}\n'
            '    ]\n'
            '  },\n'
            '  "decision_making_framework": [\n'
            '    {\n'
            '      "decision_id": "ADR-001",\n'
            '      "decision_title": "Choice of Storage Backend",\n'
            '      "solution_rationale": "...",\n'
            '      "alternatives_considered": ["S3", "Local POSIX"],\n'
            '      "dab_review_recommendation": "Approve"\n'
            '    }\n'
            '  ],\n'
            '  "enterprise_compliance_and_audit": {\n'
            '    "gxp_audit_readiness": "Verified",\n'
            '    "data_sovereignty": "<as stated in the input, else null>",\n'
            '    "disaster_recovery_rto_rpo": "<as stated in the input, else null>"\n'
            '  }\n'
            "}"
        )

        kdd_data = await call_llm(system + GROUNDING_RULES, context_str, api_key=api_key, expected_type=dict)

        if "decision_making_framework" not in kdd_data:
            kdd_data["decision_making_framework"] = []

        return kdd_data


kdd_dab_agent = KddDabAgent()
