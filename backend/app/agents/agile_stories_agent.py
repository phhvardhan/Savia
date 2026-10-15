import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.models.workflow import StageEnum
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


class AgileStoriesAgent(BaseAgent):
    id = "agile-stories"
    name = "Agile User Stories & Backlog Epics"
    purpose = "Turns requirements, BRDs or meeting outcomes into INVEST user stories with Given/When/Then acceptance criteria."
    stage = StageEnum.USER_STORY
    required_inputs = ["approved_requirements_or_mom"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        requirements_text = input_data.get("normalized_input") or input_data.get("text") or ""
        mom_content = input_data.get("mom") or input_data.get("outputs", {}).get("mom") or {}

        context_str = f"REQUIREMENTS INPUT:\n{fit_text(requirements_text, 8000)}\n\n"
        if mom_content:
            context_str += f"MOM CONTEXT:\n{json.dumps(mom_content)}\n"

        if not context_str.strip():
            raise ValueError("No input text or MOM context provided for Agile User Story Agent.")

        logger.info(f"[AgileStoriesAgent] Generating INVEST user stories from context length {len(context_str)}...")

        system = (
            "You are an expert Agile Product Manager and Scrum Master. Convert approved requirements into Agile backlog artifacts.\n"
            "REQUIREMENTS & COMPLIANCE RULES:\n"
            "1. Create INVEST-compliant user stories (Independent, Negotiable, Valuable, Estimable, Small, Testable).\n"
            "2. Generate Given-When-Then BDD acceptance criteria objects.\n"
            "3. Assign story-point estimates (Fibonacci: 1, 2, 3, 5, 8, 13) for sprint planning.\n"
            "4. Organize stories under appropriate Epics.\n"
            "5. Ground all stories strictly in the provided input without inventing unmentioned requirements.\n"
            "Return valid JSON matching this exact schema:\n"
            "{\n"
            '  "epics": ["Epic Title 1", "Epic Title 2"],\n'
            '  "user_stories": [\n'
            '    {\n'
            '      "user_story_id": "US-001",\n'
            '      "epic": "Epic Title 1",\n'
            '      "title": "Clear user story title",\n'
            '      "description": "Comprehensive story description",\n'
            '      "as_a": "Role",\n'
            '      "i_want": "Capability",\n'
            '      "so_that": "Business value benefit",\n'
            '      "acceptance_criteria": [\n'
            '        {\n'
            '          "given": "Precondition state",\n'
            '          "when": "Action event occurs",\n'
            '          "then": "Expected outcome response"\n'
            '        }\n'
            '      ],\n'
            '      "story_points": 3,\n'
            '      "priority": "High" | "Medium" | "Low",\n'
            '      "dependencies": ["US-000"]\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        stories_data = await call_llm(system, context_str, api_key=api_key, expected_type=dict)

        # Fallback defaults if LLM omitted required keys
        if "epics" not in stories_data or not isinstance(stories_data["epics"], list):
            stories_data["epics"] = list(set(s.get("epic", "Core Platform") for s in stories_data.get("user_stories", []))) or ["General Requirements"]

        if "user_stories" not in stories_data or not isinstance(stories_data["user_stories"], list):
            stories_data["user_stories"] = []

        # Guarantee ID & structure for each story
        for idx, story in enumerate(stories_data["user_stories"]):
            if "user_story_id" not in story:
                story["user_story_id"] = f"US-{idx+1:03d}"
            if "acceptance_criteria" not in story or not story["acceptance_criteria"]:
                story["acceptance_criteria"] = [{
                    "given": "The user is authenticated on the system",
                    "when": f"The user requests {story.get('title', 'the feature')}",
                    "then": "The system processes the request and returns successful output"
                }]

        return stories_data


agile_stories_agent = AgileStoriesAgent()
