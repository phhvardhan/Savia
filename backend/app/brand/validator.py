"""
Checks a rendered Word document against the J&J misuse rules. Runs on every
branded document before it is returned; raises BrandViolation listing every
broken rule.
"""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN

from app.brand import fonts
from app.brand import jnj_tokens as T
from app.brand.document import is_all_caps

# Text effects the brand forbids (w14 = Word 2010+ effects).
EFFECT_TAGS = ("w14:shadow", "w14:textOutline", "w14:glow", "w14:reflection", "w14:props3d")
FONT_FLAGS = ("shadow", "outline", "emboss", "imprint", "all_caps", "small_caps")


def style_name(role: str) -> str:
    """Word paragraph style used for a brand role, e.g. "Brand Section heading"."""
    return "Brand " + role.replace("_", " ").capitalize()


class BrandViolation(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Document breaks the J&J brand rules:\n- " + "\n- ".join(problems))


def _effective(run, paragraph, attr):
    value = getattr(run.font, attr)
    return value if value is not None else getattr(paragraph.style.font, attr)


def _background(paragraph, behind: str) -> str:
    """Paragraph shading if set, else whatever it sits on (page or table cell)."""
    fill = paragraph._p.xpath("./w:pPr/w:shd/@w:fill")
    return fill[0].upper() if fill and fill[0] != "auto" else behind


def _cell_fill(cell) -> str:
    fill = cell._tc.xpath("./w:tcPr/w:shd/@w:fill")
    return fill[0].upper() if fill and fill[0] != "auto" else T.hex_for(T.PAGE_BACKGROUND)


def _check_paragraph(p, where: str, roles_by_style: dict, problems: list[str],
                     behind: str | None = None) -> None:
    if not p.text.strip():
        return
    role = roles_by_style.get(p.style.name)
    if role is None:
        problems.append(f"{where}: paragraph style {p.style.name!r} is not a brand style.")
        return
    spec = T.ROLES[role]
    snippet = p.text.strip()[:40]

    alignment = p.alignment if p.alignment is not None else p.style.paragraph_format.alignment
    if alignment not in (None, WD_ALIGN_PARAGRAPH.LEFT):
        problems.append(f"{where} ({role}) {snippet!r}: must be left aligned.")

    expected_font = fonts.family(spec["font"])
    bg = _background(p, behind or T.hex_for(T.PAGE_BACKGROUND))
    if bg != T.hex_for(spec["background"]):
        problems.append(f"{where} ({role}) {snippet!r}: sits on {bg}, expected {spec['background']} "
                        f"({T.hex_for(spec['background'])}).")
    for run in p.runs:
        if not run.text.strip():
            continue
        font = _effective(run, p, "name")
        if spec["copy"] and font == T.FONT_FAMILIES[T.DISPLAY]:
            problems.append(f"{where} ({role}) {snippet!r}: Johnson Display is for headlines and subheads, never body copy.")
        elif font != expected_font:
            problems.append(f"{where} ({role}) {snippet!r}: font {font!r}, expected {expected_font!r}.")

        if is_all_caps(run.text):
            problems.append(f"{where} ({role}) {run.text[:40]!r}: all caps; use sentence case.")
        for flag in FONT_FLAGS:
            if _effective(run, p, flag):
                problems.append(f"{where} ({role}) {snippet!r}: text effect {flag!r} is not allowed.")
        if any(tag in run._r.xml for tag in EFFECT_TAGS):
            problems.append(f"{where} ({role}) {snippet!r}: text outline/shadow/glow effects are not allowed.")

        rgb = run.font.color.rgb or p.style.font.color.rgb
        color = str(rgb).upper() if rgb is not None else T.hex_for("black")
        if spec["copy"]:
            _check_copy_pairing(color, bg, f"{where} ({role}) {snippet!r}", problems)
        elif color != T.hex_for(spec["color"]):
            problems.append(f"{where} ({role}) {snippet!r}: colour {color}, expected {spec['color']} ({T.hex_for(spec['color'])}).")


def _check_copy_pairing(color: str, bg: str, label: str, problems: list[str]) -> None:
    red, white, black = T.hex_for("red"), T.hex_for("white"), T.hex_for("black")
    allowed = {(T.hex_for(t), T.hex_for(b)) for t, b in T.COPY_PAIRINGS}
    if (color, bg) in allowed:
        return
    if color == red and bg == white:
        problems.append(f"{label}: red text on white is not allowed for copy; use black on white.")
    elif color == black and bg == red:
        problems.append(f"{label}: black text on red is not allowed; use white on red.")
    else:
        problems.append(f"{label}: text {color} on background {bg} is not an allowed copy pairing.")


def validate_docx(doc) -> None:
    """Raise BrandViolation if the document breaks any brand rule."""
    roles_by_style = {style_name(role): role for role in T.ROLES}
    problems: list[str] = []
    for i, p in enumerate(doc.paragraphs, start=1):
        _check_paragraph(p, f"paragraph {i}", roles_by_style, problems)
    for t, table in enumerate(doc.tables, start=1):
        for cell in (c for row in table.rows for c in row.cells):
            for p in cell.paragraphs:
                _check_paragraph(p, f"table {t}", roles_by_style, problems, behind=_cell_fill(cell))
    for section in doc.sections:
        for p in section.footer.paragraphs:
            _check_paragraph(p, "footer", roles_by_style, problems)
    if problems:
        raise BrandViolation(problems)


# --- PowerPoint -------------------------------------------------------------
PPTX_EFFECT_TAGS = ("effectLst><a:", "outerShdw", "innerShdw", "glow", "reflection", "<a:ln")


def _solid_fill(fill) -> str | None:
    try:
        return str(fill.fore_color.rgb).upper() if fill.type == MSO_FILL.SOLID else None
    except (AttributeError, TypeError):
        return None


def _behind(shape, fills: list) -> str:
    """Colour of the last filled shape (drawn earlier) under the centre of this one; else the white slide."""
    cx, cy = shape.left + shape.width // 2, shape.top + shape.height // 2
    hits = [hex_ for (l, t, r, b, hex_) in fills if l <= cx <= r and t <= cy <= b]
    return hits[-1] if hits else T.hex_for("white")


def _check_pptx_text(text_frame, bg: str, where: str, problems: list[str]) -> None:
    text_font, display_font = fonts.family(T.TEXT), fonts.family(T.DISPLAY)
    red, white, black = T.hex_for("red"), T.hex_for("white"), T.hex_for("black")
    allowed = {(T.hex_for(t), T.hex_for(b)) for t, b in T.COPY_PAIRINGS}
    for p in text_frame.paragraphs:
        if not p.text.strip():
            continue
        snippet = p.text.strip()[:40]
        if p.alignment not in (None, PP_ALIGN.LEFT):
            problems.append(f"{where} {snippet!r}: must be left aligned.")
        for run in p.runs:
            if not run.text.strip():
                continue
            font, size = run.font.name, run.font.size.pt if run.font.size else None
            if font not in (text_font, display_font):
                problems.append(f"{where} {snippet!r}: font {font!r}, expected {text_font!r} or {display_font!r}.")
            elif font == display_font != text_font and size is not None and size < T.DISPLAY_MIN_PT:
                problems.append(f"{where} {snippet!r}: Johnson Display at {size:g}pt; it is for headlines and "
                                f"subheads only, use Johnson Text.")
            rpr = run._r.find("{http://schemas.openxmlformats.org/drawingml/2006/main}rPr")
            if is_all_caps(run.text) or (rpr is not None and rpr.get("cap") in ("all", "small")):
                problems.append(f"{where} {run.text[:40]!r}: all caps; use sentence case.")
            if rpr is not None and any(tag in run._r.xml for tag in PPTX_EFFECT_TAGS):
                problems.append(f"{where} {snippet!r}: text outline/shadow/glow effects are not allowed.")

            if not any(c.isalpha() for c in run.text):
                continue  # bullets, arrows, numbers-only marks
            try:
                color = str(run.font.color.rgb).upper()
            except AttributeError:
                color = black
            if bg == red and color != white:
                problems.append(f"{where} {snippet!r}: only white text on J&J Red (found {color}).")
            elif not run.font.bold and (color, bg) not in allowed:
                if color == red and bg in (white, T.hex_for("neutral_100")):
                    problems.append(f"{where} {snippet!r}: red copy on white is not allowed; use black.")
                else:
                    problems.append(f"{where} {snippet!r}: text {color} on {bg} is not an allowed copy pairing.")


def validate_pptx(prs) -> None:
    """Raise BrandViolation if the deck breaks any brand rule."""
    problems: list[str] = []
    for n, slide in enumerate(prs.slides, start=1):
        fills: list = []
        for shape in slide.shapes:
            where = f"slide {n}"
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        _check_pptx_text(cell.text_frame, _solid_fill(cell.fill) or T.hex_for("white"), where, problems)
            elif shape.has_text_frame and shape.text_frame.text.strip():
                _check_pptx_text(shape.text_frame, _behind(shape, fills), where, problems)
            fill = _solid_fill(shape.fill) if hasattr(shape, "fill") else None
            if fill:
                fills.append((shape.left, shape.top, shape.left + shape.width, shape.top + shape.height, fill))
            if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and shape.shadow.inherit:  # theme shadow
                problems.append(f"{where}: shape has a shadow; effects are not allowed.")
    if problems:
        raise BrandViolation(problems)
