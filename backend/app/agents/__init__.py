from app.agents.base import BaseAgent
from app.agents.mom_agent import mom_agent
from app.agents.user_story_agent import user_story_agent
from app.agents.ddl3_agent import ddl3_agent
from app.agents.test_agent import test_agent
from app.agents.readiness_scoring_agent import readiness_scoring_agent
from app.agents.gap_analysis_agent import gap_analysis_agent
from app.agents.change_impact_agent import change_impact_agent
from app.agents.kdd_package_agent import kdd_package_agent

AGENT_MAP = {
    "mom": mom_agent,
    "user-stories": user_story_agent,
    "ddl3": ddl3_agent,
    "test": test_agent,
    "readiness-scoring": readiness_scoring_agent,
    "gap-analysis": gap_analysis_agent,
    "change-impact": change_impact_agent,
    "kdd-package": kdd_package_agent,
}

__all__ = [
    "BaseAgent",
    "mom_agent",
    "user_story_agent",
    "ddl3_agent",
    "test_agent",
    "readiness_scoring_agent",
    "gap_analysis_agent",
    "change_impact_agent",
    "kdd_package_agent",
    "AGENT_MAP",
]
