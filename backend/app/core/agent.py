import re
import json
import os
import socket
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.utils.logger import logger

PREFERRED_GROQ_MODEL_PATTERNS = [
    "qwen/qwen3.8-27b",
    "qwen3.8",
    "groq/compound",
    "compound",
    "openai/gpt-oss-20b",
    "gpt-oss-20b",
    "groq/compound-mini",
    "compound-mini",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b",
    "llama3-8b",
    "llama",
    "qwen",
    "mixtral",
    "gemma",
]

EXCLUDED_PATTERNS = [
    "whisper",
    "guard",
    "arabic",
    "orpheus",
    "allam",
    "canopylabs",
    "safetensors",
    "vision",
    "120b",
]


def check_azure_connectivity(endpoint: str, timeout: float = 1.5) -> tuple:
    """Fast check (under 1.5s) whether the Azure host resolves and is reachable on network."""
    try:
        parsed = urlparse(endpoint)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not host:
            return False, "No valid hostname found in Azure endpoint"

        # 1. Fast DNS resolution
        addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not addr_info:
            return False, f"DNS resolution returned no addresses for {host}"

        # 2. Fast socket connection check
        sock = socket.socket(addr_info[0][0], socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(addr_info[0][4])
        sock.close()
        return True, "Reachable"
    except socket.gaierror as e:
        return False, f"DNS resolution failed for {host} (off corporate VPN/network): {e}"
    except (socket.timeout, TimeoutError):
        return False, f"Connection to {host}:{port} timed out after {timeout}s (Host blocked or off VPN)"
    except Exception as e:
        return False, f"Cannot connect to {host}:{port}: {e}"


async def determine_provider(override_key: Optional[str] = None) -> str:
    key = (override_key or "").strip()
    if key.startswith("gsk_"):
        return "groq"
    if key.startswith("sk-"):
        return "openai"

    configured = settings.LLM_PROVIDER.lower()
    if configured in ["groq", "openai", "azure_openai"]:
        return configured

    if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
        return "azure_openai"
    if settings.GROQ_API_KEY:
        return "groq"
    if settings.OPENAI_API_KEY:
        return "openai"

    return "azure_openai"


async def call_azure_openai(system: str, user: str, api_key: Optional[str] = None) -> str:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    key = api_key or settings.AZURE_OPENAI_API_KEY
    endpoint = (settings.AZURE_OPENAI_ENDPOINT or "").rstrip("/")
    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4o"
    api_version = settings.AZURE_OPENAI_API_VERSION or "2024-06-01"

    if not key or not endpoint:
        raise ValueError("No API key or endpoint configured for Azure OpenAI. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in the backend .env file.")

    # 1. Fast DNS & socket connectivity check (fails in ~15ms if off VPN)
    reachable, reason = check_azure_connectivity(endpoint, timeout=1.5)
    if not reachable:
        logger.warning(f"[LLM: Azure APIM] Host not reachable ({reason}). Fast aborting to trigger Groq fallback.")
        raise ConnectionError(f"Azure APIM host unreachable ({reason})")

    logger.info(f"[LLM: Azure APIM] Connected to {endpoint}. Dispatching request for deployment '{deployment}'...")

    payload = {
        "model": deployment,
        "max_tokens": 3000,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    headers_list = [
        {"Content-Type": "application/json", "api-key": key, "Ocp-Apim-Subscription-Key": key},
        {"Content-Type": "application/json", "Authorization": f"Bearer {key}", "api-key": key},
        {"Content-Type": "application/json", "api-key": key},
    ]

    # The J&J APIM serves the /openai/deployments/... route; the others 404 and only cost a round trip each
    candidate_urls = [
        f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}",
        f"{endpoint}/deployments/{deployment}/chat/completions?api-version={api_version}",
        f"{endpoint}/chat/completions?api-version={api_version}",
    ]

    last_error = None
    for url in candidate_urls:
        for headers in headers_list:
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=6, verify=False)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        logger.info(f"[LLM: Azure APIM] Success on '{url}'!")
                        return content
                else:
                    logger.warning(f"[LLM: Azure APIM] URL {url} returned HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"[LLM: Azure APIM] Connection attempt failed on '{url}': {e}")
                last_error = e

    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=key,
            azure_endpoint=endpoint,
            api_version=api_version,
            timeout=6.0,
        )
        resp = client.chat.completions.create(
            model=deployment,
            max_tokens=3000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"[LLM: Azure OpenAI] All attempts failed: {last_error or e}")
        raise ConnectionError(f"Failed to connect to Azure APIM ({endpoint}). Error: {last_error or e}")


async def call_groq(system: str, user: str, api_key: Optional[str] = None) -> str:
    from groq import Groq
    key = api_key or settings.GROQ_API_KEY
    if not key:
        raise ValueError("No API key configured. Please set your API key in the backend .env file.")

    client = Groq(api_key=key)

    candidate_models = []
    try:
        models_data = client.models.list().data
        for m in models_data:
            model_id = getattr(m, "id", "")
            active = getattr(m, "active", True)
            if active and not any(ex in model_id.lower() for ex in EXCLUDED_PATTERNS):
                candidate_models.append(model_id)

        def get_model_score(mid: str) -> int:
            for idx, pat in enumerate(PREFERRED_GROQ_MODEL_PATTERNS):
                if pat in mid.lower():
                    return idx
            return 99

        candidate_models.sort(key=get_model_score)
        logger.info(f"[LLM: Groq] Discovered & prioritized active models: {candidate_models}")
    except Exception as e:
        logger.warning(f"[LLM: Groq] Error fetching live models: {e}")

    if not candidate_models:
        candidate_models = ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama3-8b-8192", "gemma2-9b-it"]

    last_error = None
    for model_name in candidate_models:
        try:
            logger.info(f"[LLM: Groq] Sending request using live model '{model_name}'...")
            resp = client.chat.completions.create(
                model=model_name,
                max_tokens=4096,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            content = resp.choices[0].message.content or ""
            if content.strip():
                return content
        except Exception as e:
            logger.warning(f"[LLM: Groq] Model '{model_name}' failed: {e}")
            last_error = e

    if last_error:
        raise last_error
    raise ValueError("All available Groq models failed to respond.")


async def call_openai(system: str, user: str, api_key: Optional[str] = None) -> str:
    from openai import OpenAI
    key = api_key or settings.OPENAI_API_KEY
    model = settings.OPENAI_MODEL
    if not key:
        raise ValueError("No OpenAI API key configured. Please set OPENAI_API_KEY in backend .env file.")

    logger.info(f"[LLM: OpenAI] Sending request using model '{model}'...")
    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


async def parse_json(raw: str, expected_type=dict):
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as err:
        logger.warning(f"Initial JSON parse failed ({err}). Attempting json_repair...")
        try:
            import json_repair
            parsed = json_repair.loads(raw)
        except Exception as repair_err:
            logger.warning(f"json_repair library failed ({repair_err}). Trying heuristic repair...")
            repaired = raw
            if not repaired.endswith("}") and not repaired.endswith("]"):
                last_comma = repaired.rfind(",")
                if last_comma > 0:
                    repaired = repaired[:last_comma]
                if expected_type is list:
                    repaired += "]"
                else:
                    repaired += "}"
            try:
                parsed = json.loads(repaired)
            except Exception:
                raise err

    if expected_type is dict:
        if isinstance(parsed, list):
            if len(parsed) > 0 and isinstance(parsed[0], dict):
                return parsed[0]
            raise TypeError(f"Expected dict, got list: {parsed}")
        if not isinstance(parsed, dict):
            raise TypeError(f"Expected dict, got {type(parsed).__name__}")
    elif expected_type is list:
        if isinstance(parsed, dict):
            for k in ["user_stories", "stories", "data"]:
                if k in parsed and isinstance(parsed[k], list):
                    return parsed[k]
            return [parsed]
        if not isinstance(parsed, list):
            raise TypeError(f"Expected list, got {type(parsed).__name__}")

    return parsed


async def call_llm(system: str, user: str, api_key: Optional[str] = None, expected_type=dict):
    """
    LLM Provider Pipeline:
    1. FIRST: Check and connect to Azure OpenAI (if configured).
    2. If connecting to Azure OpenAI is NOT possible (off VPN, DNS failure, timeout, or any exception):
       ONLY THEN connect to Groq Cloud logic as fallback.
    3. If Groq also fails, fallback to OpenAI if configured.
    """
    # Check for explicit override key
    if api_key and api_key.startswith("gsk_"):
        content = await call_groq(system, user, api_key)
        return await parse_json(content, expected_type=expected_type)
    elif api_key and api_key.startswith("sk-"):
        content = await call_openai(system, user, api_key)
        return await parse_json(content, expected_type=expected_type)

    # LLM_PROVIDER=groq skips Azure even when its keys are present (e.g. a Mac off the J&J network)
    has_azure = bool(settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT) and settings.LLM_PROVIDER != "groq"
    has_groq = bool(settings.GROQ_API_KEY)
    has_openai = bool(settings.OPENAI_API_KEY)

    # 1. Check connect to Azure OpenAI FIRST
    if has_azure:
        try:
            logger.info("[LLM Pipeline] STEP 1: Checking and attempting connection to Azure OpenAI...")
            content = await call_azure_openai(system, user, api_key)
            logger.info("[LLM Pipeline] Success: Request served by Azure OpenAI!")
            return await parse_json(content, expected_type=expected_type)
        except Exception as e:
            if settings.LLM_PROVIDER == "azure_openai":
                raise  # pinned to the J&J endpoint: no Groq/OpenAI fallback
            logger.warning(
                f"[LLM Pipeline] Azure OpenAI connection not possible ({e}). "
                f"Proceeding immediately to Groq Cloud logic..."
            )

    # 2. If Azure OpenAI is not possible: connect to Groq Cloud logic
    if has_groq:
        try:
            logger.info("[LLM Pipeline] STEP 2: Connecting to Groq Cloud logic...")
            content = await call_groq(system, user, settings.GROQ_API_KEY)
            logger.info("[LLM Pipeline] Success: Request served by Groq Cloud!")
            return await parse_json(content, expected_type=expected_type)
        except Exception as e:
            logger.warning(f"[LLM Pipeline] Groq Cloud failed ({e}). Checking OpenAI fallback...")

    # 3. Fallback to OpenAI if configured
    if has_openai:
        try:
            logger.info("[LLM Pipeline] STEP 3: Connecting to OpenAI...")
            content = await call_openai(system, user, settings.OPENAI_API_KEY)
            logger.info("[LLM Pipeline] Success: Request served by OpenAI!")
            return await parse_json(content, expected_type=expected_type)
        except Exception as e:
            logger.error(f"[LLM Pipeline] OpenAI also failed: {e}")
            raise e

    raise ValueError("No LLM provider was able to respond. Please verify API keys and network connectivity.")


async def ping_groq(api_key: Optional[str] = None) -> None:
    provider = determine_provider(api_key)
    logger.info(f"Ping checking provider: '{provider}'")

    if provider == "azure_openai":
        from openai import AzureOpenAI
        key = api_key or settings.AZURE_OPENAI_API_KEY
        endpoint = settings.AZURE_OPENAI_ENDPOINT
        deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        api_version = settings.AZURE_OPENAI_API_VERSION
        if not key or not endpoint:
            raise ValueError("Azure OpenAI credentials missing in backend .env file.")
        client = AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version=api_version)
        client.chat.completions.create(
            model=deployment,
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
        )
    elif provider == "openai":
        from openai import OpenAI
        key = api_key or settings.OPENAI_API_KEY
        if not key:
            raise ValueError("OpenAI key missing.")
        client = OpenAI(api_key=key)
        client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
        )
    else:
        from groq import Groq
        key = api_key or settings.GROQ_API_KEY
        if not key:
            raise ValueError("Groq API key missing in backend .env file.")
        client = Groq(api_key=key)
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
        )


MAX_TRANSCRIPT_CHARS = 10000

# Multi-file uploads are joined with one header per file (see ingestion_route).
FILE_HEADER_RE = re.compile(r"^===== FILE \d+ of \d+: .* =====$", re.MULTILINE)


def fit_text(text: str, limit: int) -> str:
    """Trim text to `limit` chars. For multi-file input, every file gets a fair
    share (unused share passes to the others) instead of the first file eating
    the whole budget."""
    if len(text) <= limit:
        return text
    starts = [m.start() for m in FILE_HEADER_RE.finditer(text)]
    if len(starts) < 2:
        return text[:limit]
    parts = [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]
    budget, remaining = limit, len(parts)
    shares = {}
    for i in sorted(range(len(parts)), key=lambda i: len(parts[i])):  # smallest first
        shares[i] = min(len(parts[i]), budget // remaining)
        budget -= shares[i]
        remaining -= 1
    return "\n".join(
        parts[i][: shares[i]] + ("\n[...rest of this file omitted for length...]" if shares[i] < len(parts[i]) else "")
        for i in range(len(parts))
    )


async def truncate_transcript(transcript: str) -> str:
    if len(transcript) <= MAX_TRANSCRIPT_CHARS:
        return transcript
    if len(FILE_HEADER_RE.findall(transcript)) > 1:
        return fit_text(transcript, MAX_TRANSCRIPT_CHARS)
    half = MAX_TRANSCRIPT_CHARS // 2
    return (
        transcript[:half]
        + "\n\n[...transcript middle portion omitted for length efficiency...]\n\n"
        + transcript[-half:]
    )


async def generate_mom(transcript: str, api_key: Optional[str] = None) -> dict:
    transcript = await truncate_transcript(transcript)
    system = (
        "You are a senior business analyst writing Minutes of Meeting (MoM) from a transcript or notes.\n\n"
        "RULES:\n"
        "- Use only what the text says. Never invent people, owners, dates, decisions or figures.\n"
        "- If a field is not stated (e.g. an action has no due date), use null. Keep dates as written.\n"
        "- An empty list is correct when the meeting had none of that item.\n"
        "- decisions_finalized: only things the meeting explicitly agreed, not proposals.\n"
        "- open_questions: questions raised and left unanswered.\n"
        "- Text under [ANSWERS TO OPEN QUESTIONS] is confirmed by the user after the meeting: put each answer "
        "in key_points and into the decision or action it settles (e.g. an owner), and do not list it as open.\n\n"
        "Respond ONLY with valid JSON (no markdown fences) in this shape:\n"
        '{"discussion_summary": str, '
        '"attendees": [{"name": str, "role": str|null}], '
        '"key_points": [str], "requirements_identified": [str], '
        '"decisions_finalized": [{"decision": str, "speaker": str|null, "context": str|null}], '
        '"action_items": [{"action": str, "assignee": str|null, "due_date": str|null, "speaker": str|null}], '
        '"open_questions": [str]}'
    )
    return await call_llm(system, transcript, api_key, expected_type=dict)


async def check_clarity(transcript: str, mom: dict, api_key: Optional[str] = None) -> dict:
    transcript = await truncate_transcript(transcript)
    system = (
        "You are an expert requirements analyst. Based strictly on the extracted transcript and MoM, "
        "evaluate whether the discussed requirements are clear, complete, and unambiguous enough to write developer-ready user stories.\n\n"
        "RULES:\n"
        "1. Base your evaluation strictly on the facts present in the transcript.\n"
        "2. If critical technical specifications, business rules, or acceptance conditions mentioned in the transcript are vague or missing, generate clear, targeted clarification questions for the user.\n"
        "3. Respond ONLY with valid JSON: {\"is_clear\": bool, \"clarification_questions\": [str]}.\n"
        "4. If is_clear is true, clarification_questions must be an empty list."
    )
    user = f"TRANSCRIPT:\n{transcript}\n\nMoM:\n{json.dumps(mom)}"
    return await call_llm(system, user, api_key, expected_type=dict)


async def generate_user_stories(
    transcript: str, mom: dict, qa_pairs: list[dict], api_key: Optional[str] = None
) -> list[dict]:
    transcript = await truncate_transcript(transcript)
    system = (
        "You are an expert Agile product manager and technical analyst. "
        "Using the transcript, MoM, and any clarification Q&A provided, generate detailed, professional Agile "
        "user stories ready for Excel and JIRA export.\n\n"
        "EVERY STORY MUST BE TAGGED WITH A story_type OF EITHER 'Business' OR 'Technical':\n"
        "- 'Business' stories describe value visible to an end user or business stakeholder. Write these in the "
        "classic Agile form: 'As a [role], I want [capability], so that [business benefit].' Examples: a new "
        "feature, a UI change, a workflow the business asked for.\n"
        "- 'Technical' stories describe engineering/infrastructure work the business user never directly sees but "
        "that is required to deliver the feature — e.g. API changes, database migrations, integrations, "
        "performance, security, refactoring, DevOps/infra setup. Write these as: 'As a developer, I want "
        "[technical capability], so that [system/engineering outcome].'\n"
        "- Every business-facing requirement that needs backend/technical work MUST produce BOTH a Business story "
        "AND at least one linked Technical story — do not silently fold technical work into the business story's "
        "acceptance criteria.\n"
        "- Do not fabricate technical stories with no basis in the transcript; only split them out where the "
        "transcript/MoM actually implies engineering work distinct from the user-facing outcome.\n\n"
        "STRICT GROUNDING & EXPLANATION RULES:\n"
        "1. GROUNDED IN TRANSCRIPT: All stories, descriptions, and acceptance criteria MUST be strictly rooted in "
        "the facts discussed in the transcript/clarifications.\n"
        "2. WELL-EXPLAINED & PROFESSIONAL: Write comprehensive, clear summaries and descriptions. Provide detailed "
        "bulleted Acceptance Criteria.\n"
        "3. ASSIGNEE: Infer a sensible role or person based on context, or async default to 'Unassigned'.\n\n"
        "Respond ONLY with valid JSON: a list of objects, each matching:\n"
        '{"story_type": "Business" | "Technical", "person_assigned_to": str, "summary": str, "description": str, '
        '"acceptance_criteria": [str], "reasoning": str}'
    )
    qa_text = "\n".join(f"Q: {q['question']}\nA: {q['answer']}" for q in qa_pairs) or "None"
    user = (
        f"TRANSCRIPT:\n{transcript}\n\nMoM:\n{json.dumps(mom)}\n\n"
        f"CLARIFICATIONS:\n{qa_text}"
    )
    stories = await call_llm(system, user, api_key, expected_type=list)

    # Safety net: if the model forgets the field on any item, async default it to Business
    # rather than letting the frontend/export code crash on a missing key.
    for story in stories:
        if story.get("story_type") not in ("Business", "Technical"):
            story["story_type"] = "Business"

    return stories


RUBRIC_CONFIGS = {
    "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)": {
        "benchmark": "Enterprise SDLC Quality Benchmark combining ISO/IEC 25010 Software Quality and GxP 21 CFR Part 11 Regulatory Compliance.",
        "default_dimensions": [
            {"id": "dim-1", "name": "Completeness & Scope", "weight": 25, "desc": "Explicit boundary demarcations, preconditions, postconditions, and edge exception handling."},
            {"id": "dim-2", "name": "Clarity & Precision", "weight": 20, "desc": "Unambiguous requirement statements, objective terminology without subjective adjectives (e.g. 'fast', 'friendly')."},
            {"id": "dim-3", "name": "GxP / Regulatory Audit", "weight": 20, "desc": "Immutable audit trails, 21 CFR Part 11 electronic signature validation, data integrity (ALCOA+), encryption at rest/transit."},
            {"id": "dim-4", "name": "Testability & Boundaries", "weight": 20, "desc": "Quantified, verifiable acceptance criteria, explicit latency percentiles (p95/p99) and load concurrency limits."},
            {"id": "dim-5", "name": "Cross-Artifact Consistency", "weight": 15, "desc": "Unified entity naming, schema alignment with Jira user stories, and architectural diagram nomenclature."},
        ],
        "default_criteria": [
            ("Completeness & Scope", "Unambiguous scope definitions and boundary conditions"),
            ("Testability & Boundaries", "Quantified performance latency SLAs (p95/p99 defined)"),
            ("GxP / Regulatory Audit", "Audit logging for authorization state transitions (21 CFR Part 11)"),
            ("Clarity & Precision", "Absence of untestable or subjective adjectives"),
            ("Cross-Artifact Consistency", "Traceability to downstream Jira stories and component contracts"),
        ],
    },
    "ISO/IEC 25010 Software Quality Standard": {
        "benchmark": "International standard ISO/IEC 25010 Software and Data Quality model evaluating system characteristics.",
        "default_dimensions": [
            {"id": "dim-1", "name": "Functional Suitability & Completeness", "weight": 25, "desc": "Degree to which specified functions meet stated and implied needs when used under specified conditions."},
            {"id": "dim-2", "name": "Performance Efficiency & Latency", "weight": 20, "desc": "Quantified throughput (RPS), response latency percentiles (p99), and resource capacity constraints."},
            {"id": "dim-3", "name": "Compatibility & Interface Standards", "weight": 15, "desc": "Interoperability, schema standard compliance, API versioning, and co-existence with existing enterprise services."},
            {"id": "dim-4", "name": "Reliability & Fault Tolerance", "weight": 20, "desc": "System availability SLAs (99.9x%), circuit breakers, graceful degradation, and disaster recovery RTO/RPO limits."},
            {"id": "dim-5", "name": "Maintainability & Modularity", "weight": 20, "desc": "Architectural modularity, separation of concerns, testability, and clear modification boundaries."},
        ],
        "default_criteria": [
            ("Functional Suitability", "Specification of complete functional journeys with preconditions and postconditions"),
            ("Performance Efficiency", "Quantified latency percentiles (p95/p99) under specified concurrency loads"),
            ("Compatibility", "Standard REST/gRPC/OAuth contract specifications with versioning guidelines"),
            ("Reliability", "Fault tolerance, circuit breaker fallback protocols, and recovery SLAs"),
            ("Maintainability", "Modular domain boundaries and decoupling between submodules"),
        ],
    },
    "GxP Audit & Regulatory Compliance Benchmark": {
        "benchmark": "Strict Life Sciences Pharmaceutical & Medical Device compliance (FDA 21 CFR Part 11, EU Annex 11, GAMP 5, ALCOA+ data integrity).",
        "default_dimensions": [
            {"id": "dim-1", "name": "21 CFR Part 11 Audit Trail Integrity", "weight": 25, "desc": "Computer-generated, time-stamped, immutable audit trails capturing operator ID, action timestamp, and prior values."},
            {"id": "dim-2", "name": "Electronic Signatures & Dual Custody", "weight": 20, "desc": "Multi-party sign-off workflows, cryptographic binding, non-repudiation, and explicit meaning-of-signature captures."},
            {"id": "dim-3", "name": "Data Integrity & ALCOA+ Principles", "weight": 20, "desc": "Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, and Enduring data governance."},
            {"id": "dim-4", "name": "Security & Segregation of Duties", "weight": 20, "desc": "Strict role-based access control (RBAC), least privilege principle, MFA, and administrative role segregation."},
            {"id": "dim-5", "name": "Validation Traceability Matrix (VTM)", "weight": 15, "desc": "Bi-directional traceability between user requirements (URS), functional specs (FS), and IQ/OQ/PQ validation test scripts."},
        ],
        "default_criteria": [
            ("Audit Trail Integrity", "Immutable audit trail specifications with timestamp, user ID, and reason for change"),
            ("Electronic Signatures", "Dual-custody approval workflows with cryptographic signature binding"),
            ("Data Integrity", "Adherence to ALCOA+ standards across data generation, transmission, and archival"),
            ("Security & Access", "Strict role segregation preventing operational operators from altering audit records"),
            ("Validation Traceability", "Traceability mapping from user requirements to validation test protocols"),
        ],
    },
    "Agile Lean Spec & Acceptance Criteria Benchmark": {
        "benchmark": "Agile Product Management benchmark based on INVEST criteria, Given-When-Then BDD scenarios, and Lean MVP boundary scoping.",
        "default_dimensions": [
            {"id": "dim-1", "name": "INVEST User Story Compliance", "weight": 25, "desc": "Independent, Negotiable, Valuable, Estimable, Small, and Testable user story decomposition."},
            {"id": "dim-2", "name": "Given-When-Then Acceptance Criteria", "weight": 25, "desc": "Concrete, automated-test-ready Given/When/Then scenario definitions covering happy path and edge conditions."},
            {"id": "dim-3", "name": "Lean Scope & MVP Demarcation", "weight": 20, "desc": "Rigorous separation of Must-Have MVP scope from out-of-scope backlog items to prevent sprint bloat."},
            {"id": "dim-4", "name": "Cross-Story Dependency Mapping", "weight": 15, "desc": "Explicit prerequisite tracking, architectural blocking dependencies, and external team handoffs."},
            {"id": "dim-5", "name": "Estimation Feasibility & Testability", "weight": 15, "desc": "Clarity of technical assumptions enabling accurate engineering sizing and deterministic QA verification."},
        ],
        "default_criteria": [
            ("INVEST Compliance", "User stories deliver standalone stakeholder value and are appropriately sized"),
            ("Acceptance Criteria", "Given/When/Then BDD acceptance scenarios defined for every requirement"),
            ("Lean MVP Demarcation", "Explicit demarcation between current sprint MVP and future backlog phases"),
            ("Dependency Mapping", "Upstream API dependencies and blocking integration prerequisites documented"),
            ("Testability", "Objective verification criteria without ambiguous or subjective quality assertions"),
        ],
    },
}

DIM_KEY_MAPPING = {
    "completeness": "Completeness & Scope",
    "clarity": "Clarity & Precision",
    "compliance": "GxP / Regulatory Audit",
    "testability": "Testability & Boundaries",
    "crossconsistency": "Cross-Artifact Consistency",
    "cross-consistency": "Cross-Artifact Consistency",
}


async def score_document_ai(
    document_text: str,
    rubric: str = "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)",
    selected_dimensions: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> dict:
    sample_text = fit_text(document_text, 9000) if document_text else "No content provided."

    # Match or fallback to default rubric config
    rubric_conf = RUBRIC_CONFIGS.get(rubric)
    if not rubric_conf:
        # Match by partial keyword
        matched = False
        for k, conf in RUBRIC_CONFIGS.items():
            if any(term in rubric.lower() for term in ["iso", "25010"]) and "iso" in k.lower():
                rubric_conf = conf
                rubric = k
                matched = True
                break
            elif any(term in rubric.lower() for term in ["gxp", "audit", "regulatory"]) and "gxp" in k.lower():
                rubric_conf = conf
                rubric = k
                matched = True
                break
            elif any(term in rubric.lower() for term in ["agile", "lean", "invest"]) and "agile" in k.lower():
                rubric_conf = conf
                rubric = k
                matched = True
                break
        if not matched:
            rubric_conf = RUBRIC_CONFIGS["Enterprise SDLC Standard (ISO/IEC 25010 & GxP)"]
            rubric = "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)"

    # Filter dimensions if user passed specific selections
    target_dimensions = rubric_conf["default_dimensions"]
    if selected_dimensions and len(selected_dimensions) > 0:
        normalized_selected = []
        for d in selected_dimensions:
            clean_d = d.strip().lower()
            mapped = DIM_KEY_MAPPING.get(clean_d, d.strip())
            normalized_selected.append(mapped.lower())

        filtered = [
            dim for dim in target_dimensions
            if any(sel in dim["name"].lower() or dim["name"].lower() in sel for sel in normalized_selected)
        ]
        if filtered:
            target_dimensions = filtered

    dim_spec_text = "\n".join(
        f"- {d['name']} (Weight: {d['weight']}%): {d['desc']}"
        for d in target_dimensions
    )

    system = (
        "You are an expert Enterprise Software Quality Auditor and Lead Regulatory Assessor. "
        "You evaluate technical specifications, requirements documents, and architecture briefs against rigorous quality rubrics.\n\n"
        f"EVALUATION RUBRIC: {rubric}\n"
        f"BENCHMARK STANDARD: {rubric_conf['benchmark']}\n\n"
        f"EVALUATION DIMENSIONS TO ASSESS:\n{dim_spec_text}\n\n"
        "STRICT EVALUATION INSTRUCTIONS:\n"
        "1. GROUNDED IN REAL INPUT: Evaluate strictly based on the text provided. Do NOT use canned or hardcoded numbers.\n"
        "2. DYNAMIC DIMENSION SCORING: For each dimension listed above, assign an honest integer score (0-100) and rating "
        "('Strong' if score >= 80, 'Adequate' if 70-79, 'Needs Attention' if < 70) with a substantive summary explaining the score based directly on quotes or missing items from the document.\n"
        "3. CRITERIA EVALUATION: Generate 4 to 6 criteria specific to this document and rubric, with status ('Pass' | 'Partial' | 'Fail') and concrete finding referencing actual document sections.\n"
        "4. GAPS: Identify 2 to 4 genuine gaps in the document (critical / warning / info) with specific issue and recommendation.\n"
        "5. RECOMMENDATIONS: Provide 3 to 4 prioritized actionable recommendations (High / Medium / Low) with dimension and impact.\n"
        "6. SECTION RATINGS: Identify 3 to 5 actual sections or topic areas from the document and score each (0-100) with badge 'Compliant' or 'Needs Review'.\n"
        "7. SDLC CYCLE JUSTIFICATION: Provide an explicit, thorough justification of the overall score formatted across 5 core SDLC lifecycle stages:\n"
        "   - Stage 1: Requirements Gathering & Scoping\n"
        "   - Stage 2: Design & Architecture Definition\n"
        "   - Stage 3: Quality Assurance & Verification\n"
        "   - Stage 4: Traceability & Integration\n"
        "   - Stage 5: Production Readiness & Hypercare\n\n"
        "RESPOND ONLY WITH A VALID JSON OBJECT matching this exact schema:\n"
        "{\n"
        '  "dimensions": [\n'
        '     {"id": str, "name": str, "score": int (0-100), "weight": int, "rating": "Strong" | "Adequate" | "Needs Attention", "summary": str}\n'
        '  ],\n'
        '  "sdlc_score_justification": {\n'
        '     "overall_summary": "Detailed overall justification explaining why the document received this score...",\n'
        '     "sdlc_stage_breakdown": [\n'
        '        {\n'
        '           "sdlc_stage": "1. Requirements Gathering & Scoping",\n'
        '           "stage_score": int (0-100),\n'
        '           "status": "Pass" | "Needs Attention" | "Critical Risk",\n'
        '           "justification": "Detailed explanation of why this SDLC stage scored low/high based on document text...",\n'
        '           "key_deficits": ["Deficit 1", "Deficit 2"],\n'
        '           "remediation_action": "Actionable steps to improve score in this stage"\n'
        '        }\n'
        '     ]\n'
        '  },\n'
        '  "sectionRatings": [\n'
        '     {"name": str, "score": int (0-100), "badge": "Compliant" | "Needs Review", "badgeColor": "bg-green-100 text-green-700" | "bg-amber-100 text-amber-800"}\n'
        '  ],\n'
        '  "criteria": [\n'
        '     {"id": str, "dimension": str, "criterion": str, "status": "Pass" | "Partial" | "Fail", "finding": str}\n'
        '  ],\n'
        '  "gaps": [\n'
        '     {"id": str, "title": str, "severity": "critical" | "warning" | "info", "section": str, "issue": str, "recommendation": str}\n'
        '  ],\n'
        '  "recommendations": [\n'
        '     {"id": str, "title": str, "dimension": str, "priority": "High" | "Medium" | "Low", "action": str, "impact": str}\n'
        '  ]\n'
        "}"
    )

    user = f"DOCUMENT CONTENT TO AUDIT:\n\n{sample_text}"
    result = await call_llm(system, user, api_key, expected_type=dict)

    # Post-process and guarantee mathematical calculation of overallScore from dimensions
    dims = result.get("dimensions", [])
    if dims and isinstance(dims, list):
        total_weighted = 0
        total_weights = 0
        for idx, d in enumerate(dims):
            if "id" not in d:
                d["id"] = f"dim-{idx+1}"
            sc = int(d.get("score", 75))
            sc = max(0, min(100, sc))
            d["score"] = sc
            wt = int(d.get("weight", 20))
            d["weight"] = wt
            if not d.get("rating"):
                d["rating"] = "Strong" if sc >= 80 else ("Adequate" if sc >= 70 else "Needs Attention")
            total_weighted += sc * wt
            total_weights += wt

        calc_overall = round(total_weighted / total_weights) if total_weights > 0 else 80
    else:
        calc_overall = int(result.get("overallScore", 80))

    calc_overall = max(0, min(100, calc_overall))
    result["overallScore"] = calc_overall

    # Dynamic grade string
    if calc_overall >= 90:
        grade_desc = "Exemplary Specification (Sign-off Ready)"
    elif calc_overall >= 80:
        grade_desc = "Strong Enterprise Specification (Minor Gaps to Address)"
    elif calc_overall >= 70:
        grade_desc = "Adequate Specification (Revision Recommended)"
    else:
        grade_desc = "Incomplete Specification (Structural Revision Required)"
    result["grade"] = f"{calc_overall}/100 · {grade_desc}"

    # Counts
    gaps = result.get("gaps", [])
    if isinstance(gaps, list):
        result["criticalGapsCount"] = len([
            g for g in gaps
            if g.get("severity") == "critical" or g.get("badge") == "Blocking"
        ])
    else:
        result["criticalGapsCount"] = 0

    recs = result.get("recommendations", [])
    result["actionItemsCount"] = len(recs) if isinstance(recs, list) else 0
    result["scoringProfile"] = rubric

    return result


async def generate_sdlc_document_ai(
    source_context: str,
    doc_title: str = "Business Requirements Document",
    doc_type: str = "BRD",
    standard: str = "Enterprise SDLC Standard v2.4",
    included_sections: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> dict:
    sample_text = fit_text(source_context, 10000) if source_context else ""
    sections_req = ", ".join(included_sections) if included_sections else "Executive Summary, Scope, Functional Requirements, Non-Functional SLAs, Security & Compliance, Dependencies & Assumptions"

    system = (
        "You are an enterprise Lead Technical Architect and SDLC Requirements Director. "
        "You author pristine, regulatory-compliant Software Development Life Cycle specifications (BRDs, FRSs, and Architecture Blueprints).\n\n"
        f"DOCUMENT TYPE: {doc_type}\n"
        f"STANDARD / COMPLIANCE RUBRIC: {standard}\n"
        f"REQUESTED CHAPTERS: {sections_req}\n\n"
        "CRITICAL INSTRUCTION:\n"
        "Draft an authoritative, highly detailed document based strictly and exclusively on the provided project context, meeting agreements, and requirements. "
        "Do NOT invent payment reconciliation or invoice matching specifications unless the source material specifically discusses payment processing.\n"
        "Each section MUST have substantive, professional enterprise content (paragraphs, numbered items, and bullet points) derived directly from the source material and ready for engineering and compliance sign-off.\n\n"
        "RESPOND ONLY WITH A VALID JSON OBJECT matching this exact schema:\n"
        "{\n"
        f'  "title": "{doc_title}",\n'
        f'  "type": "{doc_type}",\n'
        '  "version": "1.0",\n'
        '  "qualityScore": int (86-98),\n'
        '  "wordCount": int,\n'
        '  "suggestion": {\n'
        '     "title": "e.g. Add GxP electronic signature protocol",\n'
        '     "description": "e.g. Include dual-custody verification clause in Chapter 5 for regulatory audit readiness."\n'
        '  },\n'
        '  "sections": [\n'
        '     {\n'
        '       "id": "sec-1",\n'
        '       "heading": "1. Executive Summary & Objectives",\n'
        '       "content": "Detailed paragraphs defining the strategic vision, key business drivers, and measurable success metrics...",\n'
        '       "status": "approved"\n'
        '     },\n'
        '     {\n'
        '       "id": "sec-2",\n'
        '       "heading": "2. Scope & Boundary Conditions",\n'
        '       "content": "Explicit demarcations of in-scope capabilities, out-of-scope items, and system boundaries...",\n'
        '       "status": "approved"\n'
        '     },\n'
        '     {\n'
        '       "id": "sec-3",\n'
        '       "heading": "3. Functional Requirements & Process Flows",\n'
        '       "content": "Core user journeys, transactional workflows, event-driven state transitions, and business logic rules...",\n'
        '       "status": "approved"\n'
        '     },\n'
        '     {\n'
        '       "id": "sec-4",\n'
        '       "heading": "4. Non-Functional Requirements & Performance SLAs",\n'
        '       "content": "Quantified latency percentiles (p99 <= 200ms at 500 RPS), 99.99% availability SLAs, and disaster recovery RTO/RPO limits...",\n'
        '       "status": "needs_review"\n'
        '     },\n'
        '     {\n'
        '       "id": "sec-5",\n'
        '       "heading": "5. Security, Data Governance & Audit Compliance",\n'
        '       "content": "21 CFR Part 11 audit trails, OAuth2/mTLS token exchange, encryption at rest (AES-256), and PII data masking protocols...",\n'
        '       "status": "approved"\n'
        '     },\n'
        '     {\n'
        '       "id": "sec-6",\n'
        '       "heading": "6. Dependencies & Technical Assumptions",\n'
        '       "content": "Upstream service prerequisites, schema migrations, third-party gateway contracts, and architectural constraints...",\n'
        '       "status": "draft"\n'
        '     }\n'
        '  ]\n'
        "}"
    )

    user = f"PROJECT CONTEXT & SOURCE MATERIAL:\n\n{sample_text}"
    return await call_llm(system, user, api_key, expected_type=dict)


async def rewrite_sdlc_section_ai(
    section_heading: str,
    current_content: str,
    instruction: str,
    api_key: Optional[str] = None,
) -> dict:
    system = (
        "You are an expert enterprise SDLC technical writer and architect. "
        "You rewrite and refine a single specification section based on stakeholder feedback.\n\n"
        "RESPOND ONLY WITH A VALID JSON OBJECT matching:\n"
        "{\n"
        f'  "heading": "{section_heading}",\n'
        '  "content": "Refined and polished specification text...",\n'
        '  "status": "approved"\n'
        "}"
    )

    user = (
        f"SECTION HEADING: {section_heading}\n"
        f"CURRENT CONTENT:\n{current_content}\n\n"
        f"REWRITE INSTRUCTION:\n{instruction}"
    )
    return await call_llm(system, user, api_key, expected_type=dict)


async def generate_jira_stories_ai(
    source_context: str,
    sprint: str = "Sprint 25",
    team: str = "Engineering & Product",
    project_key: Optional[str] = None,
    options: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> dict:
    sample_text = fit_text(source_context, 10000) if source_context else ""
    p_key = (project_key or "PROJ").strip().upper()

    system = (
        "You are an expert Agile Product Owner and Principal Scrum Master in an enterprise software organization. "
        "You convert approved stakeholder meeting minutes, transcripts, and requirement briefs into INVEST-compliant "
        "User Stories with testable Given/When/Then acceptance criteria.\n\n"
        f"TARGET SPRINT: {sprint}\n"
        f"ASSIGNED TEAM: {team}\n"
        f"PROJECT KEY: {p_key}\n\n"
        "CRITICAL INSTRUCTION:\n"
        "Generate 4 to 6 high-quality, actionable user stories derived DIRECTLY AND EXCLUSIVELY from the provided source context. "
        "Do NOT invent payment reconciliation or invoice matching stories unless the source material is explicitly about invoice reconciliation. "
        f"Each story must have a jira_issue_key following the format '{p_key}-101', '{p_key}-102', etc.\n\n"
        "RESPOND ONLY WITH A VALID JSON OBJECT matching this exact schema:\n"
        "{\n"
        '  "stories": [\n'
        '    {\n'
        '       "id": "story-1",\n'
        f'       "jira_issue_key": "{p_key}-101",\n'
        '       "title": "Brief, active summary of the capability",\n'
        '       "description": "As a [role], I want [capability], so that [business benefit].",\n'
        '       "acceptance_criteria": [\n'
        '          "Given [precondition], When [action is performed], Then [observable outcome]",\n'
        '          "Given [edge condition], When [action], Then [graceful handling or alert]"\n'
        '       ],\n'
        '       "priority": "High" | "Medium" | "Low",\n'
        '       "story_points": 2 | 3 | 5 | 8,\n'
        '       "sprint": "' + sprint + '",\n'
        '       "team": "' + team + '",\n'
        '       "dependencies": ["e.g. Depends on API endpoint definition"],\n'
        '       "assumptions": ["e.g. Stakeholders agree on authentication protocol"],\n'
        '       "status": "draft"\n'
        '    }\n'
        '  ],\n'
        '  "criteria_summary": [\n'
        '    {"id": "crit-1", "story_title": str, "criterion": str, "status": "Ready" | "Needs Review"}\n'
        '  ],\n'
        '  "dependencies_summary": [\n'
        '    {"id": "dep-1", "source": str, "target": str, "type": "Blocks" | "Depends on", "impact": "High" | "Medium"}\n'
        '  ],\n'
        '  "assumptions_summary": [\n'
        '    {"id": "assump-1", "text": str, "category": "Technical" | "Business" | "Compliance", "status": "Verified" | "Open Question"}\n'
        '  ]\n'
        "}"
    )

    user = f"SOURCE MATERIAL TO DECOMPOSE INTO USER STORIES:\n\n{sample_text}"
    return await call_llm(system, user, api_key, expected_type=dict)