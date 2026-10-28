from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.schemas import SolutionOutput
from app.models.workflow import StageEnum
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
    id = "solution-analyzer"
    name = "Solution Analyzer & Blueprint"
    purpose = "Takes a problem statement or discovery input and proposes a solution blueprint: approach, components, integrations, risks and a phased roadmap."
    stage = StageEnum.REQUIREMENTS
    required_inputs = ["problem_statement"]
    output_model = SolutionOutput

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.source_text(input_data).strip():
            raise ValueError("Input text cannot be empty for the Solution Analyzer Agent.")
        source = await self.source(input_data)
        logger.info(f"[SolutionAnalyzerAgent] Designing a solution from {len(source)} chars")
        return await self.generate(SYSTEM, f"PROBLEM INPUT:\n{source}")


solution_analyzer_agent = SolutionAnalyzerAgent()
