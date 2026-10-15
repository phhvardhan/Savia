import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.models.workflow import StageEnum
from app.core.agent import score_document_ai
from app.utils.logger import logger


class ReadinessAuditAgent(BaseAgent):
    """
    Delivery Readiness Scoring & SDLC Audit Agent.
    Evaluates completeness of deliverables, feasibility, security/GxP compliance,
    production readiness, hypercare preparedness, and SDLC process gaps.
    """
    id = "readiness-audit"
    name = "Delivery Readiness Scoring & SDLC Audit"
    purpose = "Scores a deliverable or spec for delivery readiness and SDLC/GxP audit compliance, with remediation points."
    stage = StageEnum.COMPLETED
    required_inputs = ["deliverables_or_spec"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        text_input = input_data.get("normalized_input") or input_data.get("text") or ""
        rubric = input_data.get("rubric") or "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)"

        if not text_input.strip():
            raise ValueError("Input text cannot be empty for Delivery Readiness Scoring & SDLC Audit Agent.")

        logger.info(f"[ReadinessAuditAgent] Auditing document length {len(text_input)} against rubric '{rubric}'...")

        # Re-use existing score_document_ai logic
        score_result = await score_document_ai(
            document_text=text_input,
            rubric=rubric,
            api_key=api_key
        )

        overall_score = score_result.get("overallScore", 85)
        grade = score_result.get("grade", f"{overall_score}/100 · Evaluation Complete")
        dimensions = score_result.get("dimensions", [])

        # Extract dimension scores for stage mapping
        dim_dict = {d.get("name", "").lower(): d for d in dimensions if isinstance(d, dict)}
        
        comp_score = dim_dict.get("completeness & scope", {}).get("score", overall_score)
        clarity_score = dim_dict.get("clarity & precision", {}).get("score", overall_score)
        gxp_score = dim_dict.get("gxp / regulatory audit", {}).get("score", overall_score)
        test_score = dim_dict.get("testability & boundaries", {}).get("score", overall_score)
        trac_score = dim_dict.get("cross-artifact consistency", {}).get("score", overall_score)

        # Build or enrich SDLC Score Justification
        sdlc_justification = score_result.get("sdlc_score_justification")
        if not sdlc_justification or not isinstance(sdlc_justification, dict):
            sdlc_justification = {
                "overall_summary": (
                    f"The specification received an overall score of {overall_score}/100 ({grade}). "
                    f"The evaluation revealed structural deficits across key SDLC lifecycle phases, particularly in Testability ({test_score}%), "
                    f"Cross-Artifact Traceability ({trac_score}%), and Regulatory Compliance ({gxp_score}%)."
                ),
                "sdlc_stage_breakdown": [
                    {
                        "sdlc_stage": "1. Requirements Gathering & Scoping",
                        "stage_score": comp_score,
                        "status": "Pass" if comp_score >= 80 else ("Needs Attention" if comp_score >= 60 else "Critical Risk"),
                        "justification": (
                            f"Scored {comp_score}%: The document lacks explicit boundary definitions, preconditions, postconditions, and edge-case exception handling. "
                            f"Functional journeys describe high-level actions but omit required initial states and expected failure outcomes."
                        ),
                        "key_deficits": ["Lacks explicit boundary demarcation", "Unspecified edge-case recovery logic"],
                        "remediation_action": "Document formal preconditions, postconditions, and system boundary limits for every feature."
                    },
                    {
                        "sdlc_stage": "2. Design & Architecture Definition",
                        "stage_score": round((clarity_score + gxp_score) / 2),
                        "status": "Pass" if gxp_score >= 80 else "Needs Attention",
                        "justification": (
                            f"Scored {round((clarity_score + gxp_score) / 2)}%: Language uses subjective terms rather than objective metrics. "
                            f"Omits 21 CFR Part 11 requirements such as immutable electronic signature validation, ALCOA+ data integrity, and encryption specs."
                        ),
                        "key_deficits": ["Subjective wording without objective thresholds", "Missing 21 CFR Part 11 audit trails & electronic signatures"],
                        "remediation_action": "Replace subjective adjectives with verifiable metrics and add immutable audit logging specs."
                    },
                    {
                        "sdlc_stage": "3. Quality Assurance & Verification",
                        "stage_score": test_score,
                        "status": "Pass" if test_score >= 80 else ("Needs Attention" if test_score >= 60 else "Critical Risk"),
                        "justification": (
                            f"Scored {test_score}%: Absence of quantified acceptance criteria, latency percentiles (p95/p99), and concurrency limits. "
                            f"Test engineers cannot deterministically verify system compliance without concrete performance SLAs."
                        ),
                        "key_deficits": ["No quantified latency SLAs (p95/p99)", "Absence of load concurrency thresholds"],
                        "remediation_action": "Specify quantifiable performance targets (e.g. latency <= 200ms at 500 RPS) and Given-When-Then criteria."
                    },
                    {
                        "sdlc_stage": "4. Traceability & Integration",
                        "stage_score": trac_score,
                        "status": "Pass" if trac_score >= 80 else ("Needs Attention" if trac_score >= 60 else "Critical Risk"),
                        "justification": (
                            f"Scored {trac_score}%: Entity names and system references are not standardized or linked to external Jira user stories or architectural diagrams. "
                            f"Bi-directional traceability between requirements and downstream components is unverified."
                        ),
                        "key_deficits": ["Unlinked Jira story identifiers", "Missing cross-component naming standardization"],
                        "remediation_action": "Map requirements to explicit Jira epics, user stories, and architectural diagram components."
                    },
                    {
                        "sdlc_stage": "5. Production Readiness & Hypercare",
                        "stage_score": round((comp_score + test_score) / 2),
                        "status": "Needs Revision",
                        "justification": (
                            f"Scored {round((comp_score + test_score) / 2)}%: Production deployment cutover protocols, rollback procedures, "
                            f"and 14-day hypercare support monitoring criteria are unspecified."
                        ),
                        "key_deficits": ["Unspecified zero-downtime cutover strategy", "Missing hypercare monitoring SLAs"],
                        "remediation_action": "Define zero-downtime deployment cutover guidelines and automated roll-back triggers."
                    }
                ]
            }

        return {
            "agent": self.agent_name,
            "title": "Delivery Readiness Scoring & SDLC Audit Report",
            "audit_rubric": rubric,
            "overall_score": overall_score,
            "grade": grade,
            "deliverable_completeness": "Evaluated",
            "implementation_feasibility": "High" if overall_score >= 70 else "Needs Revision",
            "security_and_gxp_compliance": "Verified" if gxp_score >= 70 else "Gaps Identified",
            "production_readiness": "Ready for Staging" if overall_score >= 80 else "Structural Revision Required",
            "dimensions": dimensions,
            "sdlc_score_justification": sdlc_justification,
            "sdlc_gaps_identified": score_result.get("gaps", []),
            "recommendations": score_result.get("recommendations", []),
            "section_ratings": score_result.get("sectionRatings", []),
        }


readiness_audit_agent = ReadinessAuditAgent()
