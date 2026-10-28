import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.schemas import Ddl3Output
from app.models.workflow import StageEnum
from app.utils.logger import logger

HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH")


def _numbered(items: List[Any], prefix: str, key: str, text_key: str) -> List[Dict[str, Any]]:
    result = []
    for idx, item in enumerate(items):
        item = item if isinstance(item, dict) else {text_key: str(item)}
        item[key] = item.get(key) or f"{prefix}-{idx + 1:03d}"
        result.append(item)
    return result


def _flow(items: List[Any]) -> List[Dict[str, Any]]:
    result = []
    for idx, item in enumerate(items):
        if isinstance(item, str):
            title, _, description = item.partition(":")
            item = {"title": title.strip(), "description": description.strip() or item}
        item.setdefault("step", idx + 1)
        result.append(item)
    return result


def _apis(items: List[Any]) -> List[Dict[str, Any]]:
    result = []
    for item in items:
        item = item if isinstance(item, dict) else {"endpoint": str(item), "description": str(item)}
        if not item.get("method"):
            method, _, path = str(item.get("endpoint", "")).partition(" ")
            if method.upper() in HTTP_METHODS and path:
                item["method"], item["endpoint"] = method.upper(), path
            else:
                item["method"] = None
        result.append(item)
    return result


# What makes a technical or configuration design different from a functional one.
TYPE_FOCUS = {
    "technical": (
        "TECHNICAL DESIGN FOCUS:\n"
        "- Describe how the system is built, not only what it does: spell out each interface's request and response "
        "fields and list the data entities the system stores or passes, with their fields.\n"
        "- Only entities, fields and integrations the input implies; mark anything the input leaves open as an open question.\n\n"
    ),
    "config": (
        "CONFIGURATION DESIGN FOCUS:\n"
        "- Specify what is configurable rather than coded: each parameter, what it controls, where it applies and its "
        "value. Take a value only from the input; use null when the input does not state one.\n"
        "- Business rules become configuration rules; list which settings each rule depends on.\n\n"
    ),
}
TYPE_SCHEMA = {
    "technical": (
        '  "data_entities": [{"entity": "<name>", "fields": ["<field>"], "description": "<what it holds>"}],\n'
    ),
    "config": (
        '  "configuration_parameters": [{"parameter": "<name>", "description": "<what it controls>", '
        '"applies_to": "<rule, step or interface>", "value": "<value stated in the input, else null>"}],\n'
    ),
}


class Ddl3Agent(BaseAgent):
    id = "ddl3"
    name = "DDL3 (Design Document Lifecycle)"
    purpose = "Writes or updates a DDL3 detailed functional/technical design document from approved stories or architecture input."
    stage = StageEnum.DDL3
    required_inputs = ["approved_user_stories_or_architecture"]
    consumes = ("agile-stories", "solution-analyzer")
    defines = ("DES", "BR", "VAL")
    prompt_version = "3"
    output_model = Ddl3Output

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        document_type = str(input_data.get("document_type") or "functional_design").lower()
        use_case = input_data.get("use_case") or "create_functional_design"
        source = await self.source(input_data)
        upstream = self.upstream_block(
            input_data, {"agile-stories": "USER STORIES", "solution-analyzer": "SOLUTION BLUEPRINT"}
        )
        existing: Optional[dict] = input_data.get("existing_design_doc")
        if not (source.strip() or upstream or existing):
            raise ValueError("Supply approved requirements, user stories or an existing DDL3 document.")

        kind = "technical" if "technical" in document_type else "config" if "config" in document_type else "functional"
        design_id_prefix = (
            "DES-FD" if "functional" in document_type
            else "DES-TD" if "technical" in document_type
            else "DES-CFG" if "config" in document_type
            else "DES"
        )
        user = f"USE CASE: {use_case}\nDOCUMENT TYPE: {document_type}\n\nREQUIREMENTS:\n{source}\n\n{upstream}"
        if existing:
            user += f"\n\nEXISTING DESIGN DOC TO UPDATE:\n{json.dumps(existing, ensure_ascii=False)[:self.upstream_chars]}"
        logger.info(f"[Ddl3Agent] {use_case} / {document_type} from {len(user)} chars")

        system = (
            "You are an Enterprise Lead System Architect & DDL3 Specialist. "
            "Your role is to produce comprehensive Design Document Lifecycle (DDL3) specifications — "
            "functional designs, technical designs, and configuration specifications following WRIEF & Config standards.\n\n"
            "CRITICAL GROUNDING RULES:\n"
            "1. Generate the DDL3 specification STRICTLY and EXCLUSIVELY from the provided REQUIREMENTS and USER STORIES.\n"
            "2. Do NOT invent functionality or business rules that the input does not describe. API endpoints, error codes "
            "and field names are design proposals: derive each one from a step of the flow, keep them minimal, and never "
            "add a capability, integration or system the input does not mention.\n"
            "3. Extract the actual system objective, functional flows, business rules, validation rules, API requirements, "
            "and error handling scenarios directly from the user's input text.\n"
            "4. If the input describes an order tracking system, produce an order tracking spec. If it describes a payroll system, "
            "produce a payroll spec. NEVER substitute one domain for another.\n"
            "5. The title and purpose MUST reflect the actual system described in the requirements — not a generic placeholder.\n\n"
            "WRIEF CLASSIFICATION GUIDE:\n"
            "- Workflows: Business process orchestration engines, approval chains, state machines\n"
            "- Reports: Data aggregation, reconciliation, analytics, dashboards\n"
            "- Interfaces: REST/SOAP/gRPC API endpoints, file-based integrations, event streams\n"
            "- Extensions: Custom fields, coding blocks, enhancement points, user exits\n"
            "- Forms: UI screens, input forms, configuration panels\n\n"
            "TRACEABILITY:\n"
            "- Where the input or the approved stories carry IDs (REQ-, US-), set story_ids on every functional_flow step "
            "and business rule to the IDs it implements, exactly as written. Use [] only when the input has no IDs.\n\n"
            f"{TYPE_FOCUS.get(kind, '')}"
            "FUNCTIONAL FLOW INSTRUCTIONS:\n"
            "- Break down the system into sequential processing steps (minimum 3, maximum 8)\n"
            "- Each step must have a clear title and detailed description of what happens\n"
            "- Steps should flow logically from user input through processing to output/display\n\n"
            "BUSINESS RULES & VALIDATION:\n"
            "- Extract every business rule mentioned or implied in the requirements\n"
            "- Each business rule gets a unique ID (BR-001, BR-002, etc.)\n"
            "- Each validation rule gets a unique ID (VAL-001, VAL-002, etc.) with the specific error condition and error code\n\n"
            "API REQUIREMENTS:\n"
            "- Identify all API endpoints needed based on the functional flow\n"
            "- Specify HTTP method, endpoint path, and what each API does\n\n"
            "ERROR HANDLING:\n"
            "- Identify all error scenarios from validation rules, API failures, and edge cases\n"
            "- Specify how each error should be handled by the system\n\n"
            "Return valid JSON matching this exact schema:\n"
            "{\n"
            f'  "design_id": "{design_id_prefix}-001",\n'
            f'  "use_case": "{use_case}",\n'
            f'  "document_type": "{document_type}",\n'
            '  "title": "<Descriptive title derived from the actual requirements>",\n'
            '  "purpose": "<Clear statement of what the system does, derived from requirements>",\n'
            '  "scope": "<In-scope capabilities and out-of-scope exclusions based on requirements>",\n'
            '  "wrief_classification": {\n'
            '    "workflows": ["<Workflow components identified from requirements>"],\n'
            '    "reports": ["<Reporting/analytics components>"],\n'
            '    "interfaces": ["<API endpoints and integrations>"],\n'
            '    "extensions": ["<Custom fields, coding blocks, enhancements>"],\n'
            '    "forms": ["<UI screens and input forms>"]\n'
            '  },\n'
            '  "functional_flow": [\n'
            '    {"step": 1, "title": "<Step title>", "description": "<What happens in this step>", "story_ids": ["US-001"]},\n'
            '    {"step": 2, "title": "<Step title>", "description": "<What happens in this step>", "story_ids": []}\n'
            '  ],\n'
            '  "business_rules": [\n'
            '    {"rule_id": "BR-001", "rule": "<Business rule text>", "category": "<Category>", "story_ids": ["US-001"]}\n'
            '  ],\n'
            '  "validation_rules": [\n'
            '    {"rule_id": "VAL-001", "condition": "<Input condition>", "error_code": "<Error code>", "action": "<What happens>"}\n'
            '  ],\n'
            '  "api_requirements": [\n'
            '    {"method": "GET", "endpoint": "<API path>", "description": "<What this API does>", "request": "<Request params>", "response": "<Response contract>"}\n'
            '  ],\n'
            '  "error_handling": [\n'
            '    {"error": "<Error scenario>", "code": "<Error code>", "handling": "<How the system handles it>"}\n'
            '  ],\n'
            f"{TYPE_SCHEMA.get(kind, '')}"
            '  "open_questions": ["<Any unresolved items from the requirements>"]\n'
            "}"
        )

        doc = await self.generate(system, user.strip())
        doc["design_id"] = doc.get("design_id") or f"{design_id_prefix}-001"
        doc["use_case"] = doc.get("use_case") or use_case
        doc["document_type"] = doc.get("document_type") or document_type
        doc["functional_flow"] = _flow(doc["functional_flow"])
        doc["business_rules"] = _numbered(doc["business_rules"], "BR", "rule_id", "rule")
        doc["validation_rules"] = _numbered(doc["validation_rules"], "VAL", "rule_id", "condition")
        doc["api_requirements"] = _apis(doc["api_requirements"])
        doc["error_handling"] = [e if isinstance(e, dict) else {"error": str(e)} for e in doc["error_handling"]]
        extra = {"technical": "data_entities", "config": "configuration_parameters"}.get(kind)
        if extra:
            items = doc.get(extra)
            doc[extra] = [i if isinstance(i, dict) else {"entity" if kind == "technical" else "parameter": str(i)} for i in items] if isinstance(items, list) else []
        return doc


ddl3_agent = Ddl3Agent()
