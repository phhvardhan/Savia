"""
Font resolution: Johnson fonts when their files are in the fonts directory,
otherwise Arial. Font files are proprietary; the directory is git-ignored.

Directory: $SAVIA_BRAND_FONTS_DIR, default backend/app/brand/fonts/.
Expected names: JohnsonDisplay-<Weight>.otf / JohnsonText-<Weight>.otf
(.ttf and .woff2 also accepted), weights Light, Regular, Medium, Bold.
"""
import os
from pathlib import Path

from app.brand import jnj_tokens as T

FONT_EXTS = {".otf", ".ttf", ".woff2"}
WEIGHTS = {"Light": 300, "Regular": 400, "Medium": 500, "Bold": 700}


def fonts_dir() -> Path:
    return Path(os.getenv("SAVIA_BRAND_FONTS_DIR") or Path(__file__).parent / "fonts")


def font_files() -> list[Path]:
    d = fonts_dir()
    return sorted(p for p in d.iterdir() if p.suffix.lower() in FONT_EXTS) if d.is_dir() else []


def family(role: str) -> str:
    """Font family for a role ("display" or "text")."""
    prefix = T.FONT_FILE_PREFIX[role] + "-"
    if any(p.name.startswith(prefix) for p in font_files()):
        return T.FONT_FAMILIES[role]
    return T.FALLBACK_FONT


def font_faces() -> list[dict]:
    """Available Johnson font files as {family, weight, file} for the browser preview."""
    faces = []
    for p in font_files():
        for role, prefix in T.FONT_FILE_PREFIX.items():
            weight = WEIGHTS.get(p.stem.removeprefix(prefix + "-"))
            if p.stem.startswith(prefix + "-") and weight:
                faces.append({"family": T.FONT_FAMILIES[role], "weight": weight, "file": p.name})
    return faces
