from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.models.workflow import StageEnum
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


SYSTEM = (
    "You are an enterprise solution architect. Read the problem the team describes and propose a solution.\n\n"
    "RULES:\n"
    "1. Keep what the input says apart from what you propose. 'problem' and 'constraints' come only from "
    "the input; quote or name what you saw. Design choices are proposals.\n"
    "2. Never invent figures (costs, savings, volumes, dates, headcount). If a figure is needed and not in "
    "the input, add a question to needs_info instead.\n"
    "3. Only name systems the input mentions, or mark them clearly as a suggestion in 'rationale'.\n"
    "4. Plain text values, no markdown.\n\n"
    "Return only JSON in this shape:\n"
    "{\n"
    '  "title": "Solution Blueprint: <short name>",\n'
    '  "executive_summary": "2-3 sentences: the problem and the proposed solution",\n'
    '  "problem": {"statement": "...", "evidence": ["what in the input shows it"], "affected": ["teams, users or systems"]},\n'
    '  "constraints": ["limits stated in the input (systems, compliance, timing)"],\n'
    '  "proposed_solution": {"approach": "...", "rationale": "why this fits the problem"},\n'
    '  "components": [{"name": "...", "purpose": "...", "new_or_existing": "New" | "Existing" | "Changed"}],\n'
    '  "integrations": [{"from": "...", "to": "...", "data": "...", "method": "API | event | file | manual"}],\n'
    '  "alternatives": [{"option": "...", "why_not": "..."}],\n'
    '  "risks": [{"risk": "...", "impact": "High" | "Medium" | "Low", "mitigation": "..."}],\n'
    '  "roadmap": [{"phase": "Phase 1", "scope": "...", "outcome": "..."}],\n'
    '  "needs_info": ["questions the team must answer, e.g. budget, volumes, deadlines"]\n'
    "}"
)


class SolutionAnalyzerAgent(BaseAgent):
    """Solution Analyzer: proposes a solution blueprint for the problem in the input."""

    id = "solution-analyzer"
    name = "Solution Analyzer & Blueprint"
    purpose = "Takes a problem statement or discovery input and proposes a solution blueprint: approach, components, integrations, risks and a phased roadmap."
    stage = StageEnum.REQUIREMENTS
    required_inputs = ["problem_statement"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        text = self.source_text(input_data)
        if not text.strip():
            raise ValueError("Input text cannot be empty for the Solution Analyzer Agent.")

        logger.info(f"[SolutionAnalyzerAgent] Designing a solution from input length {len(text)}...")
        result = await call_llm(SYSTEM, f"PROBLEM INPUT:\n{fit_text(text, 8000)}", api_key=api_key, expected_type=dict)

        for key in ("components", "integrations", "alternatives", "risks", "roadmap", "needs_info", "constraints"):
            result.setdefault(key, [])
        return result


solution_analyzer_agent = SolutionAnalyzerAgent()
