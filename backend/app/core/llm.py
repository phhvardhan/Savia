import asyncio
import contextvars
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Type

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.db import db
from app.utils.logger import logger

current_run_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_run_id", default=None)
current_purpose: contextvars.ContextVar[str] = contextvars.ContextVar("current_purpose", default="")

RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class LLMError(RuntimeError):
    pass


class LLMTruncated(LLMError):
    pass


class _Retryable(Exception):
    pass


@dataclass
class Target:
    provider: str
    url: str
    headers: dict
    model: str


@dataclass
class Completion:
    content: str
    provider: str
    model: str
    finish_reason: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


_clients: dict[int, httpx.AsyncClient] = {}


def _http() -> httpx.AsyncClient:
    key = id(asyncio.get_running_loop())
    client = _clients.get(key)
    if client is None or client.is_closed:
        verify: Any = settings.LLM_CA_BUNDLE or settings.LLM_VERIFY_TLS
        timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS, connect=5.0)
        client = _clients[key] = httpx.AsyncClient(timeout=timeout, verify=verify)
    return client


def _azure() -> list[Target]:
    key = settings.AZURE_OPENAI_API_KEY
    if not (key and settings.AZURE_OPENAI_ENDPOINT):
        return []
    headers = {"api-key": key, "Ocp-Apim-Subscription-Key": key}
    return [Target("azure_openai", settings.AZURE_OPENAI_URL, headers, settings.AZURE_OPENAI_DEPLOYMENT_NAME)]


def _groq() -> list[Target]:
    key = settings.GROQ_API_KEY
    if not key:
        return []
    return [Target("groq", GROQ_URL, {"Authorization": f"Bearer {key}"}, m) for m in settings.GROQ_MODELS]


def _openai() -> list[Target]:
    key = settings.OPENAI_API_KEY
    if not key:
        return []
    return [Target("openai", OPENAI_URL, {"Authorization": f"Bearer {key}"}, settings.OPENAI_MODEL)]


def targets() -> list[Target]:
    provider = settings.LLM_PROVIDER
    if provider == "azure_openai":
        return _azure()
    if provider == "groq":
        return _groq()
    if provider == "openai":
        return _openai()
    return _azure() + _groq() + _openai()


def _record(target: Target, started: float, completion: Optional[Completion], error: Optional[str]) -> None:
    try:
        db.execute(
            "INSERT INTO llm_calls (run_id, purpose, provider, model, prompt_tokens, completion_tokens, latency_ms,"
            " finish_reason, ok, error, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                current_run_id.get(),
                current_purpose.get(),
                target.provider,
                target.model,
                completion.prompt_tokens if completion else None,
                completion.completion_tokens if completion else None,
                int((time.perf_counter() - started) * 1000),
                completion.finish_reason if completion else None,
                1 if completion and not error else 0,
                (error or "")[:500] or None,
                datetime.utcnow().isoformat(),
            ),
        )
    except Exception as e:
        logger.warning(f"[LLM] Could not record call: {e}")


async def _post(target: Target, system: str, user: str, max_tokens: int, json_mode: bool) -> Completion:
    payload: dict[str, Any] = {
        "model": target.model,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        resp = await _http().post(target.url, json=payload, headers={"Content-Type": "application/json", **target.headers})
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        raise _Retryable(f"{type(e).__name__}: {e}") from e
    if resp.status_code in RETRYABLE_STATUS:
        raise _Retryable(f"HTTP {resp.status_code}: {resp.text[:200]}")
    if resp.status_code != 200:
        raise LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    choice = data["choices"][0]
    usage = data.get("usage") or {}
    return Completion(
        content=choice["message"].get("content") or "",
        provider=target.provider,
        model=data.get("model") or target.model,
        finish_reason=choice.get("finish_reason"),
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
    )


async def complete(system: str, user: str, max_tokens: Optional[int] = None, json_mode: bool = True) -> Completion:
    candidates = targets()
    if not candidates:
        raise LLMError("No LLM provider is configured. Set LLM_PROVIDER and its keys in backend/.env.")
    max_tokens = max_tokens or settings.LLM_MAX_OUTPUT_TOKENS
    errors: list[str] = []
    for target in candidates:
        for attempt in range(3):
            started = time.perf_counter()
            try:
                completion = await _post(target, system, user, max_tokens, json_mode)
            except _Retryable as e:
                _record(target, started, None, str(e))
                errors.append(f"{target.provider}/{target.model}: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                break
            except Exception as e:
                _record(target, started, None, str(e))
                errors.append(f"{target.provider}/{target.model}: {e}")
                break
            if completion.finish_reason == "length":
                _record(target, started, completion, "truncated")
                raise LLMTruncated(
                    f"The answer was cut off at {max_tokens} output tokens. "
                    "Raise LLM_MAX_OUTPUT_TOKENS or send a smaller input."
                )
            if not completion.content.strip():
                _record(target, started, completion, "empty")
                errors.append(f"{target.provider}/{target.model}: empty answer")
                break
            _record(target, started, completion, None)
            logger.info(
                f"[LLM] {target.provider}/{completion.model} ok in {int((time.perf_counter() - started) * 1000)} ms, "
                f"{completion.prompt_tokens}+{completion.completion_tokens} tokens"
            )
            return completion
    raise LLMError("No LLM provider answered. " + " | ".join(errors[-4:]))


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


async def parse_json(raw: str, expected_type=dict):
    raw = _strip_fences(raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        parsed = json_repair.loads(raw)
        if parsed in ("", None):
            raise ValueError("The answer was not valid JSON.")

    if expected_type is dict:
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
            return parsed[0]
        if not isinstance(parsed, dict):
            raise TypeError(f"Expected a JSON object, got {type(parsed).__name__}.")
    elif expected_type is list:
        if isinstance(parsed, dict):
            for key in ("user_stories", "stories", "items", "data"):
                if isinstance(parsed.get(key), list):
                    return parsed[key]
            return [parsed]
        if not isinstance(parsed, list):
            raise TypeError(f"Expected a JSON list, got {type(parsed).__name__}.")
    return parsed


async def call_llm(system: str, user: str, expected_type=dict, max_tokens: Optional[int] = None):
    completion = await complete(system, user, max_tokens=max_tokens)
    return await parse_json(completion.content, expected_type=expected_type)


def _describe(error: Exception) -> str:
    if isinstance(error, ValidationError):
        return "\n".join(
            f"- {'.'.join(str(p) for p in e['loc']) or '(root)'}: {e['msg']}" for e in error.errors()[:15]
        )
    return f"- {error}"


async def call_structured(system: str, user: str, model: Type[BaseModel], retries: Optional[int] = None) -> dict:
    retries = settings.LLM_RETRIES if retries is None else retries
    prompt = user
    last: Optional[Exception] = None
    for _ in range(retries + 1):
        completion = await complete(system, prompt)
        try:
            data = await parse_json(completion.content, expected_type=dict)
            return model.model_validate(data).model_dump(mode="json")
        except (ValueError, TypeError, ValidationError) as e:
            last = e
            logger.warning(f"[LLM] Invalid structured output for {model.__name__}: {_describe(e)}")
            prompt = (
                f"{user}\n\nYOUR PREVIOUS ANSWER DID NOT MATCH THE REQUIRED SCHEMA:\n{_describe(e)}\n"
                "Return the complete corrected JSON object only."
            )
    raise LLMError(f"The model did not return valid {model.__name__} output: {_describe(last)}")
