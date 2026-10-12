from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.workflow import TraceabilityLink


class BaseAgent(ABC):
    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @property
    @abstractmethod
    def stage(self) -> str:
        pass

    @abstractmethod
    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute agent logic deterministically and return structured JSON dictionary.
        Must ground output in input_data without hallucinating unmentioned attributes.
        """
        pass
