from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.workflow import StageEnum


# Appended to agent prompts: the values in a JSON schema example are shapes, not answers.
GROUNDING_RULES = (
    "\n\nGROUNDING RULES:\n"
    "- Use only facts from the input. Never invent figures, costs, effort, dates, percentages, scores or names.\n"
    "- If a field's value is not stated or clearly derivable from the input, use null (or [] for lists).\n"
    "- The example values in the schema show the format only; never copy them.\n"
)


class BaseAgent(ABC):
    """
    One SDLC agent. Subclasses set the class attributes below; the registry
    (app.agents.AGENTS), the recommender and POST /agents/{id} all read them,
    so adding an agent is one file plus one line in AGENTS.
    """

    id: str  # registry key and URL segment, e.g. "agile-stories"
    name: str  # display name
    purpose: str  # what it produces; the recommender's LLM picks agents on this
    stage: StageEnum  # lifecycle stage its artifact is saved under
    required_inputs: List[str] = ["normalized_text"]

    @property
    def agent_name(self) -> str:
        return self.id

    @staticmethod
    def source_text(input_data: Dict[str, Any]) -> str:
        """The user's input as text, whichever key the caller used."""
        return input_data.get("normalized_input") or input_data.get("text") or ""

    @abstractmethod
    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute agent logic and return a structured JSON dictionary.
        Must ground output in input_data without hallucinating unmentioned attributes.
        """
