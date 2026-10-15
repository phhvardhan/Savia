from app.agents.base import BaseAgent
from app.agents.mom_agent import mom_agent
from app.agents.agile_stories_agent import agile_stories_agent
from app.agents.solution_analyzer_agent import solution_analyzer_agent
from app.agents.gap_analysis_agent import gap_analysis_agent
from app.agents.ddl3_agent import ddl3_agent
from app.agents.kdd_dab_agent import kdd_dab_agent
from app.agents.change_impact_agent import change_impact_agent
from app.agents.test_agent import test_agent
from app.agents.readiness_audit_agent import readiness_audit_agent

# Every agent, in the order the UI and recommender list them. Add new agents here.
AGENTS = [
    mom_agent,
    agile_stories_agent,
    solution_analyzer_agent,
    gap_analysis_agent,
    ddl3_agent,
    kdd_dab_agent,
    change_impact_agent,
    test_agent,
    readiness_audit_agent,
]

AGENT_MAP = {agent.id: agent for agent in AGENTS}

__all__ = ["BaseAgent", "AGENTS", "AGENT_MAP"]
