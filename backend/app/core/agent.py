from typing import List, Optional
from app.core.llm import call_llm, parse_json
from app.core.text import FILE_HEADER_RE, fit_text

__all__ = ["call_llm", "parse_json", "fit_text", "FILE_HEADER_RE", "generate_jira_stories_ai"]


async def generate_jira_stories_ai(
    source_context: str,
    sprint: str = "Sprint 25",
    team: str = "Engineering & Product",
    project_key: Optional[str] = None,
    options: Optional[List[str]] = None,
) -> dict:
    sample_text = fit_text(source_context, 10000) if source_context else ""
    p_key = (project_key or "PROJ").strip().upper()

    system = (
        "You are an expert Agile Product Owner and Principal Scrum Master in an enterprise software organization. "
        "You convert approved stakeholder meeting minutes, transcripts, and requirement briefs into INVEST-compliant "
        "User Stories with testable Given/When/Then acceptance criteria.\n\n"
        f"TARGET SPRINT: {sprint}\n"
        f"ASSIGNED TEAM: {team}\n"
        f"PROJECT KEY: {p_key}\n\n"
        "CRITICAL INSTRUCTION:\n"
        "Generate 4 to 6 high-quality, actionable user stories derived DIRECTLY AND EXCLUSIVELY from the provided source context. "
        "Do NOT invent payment reconciliation or invoice matching stories unless the source material is explicitly about invoice reconciliation. "
        f"Each story must have a jira_issue_key following the format '{p_key}-101', '{p_key}-102', etc.\n\n"
        "RESPOND ONLY WITH A VALID JSON OBJECT matching this exact schema:\n"
        "{\n"
        '  "stories": [\n'
        '    {\n'
        '       "id": "story-1",\n'
        f'       "jira_issue_key": "{p_key}-101",\n'
        '       "title": "Brief, active summary of the capability",\n'
        '       "description": "As a [role], I want [capability], so that [business benefit].",\n'
        '       "acceptance_criteria": [\n'
        '          "Given [precondition], When [action is performed], Then [observable outcome]",\n'
        '          "Given [edge condition], When [action], Then [graceful handling or alert]"\n'
        '       ],\n'
        '       "priority": "High" | "Medium" | "Low",\n'
        '       "story_points": 2 | 3 | 5 | 8,\n'
        '       "sprint": "' + sprint + '",\n'
        '       "team": "' + team + '",\n'
        '       "dependencies": ["e.g. Depends on API endpoint definition"],\n'
        '       "assumptions": ["e.g. Stakeholders agree on authentication protocol"],\n'
        '       "status": "draft"\n'
        '    }\n'
        '  ],\n'
        '  "criteria_summary": [\n'
        '    {"id": "crit-1", "story_title": str, "criterion": str, "status": "Ready" | "Needs Review"}\n'
        '  ],\n'
        '  "dependencies_summary": [\n'
        '    {"id": "dep-1", "source": str, "target": str, "type": "Blocks" | "Depends on", "impact": "High" | "Medium"}\n'
        '  ],\n'
        '  "assumptions_summary": [\n'
        '    {"id": "assump-1", "text": str, "category": "Technical" | "Business" | "Compliance", "status": "Verified" | "Open Question"}\n'
        '  ]\n'
        "}"
    )

    user = f"SOURCE MATERIAL TO DECOMPOSE INTO USER STORIES:\n\n{sample_text}"
    return await call_llm(system, user, expected_type=dict)
