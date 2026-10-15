from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent


class FutureAgentRegistry:
    """
    Registry for future expansion agents described in SAVIA specification.
    These agents remain inactive by default until explicitly enabled/configured.
    """
    AVAILABLE_FUTURE_AGENTS = [
        {"id": "change-impact", "name": "Change Impact Assessment & Interdependency Matrix"},
        {"id": "kdd-dab", "name": "KDD Package for DAB"},
        {"id": "gap-analysis", "name": "Requirement Gap Analysis & RTM"},
        {"id": "readiness-audit", "name": "Delivery Readiness Scoring & SDLC Audit"},
    ]

    def list_future_agents(self) -> List[Dict[str, str]]:
        return self.AVAILABLE_FUTURE_AGENTS


future_agent_registry = FutureAgentRegistry()
