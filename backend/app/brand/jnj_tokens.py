"""
Johnson & Johnson brand tokens: the ONE place brand values live.

Every renderer (Word export, on-screen brand preview) reads from here. Nothing
brand-related belongs in an LLM prompt.

TO FILL IN: replace each "TODO_HEX" in COLORS with the official 6-digit hex
(no "#"), e.g. "AB1234". Until then the renderer uses FALLBACK_HEX and logs a
warning naming each unfilled token.
"""
import logging

log = logging.getLogger(__name__)

TODO = "TODO_HEX"

# --- Colours ----------------------------------------------------------------
COLORS = {
    # Core
    "red": "EB1700",    # J&J Red, as used in the SAVIA Figma (--brand-red). Confirm against official guide.
    "white": "FFFFFF",
    "black": "000000",
    # Neutrals: warm grays, near-white to black
    "neutral_100": TODO,  # near-white
    "neutral_300": TODO,
    "neutral_500": TODO,
    "neutral_700": TODO,
    "neutral_900": TODO,  # near-black
    # Accents: small use only
    "accent_yellow": TODO,
    "accent_orange": TODO,
    "accent_dark_red": TODO,
    "accent_purple": TODO,
    "accent_green": TODO,
    "accent_blue": TODO,
}

# Used only while a token above is still TODO, so documents keep rendering.
# Plain white / light gray / black, not brand claims.
FALLBACK_HEX = {"white": "FFFFFF", "neutral_100": "F2F2F2", "neutral_300": "BFBFBF"}
FALLBACK_DEFAULT = "000000"

# Share of a layout each colour family should cover. Reference only: a Word
# document has no measurable colour area, so this is not enforced in code.
PROPORTIONS = {"red": 0.40, "white": 0.40, "neutrals": 0.15, "accents": 0.05}

# The only text/background pairs allowed for copy (body, footer).
# Never red text on white, never black text on red.
# A near-white neutral panel counts as white.
COPY_PAIRINGS = {("black", "white"), ("white", "red"), ("black", "neutral_100")}

# --- Fonts ------------------------------------------------------------------
# Font "roles" map to families in brand/fonts.py (Johnson file present, else Arial).
DISPLAY = "display"  # Johnson Display: headlines and subheads, large scale
TEXT = "text"        # Johnson Text: body copy, captions, detailed content

FONT_FAMILIES = {DISPLAY: "Johnson Display", TEXT: "Johnson Text"}
FONT_FILE_PREFIX = {DISPLAY: "JohnsonDisplay", TEXT: "JohnsonText"}
FALLBACK_FONT = "Arial"
# Johnson Display is for large scale only; in slides, smaller text must be Johnson Text.
DISPLAY_MIN_PT = 16

# --- Hierarchy --------------------------------------------------------------
# In document order. All left aligned, no effects, sentence case.
# "background": the colour the role sits on. Eyebrow, headline and subhead sit
# on the full-width J&J Red cover band in white (white on red is allowed).
# "copy" roles must follow COPY_PAIRINGS and may never use Johnson Display.
ROLES = {
    "eyebrow":         {"font": TEXT,    "size_pt": 10,   "bold": True,  "color": "white", "background": "red",   "copy": False},
    "headline":        {"font": DISPLAY, "size_pt": 30,   "bold": True,  "color": "white", "background": "red",   "copy": False},
    "subhead":         {"font": DISPLAY, "size_pt": 13,   "bold": False, "color": "white", "background": "red",   "copy": False},
    # Section headings are short labels, not large-scale display type, so Johnson Text Bold.
    "section_heading": {"font": TEXT,    "size_pt": 15,   "bold": True,  "color": "red",   "background": "white", "copy": False},
    # One record (a story, an action item, a risk): its id and title.
    "item_title":      {"font": TEXT,    "size_pt": 11.5, "bold": True,  "color": "black", "background": "white", "copy": False},
    "body":            {"font": TEXT,    "size_pt": 10,   "bold": False, "color": "black", "background": "white", "copy": True},
    "footer":          {"font": TEXT,    "size_pt": 8,    "bold": False, "color": "black", "background": "white", "copy": True},
}

PAGE_BACKGROUND = "white"
RULE_COLOR = "neutral_300"  # thin line between records

_warned: set[str] = set()


def hex_for(name: str) -> str:
    """Resolved 6-digit hex for a colour token, falling back while it is TODO."""
    value = COLORS[name]
    if value == TODO:
        if name not in _warned:
            _warned.add(name)
            log.warning("Brand colour %r is still TODO_HEX in brand/jnj_tokens.py; using a fallback.", name)
        return FALLBACK_HEX.get(name, FALLBACK_DEFAULT)
    return value.upper()
