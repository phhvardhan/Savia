import json
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.models.workflow import StageEnum
from app.core.agent import call_llm, fit_text
from app.utils.logger import logger


class Ddl3Agent(BaseAgent):
    """
    DDL3 Agent - Design Document Lifecycle Management.
    Manages full design document lifecycle for functional and technical specs (WRIEF & Config).
    
    Use Cases:
    1. Create functional design
    2. Create technical design
    3. Update DDL3 (FD & TD)
    4. Create Config DDL3
    5. Update Config DDL3
    """
    id = "ddl3"
    name = "DDL3 (Design Document Lifecycle)"
    purpose = "Writes or updates a DDL3 detailed functional/technical design document from approved stories or architecture input."
    stage = StageEnum.DDL3
    required_inputs = ["approved_user_stories_or_architecture"]

    async def run(self, input_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        document_type = input_data.get("document_type", "functional_design").lower()
        use_case = input_data.get("use_case") or "create_functional_design"
        
        text_input = input_data.get("normalized_input") or input_data.get("text") or ""
        stories_input = input_data.get("agile_stories") or input_data.get("outputs", {}).get("agile_stories") or {}
        existing_doc = input_data.get("existing_design_doc") or {}

        context_str = f"USE CASE: {use_case}\nDOCUMENT TYPE: {document_type}\n\nREQUIREMENTS:\n{fit_text(text_input, 6000)}\n\n"
        if stories_input:
            context_str += f"USER STORIES:\n{json.dumps(stories_input)[:3000]}\n\n"
        if existing_doc:
            context_str += f"EXISTING DESIGN DOC TO UPDATE:\n{json.dumps(existing_doc)[:3000]}\n\n"

        if not text_input and not stories_input and not existing_doc:
            return {
                "status": "clarification_required",
                "missing_information": ["Approved requirements, user stories, or existing DDL3 document"],
                "clarification_request": "Insufficient input provided to construct a DDL3 specification. Please supply approved requirements or user stories."
            }

        logger.info(f"[Ddl3Agent] Running DDL3 Agent (Use Case: '{use_case}', Doc Type: '{document_type}') length {len(context_str)}...")

        # Dynamic design ID prefix based on document type
        design_id_prefix = "DES-FD" if "functional" in document_type else "DES-TD" if "technical" in document_type else "DES-CFG" if "config" in document_type else "DES"

        system = (
            "You are an Enterprise Lead System Architect & DDL3 Specialist. "
            "Your role is to produce comprehensive Design Document Lifecycle (DDL3) specifications — "
            "functional designs, technical designs, and configuration specifications following WRIEF & Config standards.\n\n"
            
            "CRITICAL GROUNDING RULES:\n"
            "1. Generate the DDL3 specification STRICTLY and EXCLUSIVELY from the provided REQUIREMENTS and USER STORIES.\n"
            "2. Do NOT invent functionality, APIs, business rules, or system behaviors that are not described in the input.\n"
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
            '    {"step": 1, "title": "<Step title>", "description": "<What happens in this step>"},\n'
            '    {"step": 2, "title": "<Step title>", "description": "<What happens in this step>"}\n'
            '  ],\n'
            '  "business_rules": [\n'
            '    {"rule_id": "BR-001", "rule": "<Business rule text>", "category": "<Category>"}\n'
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
            '  "open_questions": ["<Any unresolved items from the requirements>"]\n'
            "}"
        )

        ddl3_doc = await call_llm(system, context_str, api_key=api_key, expected_type=dict)

        # Lightweight fallbacks — only fill in truly missing structural keys, never overwrite valid LLM output
        if "design_id" not in ddl3_doc:
            ddl3_doc["design_id"] = f"{design_id_prefix}-001"
        if "use_case" not in ddl3_doc:
            ddl3_doc["use_case"] = use_case
        if "document_type" not in ddl3_doc:
            ddl3_doc["document_type"] = document_type
        if "title" not in ddl3_doc or not ddl3_doc["title"]:
            ddl3_doc["title"] = "Design Specification Document"
        if "purpose" not in ddl3_doc or not ddl3_doc["purpose"]:
            ddl3_doc["purpose"] = "Functional and technical design specification generated from provided requirements."

        # Ensure functional_flow is a list of dicts (normalize string entries from older LLM responses)
        if "functional_flow" in ddl3_doc and isinstance(ddl3_doc["functional_flow"], list):
            normalized_flow = []
            for idx, item in enumerate(ddl3_doc["functional_flow"]):
                if isinstance(item, str):
                    # Parse "Title: Description" format
                    parts = item.split(":", 1)
                    normalized_flow.append({
                        "step": idx + 1,
                        "title": parts[0].strip(),
                        "description": parts[1].strip() if len(parts) > 1 else item
                    })
                elif isinstance(item, dict):
                    if "step" not in item:
                        item["step"] = idx + 1
                    normalized_flow.append(item)
            ddl3_doc["functional_flow"] = normalized_flow

        # Ensure business_rules is a list of dicts
        if "business_rules" in ddl3_doc and isinstance(ddl3_doc["business_rules"], list):
            normalized_rules = []
            for idx, item in enumerate(ddl3_doc["business_rules"]):
                if isinstance(item, str):
                    normalized_rules.append({
                        "rule_id": f"BR-{idx + 1:03d}",
                        "rule": item,
                        "category": "General"
                    })
                elif isinstance(item, dict):
                    if "rule_id" not in item:
                        item["rule_id"] = f"BR-{idx + 1:03d}"
                    normalized_rules.append(item)
            ddl3_doc["business_rules"] = normalized_rules

        # Ensure validation_rules is a list of dicts
        if "validation_rules" in ddl3_doc and isinstance(ddl3_doc["validation_rules"], list):
            normalized_vals = []
            for idx, item in enumerate(ddl3_doc["validation_rules"]):
                if isinstance(item, str):
                    normalized_vals.append({
                        "rule_id": f"VAL-{idx + 1:03d}",
                        "condition": item,
                        "error_code": f"ERR_{idx + 1:03d}",
                        "action": "Display validation error"
                    })
                elif isinstance(item, dict):
                    if "rule_id" not in item:
                        item["rule_id"] = f"VAL-{idx + 1:03d}"
                    normalized_vals.append(item)
            ddl3_doc["validation_rules"] = normalized_vals

        # Ensure api_requirements is a list of dicts
        if "api_requirements" in ddl3_doc and isinstance(ddl3_doc["api_requirements"], list):
            normalized_apis = []
            for idx, item in enumerate(ddl3_doc["api_requirements"]):
                if isinstance(item, dict):
                    # Normalize: some LLMs return {endpoint, description} without method
                    if "method" not in item:
                        endpoint_str = str(item.get("endpoint", ""))
                        if endpoint_str.upper().startswith(("GET ", "POST ", "PUT ", "DELETE ", "PATCH ")):
                            parts = endpoint_str.split(" ", 1)
                            item["method"] = parts[0].upper()
                            item["endpoint"] = parts[1] if len(parts) > 1 else endpoint_str
                        else:
                            item["method"] = "GET"
                    normalized_apis.append(item)
                elif isinstance(item, str):
                    normalized_apis.append({
                        "method": "GET",
                        "endpoint": item,
                        "description": item
                    })
            ddl3_doc["api_requirements"] = normalized_apis

        # Ensure error_handling is a list of dicts
        if "error_handling" in ddl3_doc and isinstance(ddl3_doc["error_handling"], list):
            normalized_errors = []
            for item in ddl3_doc["error_handling"]:
                if isinstance(item, dict):
                    normalized_errors.append(item)
                elif isinstance(item, str):
                    normalized_errors.append({
                        "error": item,
                        "code": "ERR_GENERAL",
                        "handling": item
                    })
            ddl3_doc["error_handling"] = normalized_errors

        return ddl3_doc


ddl3_agent = Ddl3Agent()
