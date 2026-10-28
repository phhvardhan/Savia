from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.schemas import KddOutput
from app.models.workflow import StageEnum
from app.utils.logger import logger

SYSTEM = (
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
    '    "gxp_audit_readiness": "<as evidenced by the input, else null>",\n'
    '    "data_sovereignty": "<as stated in the input, else null>",\n'
    '    "disaster_recovery_rto_rpo": "<as stated in the input, else null>"\n'
    '  }\n'
    "}"
)


class KddDabAgent(BaseAgent):
    id = "kdd-dab"
    name = "KDD Package for DAB"
    purpose = "Assembles a Knowledge Design Document package for Design Authority Board (DAB) review from an architecture/design doc."
    stage = StageEnum.DDL3
    required_inputs = ["architecture_design_doc"]
    consumes = ("ddl3", "solution-analyzer")
    defines = ("ADR", "DAB")
    output_model = KddOutput

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        source = await self.source(input_data)
        upstream = self.upstream_block(
            input_data, {"ddl3": "DESIGN SPECIFICATION", "solution-analyzer": "SOLUTION BLUEPRINT"}
        )
        if not (source.strip() or upstream):
            raise ValueError("Input text cannot be empty for KDD Package for DAB Agent.")
        user = f"ARCHITECTURE SPECIFICATION:\n{source}\n\n{upstream}".strip()
        logger.info(f"[KddDabAgent] Assembling the DAB package from {len(user)} chars")
        return await self.generate(SYSTEM, user)


kdd_dab_agent = KddDabAgent()
