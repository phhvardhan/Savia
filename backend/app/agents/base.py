import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Type

from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.core.context import fit_source
from app.core.llm import call_structured
from app.models.workflow import StageEnum

GROUNDING_RULES = (
    "\n\nGROUNDING RULES:\n"
    "- Use only facts from the input. Never invent figures, costs, effort, dates, percentages, scores or names.\n"
    "- If a field's value is not stated or clearly derivable from the input, use null (or [] for lists).\n"
    "- The example values in the schema show the format only; never copy them.\n"
    "- Keep IDs that appear in the input (REQ-, US-, DES-, TC-) exactly as written and reference them where they apply.\n"
)


class AgentOutput(BaseModel):
    model_config = ConfigDict(extra="allow")


class BaseAgent(ABC):
    id: str
    name: str
    purpose: str
    stage: StageEnum
    required_inputs: List[str] = ["normalized_text"]
    consumes: Tuple[str, ...] = ()
    defines: Tuple[str, ...] = ()
    output_model: Type[BaseModel] = AgentOutput
    prompt_version: str = "2"
    upstream_chars: int = 12000

    @property
    def agent_name(self) -> str:
        return self.id

    @staticmethod
    def source_text(input_data: Dict[str, Any]) -> str:
        return input_data.get("normalized_input") or input_data.get("text") or ""

    async def source(self, input_data: Dict[str, Any], budget: int | None = None) -> str:
        return await fit_source(self.source_text(input_data), self.purpose, budget or settings.LLM_INPUT_CHARS)

    @staticmethod
    def upstream(input_data: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        return (input_data.get("upstream") or {}).get(agent_id) or {}

    def upstream_block(self, input_data: Dict[str, Any], labels: Dict[str, str]) -> str:
        blocks = []
        share = self.upstream_chars // max(len(labels), 1)
        for agent_id, label in labels.items():
            content = self.upstream(input_data, agent_id)
            if content:
                blocks.append(f"{label} (approved):\n{json.dumps(content, ensure_ascii=False)[:share]}")
        return "\n\n".join(blocks)

    async def generate(self, system: str, user: str) -> Dict[str, Any]:
        return await call_structured(system + GROUNDING_RULES, user, self.output_model)

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        ...
