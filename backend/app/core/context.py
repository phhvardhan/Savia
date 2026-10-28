import asyncio
import hashlib
from collections import OrderedDict
from typing import Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.llm import call_structured
from app.core.text import chunk_text, fit_text
from app.utils.logger import logger

CONDENSE_SYSTEM = (
    "You prepare source material for an SDLC deliverable. You get one excerpt of a longer input.\n"
    "FOCUS: {focus}\n"
    "Copy every passage of the excerpt that matters for the focus: requirements, decisions, actions, owners, "
    "dates, figures, IDs, constraints, risks, open questions and who said what.\n"
    "Keep wording, names, numbers and IDs exactly as written. Never add anything that is not in the excerpt. "
    "Skip small talk and repetition.\n"
    'Return only JSON: {{"notes": ["..."]}}'
)

_cache: "OrderedDict[str, str]" = OrderedDict()


class Notes(BaseModel):
    notes: list[str] = Field(default_factory=list)


async def _condense(chunk: str, focus: str, index: int, total: int, gate: asyncio.Semaphore) -> str:
    async with gate:
        data = await call_structured(CONDENSE_SYSTEM.format(focus=focus), chunk, Notes)
    notes = "\n".join(f"- {n}" for n in data["notes"] if n.strip())
    return f"===== PART {index} of {total} =====\n{notes or '(nothing relevant)'}"


async def fit_source(text: str, focus: str, budget: Optional[int] = None) -> str:
    budget = budget or settings.LLM_INPUT_CHARS
    if len(text) <= budget:
        return text
    key = hashlib.sha256(f"{budget}|{focus}|{text}".encode("utf-8")).hexdigest()
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    chunks = chunk_text(text, settings.LLM_CHUNK_CHARS)
    logger.info(f"[Context] Condensing {len(text)} chars in {len(chunks)} parts for: {focus[:60]}")
    gate = asyncio.Semaphore(4)
    parts = await asyncio.gather(*(_condense(c, focus, i, len(chunks), gate) for i, c in enumerate(chunks, 1)))
    condensed = fit_text("\n\n".join(parts), budget)
    _cache[key] = condensed
    if len(_cache) > 32:
        _cache.popitem(last=False)
    return condensed
