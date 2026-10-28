from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.rubrics import RUBRIC_CONFIGS
from app.agents.schemas import AuditOutput
from app.models.workflow import StageEnum
from app.utils.logger import logger

DEFAULT_RUBRIC = "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)"
RUBRIC_KEYWORDS = (
    (("iso", "25010"), "ISO/IEC 25010 Software Quality Standard"),
    (("gxp", "audit", "regulatory"), "GxP Audit & Regulatory Compliance Benchmark"),
    (("agile", "lean", "invest"), "Agile Lean Spec & Acceptance Criteria Benchmark"),
)


def resolve_rubric(rubric: str) -> str:
    if rubric in RUBRIC_CONFIGS:
        return rubric
    lowered = rubric.lower()
    for terms, name in RUBRIC_KEYWORDS:
        if any(t in lowered for t in terms):
            return name
    return DEFAULT_RUBRIC


def grade_for(score: int) -> str:
    if score >= 90:
        label = "Exemplary Specification (Sign-off Ready)"
    elif score >= 80:
        label = "Strong Enterprise Specification (Minor Gaps to Address)"
    elif score >= 70:
        label = "Adequate Specification (Revision Recommended)"
    else:
        label = "Incomplete Specification (Structural Revision Required)"
    return f"{score}/100 · {label}"


def weighted_score(dimensions: List[Dict[str, Any]]) -> int:
    total_weight = sum(d["weight"] for d in dimensions)
    if not total_weight:
        return round(sum(d["score"] for d in dimensions) / len(dimensions))
    return round(sum(d["score"] * d["weight"] for d in dimensions) / total_weight)


class ReadinessAuditAgent(BaseAgent):
    id = "readiness-audit"
    name = "Delivery Readiness Scoring & SDLC Audit"
    purpose = "Scores a deliverable or spec for delivery readiness and SDLC/GxP audit compliance, with remediation points."
    stage = StageEnum.COMPLETED
    required_inputs = ["deliverables_or_spec"]
    consumes = ("agile-stories", "ddl3", "test")
    defines = ("GAP", "REC", "CRIT")
    output_model = AuditOutput

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.source_text(input_data).strip():
            raise ValueError("Input text cannot be empty for Delivery Readiness Scoring & SDLC Audit Agent.")
        rubric = resolve_rubric(input_data.get("rubric") or DEFAULT_RUBRIC)
        rubric_conf = RUBRIC_CONFIGS[rubric]
        dim_spec_text = "\n".join(f"- {d['name']} (Weight: {d['weight']}%): {d['desc']}" for d in rubric_conf["default_dimensions"])
        source = await self.source(input_data)
        upstream = self.upstream_block(
            input_data, {"agile-stories": "USER STORIES", "ddl3": "DESIGN SPECIFICATION", "test": "TEST CASES"}
        )
        logger.info(f"[ReadinessAuditAgent] Auditing {len(source)} chars against '{rubric}'")

        system = (
            "You are an expert Enterprise Software Quality Auditor and Lead Regulatory Assessor. "
            "You evaluate technical specifications, requirements documents, and architecture briefs against rigorous quality rubrics.\n\n"
            f"EVALUATION RUBRIC: {rubric}\n"
            f"BENCHMARK STANDARD: {rubric_conf['benchmark']}\n\n"
            f"EVALUATION DIMENSIONS TO ASSESS:\n{dim_spec_text}\n\n"
            "STRICT EVALUATION INSTRUCTIONS:\n"
            "1. GROUNDED IN REAL INPUT: Evaluate strictly based on the text provided. Do NOT use canned or hardcoded numbers.\n"
            "2. DYNAMIC DIMENSION SCORING: For each dimension listed above, assign an honest integer score (0-100) and rating "
            "('Strong' if score >= 80, 'Adequate' if 70-79, 'Needs Attention' if < 70) with a substantive summary explaining the score based directly on quotes or missing items from the document.\n"
            "3. CRITERIA EVALUATION: Generate 4 to 6 criteria specific to this document and rubric, with status ('Pass' | 'Partial' | 'Fail') and concrete finding referencing actual document sections.\n"
            "4. GAPS: Identify 2 to 4 genuine gaps in the document (critical / warning / info) with specific issue and recommendation.\n"
            "5. RECOMMENDATIONS: Provide 3 to 4 prioritized actionable recommendations (High / Medium / Low) with dimension and impact.\n"
            "6. SECTION RATINGS: Identify 3 to 5 actual sections or topic areas from the document and score each (0-100) with badge 'Compliant' or 'Needs Review'.\n"
            "7. SDLC CYCLE JUSTIFICATION: Provide an explicit, thorough justification of the overall score formatted across 5 core SDLC lifecycle stages:\n"
            "   - Stage 1: Requirements Gathering & Scoping\n"
            "   - Stage 2: Design & Architecture Definition\n"
            "   - Stage 3: Quality Assurance & Verification\n"
            "   - Stage 4: Traceability & Integration\n"
            "   - Stage 5: Production Readiness & Hypercare\n\n"
            "RESPOND ONLY WITH A VALID JSON OBJECT matching this exact schema:\n"
            "{\n"
            '  "dimensions": [\n'
            '     {"id": str, "name": str, "score": int (0-100), "weight": int, "rating": "Strong" | "Adequate" | "Needs Attention", "summary": str}\n'
            '  ],\n'
            '  "sdlc_score_justification": {\n'
            '     "overall_summary": "Detailed overall justification explaining why the document received this score...",\n'
            '     "sdlc_stage_breakdown": [\n'
            '        {\n'
            '           "sdlc_stage": "1. Requirements Gathering & Scoping",\n'
            '           "stage_score": int (0-100),\n'
            '           "status": "Pass" | "Needs Attention" | "Critical Risk",\n'
            '           "justification": "Detailed explanation of why this SDLC stage scored low/high based on document text...",\n'
            '           "key_deficits": ["Deficit 1", "Deficit 2"],\n'
            '           "remediation_action": "Actionable steps to improve score in this stage"\n'
            '        }\n'
            '     ]\n'
            '  },\n'
            '  "sectionRatings": [\n'
            '     {"name": str, "score": int (0-100), "badge": "Compliant" | "Needs Review", "badgeColor": "bg-green-100 text-green-700" | "bg-amber-100 text-amber-800"}\n'
            '  ],\n'
            '  "criteria": [\n'
            '     {"id": str, "dimension": str, "criterion": str, "status": "Pass" | "Partial" | "Fail", "finding": str}\n'
            '  ],\n'
            '  "gaps": [\n'
            '     {"id": str, "title": str, "severity": "critical" | "warning" | "info", "section": str, "issue": str, "recommendation": str}\n'
            '  ],\n'
            '  "recommendations": [\n'
            '     {"id": str, "title": str, "dimension": str, "priority": "High" | "Medium" | "Low", "action": str, "impact": str}\n'
            '  ]\n'
            "}"
        )

        result = await self.generate(system, f"DOCUMENT CONTENT TO AUDIT:\n\n{source}\n\n{upstream}".strip())
        dimensions = result["dimensions"]
        for idx, d in enumerate(dimensions):
            d["id"] = d.get("id") or f"dim-{idx + 1}"
            d["rating"] = d.get("rating") or ("Strong" if d["score"] >= 80 else "Adequate" if d["score"] >= 70 else "Needs Attention")
        overall = weighted_score(dimensions)
        scores = {d["name"].lower(): d["score"] for d in dimensions}
        gxp = next((v for k, v in scores.items() if "gxp" in k or "regulatory" in k or "audit" in k), None)
        gaps = result.get("gaps") or []
        return {
            "agent": self.id,
            "title": "Delivery Readiness Scoring & SDLC Audit Report",
            "audit_rubric": rubric,
            "overall_score": overall,
            "grade": grade_for(overall),
            "implementation_feasibility": "High" if overall >= 70 else "Needs Revision",
            "security_and_gxp_compliance": None if gxp is None else "Verified" if gxp >= 70 else "Gaps Identified",
            "production_readiness": "Ready for Staging" if overall >= 80 else "Structural Revision Required",
            "critical_gaps_count": sum(1 for g in gaps if isinstance(g, dict) and g.get("severity") == "critical"),
            "dimensions": dimensions,
            "sdlc_score_justification": result["sdlc_score_justification"],
            "criteria": result.get("criteria") or [],
            "sdlc_gaps_identified": gaps,
            "recommendations": result.get("recommendations") or [],
            "section_ratings": result.get("sectionRatings") or [],
        }


readiness_audit_agent = ReadinessAuditAgent()
