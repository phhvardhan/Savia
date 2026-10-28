from typing import Any, Dict

from app.agents.base import BaseAgent
from app.agents.schemas import AgileStoriesOutput
from app.models.workflow import StageEnum
from app.utils.logger import logger

SYSTEM = (
    "You are an expert Agile Product Manager and Scrum Master. Convert requirements into Agile backlog artifacts.\n"
    "RULES:\n"
    "1. Create INVEST-compliant user stories (Independent, Negotiable, Valuable, Estimable, Small, Testable). "
    "Every story delivers one user-visible capability the input describes. Never write filler stories about a "
    "system or portal merely existing or being available: a requirement that only names the system is context for the epic, not a story.\n"
    "2. Write Given/When/Then acceptance criteria using only behaviour the input describes. Give every story a "
    "happy-path criterion and, where the input implies one (a rejection, a deadline, an invalid or unsupported "
    "input, a failure), a criterion for that case too. When the input names two outcomes (approve or reject), "
    "write one criterion per outcome. If the input gives no testable behaviour for a story, "
    "leave acceptance_criteria empty and add a question to open_questions.\n"
    "3. story_points: Fibonacci (1, 2, 3, 5, 8, 13), differentiated by each story's relative size, only when the "
    "scope is clear enough to size; otherwise null. priority: only when the input implies an order or "
    "importance; otherwise null. Never give every story the same value.\n"
    "4. Epics are themes that group two or more related stories, named after the input's own themes. A "
    "requirement that yields a single story belongs under a broader epic, not its own.\n"
    "5. requirement_ids: the REQ- IDs from the input or the approved minutes that the story implements. Every "
    "story that implements a requirement lists its ID; use [] only when the input has no matching REQ- ID.\n"
    "6. Do not invent requirements that the input does not mention. Put unresolved risks and decisions in "
    "open_questions.\n"
    "Return only JSON in this shape:\n"
    "{\n"
    '  "epics": ["<epic>"],\n'
    '  "user_stories": [\n'
    "    {\n"
    '      "user_story_id": "US-001",\n'
    '      "epic": "<epic>",\n'
    '      "title": "<story title>",\n'
    '      "description": "<story description>",\n'
    '      "as_a": "<role>",\n'
    '      "i_want": "<capability>",\n'
    '      "so_that": "<benefit>",\n'
    '      "acceptance_criteria": [{"given": "<state>", "when": "<event>", "then": "<outcome>"}],\n'
    '      "story_points": 3,\n'
    '      "priority": "High" | "Medium" | "Low" | null,\n'
    '      "dependencies": ["US-000"],\n'
    '      "requirement_ids": ["REQ-001"]\n'
    "    }\n"
    "  ],\n"
    '  "open_questions": ["<what the team must clarify>"]\n'
    "}"
)


class AgileStoriesAgent(BaseAgent):
    id = "agile-stories"
    name = "Agile User Stories & Backlog Epics"
    purpose = "Turns requirements, BRDs or meeting outcomes into INVEST user stories with Given/When/Then acceptance criteria."
    stage = StageEnum.USER_STORY
    required_inputs = ["approved_requirements_or_mom"]
    consumes = ("mom",)
    defines = ("US",)
    output_model = AgileStoriesOutput
    prompt_version = "3"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        source = await self.source(input_data)
        upstream = self.upstream_block(input_data, {"mom": "MINUTES OF MEETING"})
        if not (source.strip() or upstream):
            raise ValueError("No requirements or approved minutes to write user stories from.")
        user = f"REQUIREMENTS INPUT:\n{source}\n\n{upstream}".strip()
        logger.info(f"[AgileStoriesAgent] Writing stories from {len(user)} chars")
        data = await self.generate(SYSTEM, user)

        for idx, story in enumerate(data["user_stories"]):
            story["user_story_id"] = story.get("user_story_id") or f"US-{idx + 1:03d}"
        # Enforced here, not left to the model: identical sizing or priority on every story is a default, not an estimate.
        stories = data["user_stories"]
        if len(stories) >= 3:
            for field in ("story_points", "priority"):
                if len({s.get(field) for s in stories}) == 1:
                    for s in stories:
                        s[field] = None
        if not data["epics"]:
            data["epics"] = sorted({s["epic"] for s in data["user_stories"] if s.get("epic")})
        return data


agile_stories_agent = AgileStoriesAgent()
