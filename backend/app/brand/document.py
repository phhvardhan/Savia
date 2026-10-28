"""
The structured content a branded document is built from. Text is normalised
to sentence case on the way in, so all-caps never reaches a renderer.
"""
from typing import Optional

from pydantic import BaseModel, field_validator


# Short words that are ordinary English, not acronyms, when a line is shouted.
# ponytail: fixed list; a shouted "IT" (the department) gets lowercased. Extend if it bites.
_SHORT_WORDS = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are", "be", "it", "we",
                "as", "at", "by", "if", "no", "not", "can", "our", "all", "you", "new", "now", "how", "why",
                "who", "use", "per", "via", "has", "was", "but", "its", "out", "up", "so", "do"}


def _is_acronym(word: str) -> bool:
    """SAP, WMS, API, S/4HANA, DDL3, J&J: short (not a common word) or containing a digit, "/" or "&"."""
    if any(c.isdigit() or c in "/&" for c in word):
        return True
    letters = "".join(c for c in word if c.isalpha())
    return len(letters) <= 3 and letters.lower() not in _SHORT_WORDS


def is_all_caps(text: str) -> bool:
    """Shouting: 4+ letters outside acronyms, all upper case."""
    letters = [c for w in text.split() if not _is_acronym(w) for c in w if c.isalpha()]
    return len(letters) >= 4 and all(c.isupper() for c in letters)


def sentence_case(text: str) -> str:
    """All-caps text becomes sentence case, keeping acronyms; anything else is left as written."""
    if not is_all_caps(text):
        return text
    lower = " ".join(w if _is_acronym(w) else w.lower() for w in text.split(" "))
    return next((lower[:i] + c.upper() + lower[i + 1:] for i, c in enumerate(lower) if c.isalpha()), lower)


def _multiline(text: str) -> str:
    return "\n".join(sentence_case(line) for line in text.split("\n"))


class Field(BaseModel):
    label: str
    value: str

    @field_validator("label")
    @classmethod
    def _label(cls, v: str) -> str:
        return sentence_case(v)

    @field_validator("value")
    @classmethod
    def _value(cls, v: str) -> str:
        return _multiline(v)


class Item(BaseModel):
    """One record in a section (a user story, an action item, a risk)."""
    title: Optional[str] = None
    fields: list[Field] = []

    @field_validator("title")
    @classmethod
    def _title(cls, v: Optional[str]) -> Optional[str]:
        return sentence_case(v) if v else v


class Section(BaseModel):
    heading: str
    body: list[str] = []  # one entry per paragraph
    items: list[Item] = []

    @field_validator("heading")
    @classmethod
    def _heading(cls, v: str) -> str:
        return sentence_case(v)

    @field_validator("body")
    @classmethod
    def _body(cls, v: list[str]) -> list[str]:
        return [_multiline(p) for p in v]


class BrandDocument(BaseModel):
    eyebrow: Optional[str] = None
    headline: str
    subhead: Optional[str] = None
    sections: list[Section] = []
    footer: str = ""

    @field_validator("eyebrow", "headline", "subhead", "footer")
    @classmethod
    def _text(cls, v: Optional[str]) -> Optional[str]:
        return sentence_case(v) if v else v
