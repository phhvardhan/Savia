import re
from typing import Any, Iterable

from app.models.workflow import TraceabilityLink

ID_RE = re.compile(r"\b(REQ|US|DES(?:-[A-Z]{2,3})?|TC)-\d{1,5}\b")
FIGURE_RE = re.compile(
    r"(?:[$€£]\s?\d[\d,]*(?:\.\d+)?\s?(?:k|m|bn|million|billion)?"
    r"|\b\d[\d,]*(?:\.\d+)?\s?(?:%|percent\b|ms\b|milliseconds?\b|seconds?\b|secs?\b|minutes?\b|mins?\b|hours?\b"
    r"|hrs?\b|days?\b|weeks?\b|months?\b|years?\b|rps\b|tps\b|users?\b|gb\b|tb\b|mb\b|usd\b|eur\b)"
    r"|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b)",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
PREFIX_FIELD = {"REQ": "requirement_ids", "US": "user_story_ids", "DES": "design_ids", "TC": "test_case_ids"}


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from strings(v)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield str(value)


def ids_in(value: Any) -> set[str]:
    return {m.group(0) for s in strings(value) for m in ID_RE.finditer(s)}


def _prefix(identifier: str) -> str:
    return identifier.split("-")[0]


def _numbers(text: str) -> set[str]:
    return {n.lstrip("0") or "0" for n in NUMBER_RE.findall(text.replace(",", ""))}


def unsupported_figures(content: Any, evidence: str) -> list[str]:
    known = _numbers(evidence)
    found: list[str] = []
    for s in strings(content):
        for match in FIGURE_RE.finditer(s):
            figure = match.group(0).strip()
            if not _numbers(figure) <= known and figure not in found:
                found.append(figure)
    return found[:25]


def assess(content: dict, source: str, upstream: dict, defines: tuple[str, ...]) -> dict:
    evidence = source + "\n" + "\n".join(strings(upstream))
    known_ids = ids_in(source) | ids_in(upstream)
    referenced = {i for i in ids_in(content) if _prefix(i) not in defines}
    return {
        "unsupported_figures": unsupported_figures(content, evidence),
        "dangling_references": sorted(referenced - known_ids),
        "checked": True,
    }


def traceability(content: dict, source: str, upstream_ids: list[str], workflow_id: str) -> TraceabilityLink:
    link = TraceabilityLink(upstream_artifact_ids=upstream_ids, source_reference=workflow_id)
    for identifier in sorted(ids_in(content) | ids_in(source)):
        field = PREFIX_FIELD.get(_prefix(identifier))
        if field:
            getattr(link, field).append(identifier)
    return link
