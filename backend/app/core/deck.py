"""
Solution Analyzer output as a client-ready PowerPoint deck (16:9).

One idea per slide, in the order a stakeholder pitch runs: title, summary,
problem, constraints, approach, components, integrations, alternatives,
risks, roadmap, what we need from you, discussion. Only the agent's real
output goes in; empty sections are skipped rather than padded.
"""
import io
import re
from datetime import date
from typing import Any, Dict, List

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from app.brand import fonts as brand_fonts
from app.brand import jnj_tokens as T
from app.brand.document import sentence_case
from app.brand.validator import validate_pptx


def _rgb(token: str) -> RGBColor:
    return RGBColor.from_string(T.hex_for(token))


# J&J brand colours, all from app/brand/jnj_tokens.py. Copy is black on white
# (or a near-white neutral) or white on J&J Red; never red copy, never black on red.
ACCENT = _rgb("red")
ACCENT_DARK = ACCENT
ACCENT_TINT = _rgb("neutral_100")
INK = _rgb("black")
MUTED = INK
LINE = _rgb("neutral_300")
WHITE = _rgb("white")
SOFT_BG = ACCENT_TINT
# Accents are for small use only (a level label); plain black until their hex values are filled in.
LEVEL = {
    "high": _rgb("accent_dark_red"),
    "medium": _rgb("accent_orange"),
    "low": _rgb("accent_green"),
}
W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.7)
ROWS_PER_SLIDE = 5


def _clean(value: Any) -> str:
    """Plain text for a slide: no 'What the input says:' prefixes, no stray None."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ("none", "null", "n/a"):
        return ""
    text = re.sub(r"^what the input says:\s*", "", text, flags=re.I)
    return sentence_case(text.strip())


def _quote(value: Any) -> str:
    """Evidence quoted from the input reads as a quote."""
    text = _clean(value)
    m = re.match(r"^['\"‘“](.*)['\"’”](.*)$", text)
    return f"“{m.group(1)}”{m.group(2)}" if m else text


def _size_for(text: str, big: int, small: int, long_at: int = 220) -> int:
    """Shrinks long text so it stays inside its box (python-pptx can't autofit)."""
    n = len(text)
    if n <= long_at // 2:
        return big
    if n >= long_at * 2:
        return small
    return round(big - (big - small) * (n - long_at // 2) / (long_at * 1.5))


def _text(slide, x, y, w, h, text, size=18, bold=False, color=INK, anchor=MSO_ANCHOR.TOP, display=False):
    """Left-aligned text. display=True for large headings (Johnson Display); everything else is Johnson Text."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = brand_fonts.family(T.DISPLAY if display else T.TEXT)
    return box


def _rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    return s


def _bullets(slide, x, y, w, h, items: List[str], size=18, color=INK, bullet_color=ACCENT):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(10)
        dot = p.add_run()
        dot.text = "■  "
        dot.font.size = Pt(size - 6)
        dot.font.color.rgb = bullet_color
        dot.font.name = brand_fonts.family(T.TEXT)
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.name = brand_fonts.family(T.TEXT)
    return box


class _Deck:
    def __init__(self, title: str, footer: str):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.title = title
        self.footer = footer
        self.count = 0

    def slide(self, heading: str, kicker: str = ""):
        """A content slide: accent bar, kicker, heading, footer with page number."""
        s = self.prs.slides.add_slide(self.blank)
        self.count += 1
        _rect(s, 0, 0, Inches(0.18), H, ACCENT)
        if kicker:
            _text(s, MARGIN, Inches(0.45), Inches(10), Inches(0.35), kicker, 13, True, ACCENT)
        _text(s, MARGIN, Inches(0.78), W - 2 * MARGIN, Inches(0.8), heading, 32, True, INK, display=True)
        _rect(s, MARGIN, H - Inches(0.55), W - 2 * MARGIN, Emu(9525), LINE)
        _text(s, MARGIN, H - Inches(0.45), W - 2 * MARGIN, Inches(0.3), f"{self.footer} · {self.count + 1}",
              10, color=MUTED)
        return s

    def table(self, s, headers: List[str], rows: List[List[str]], widths: List[float],
              y=Inches(1.85), pill_col: int = -1):
        """A clean table: J&J Red header, banded rows; pill_col gets a coloured level label."""
        total = sum(widths)
        avail = W - 2 * MARGIN
        col_w = [int(avail * w / total) for w in widths]
        row_h = Inches(0.5)
        shape = s.shapes.add_table(len(rows) + 1, len(headers), MARGIN, y, avail, row_h * (len(rows) + 1))
        tbl = shape.table
        tbl.first_row = True
        for i, wdt in enumerate(col_w):
            tbl.columns[i].width = wdt
        longest = max((len(c) for r in rows for c in r), default=0)
        body = 14 if longest < 120 else 12
        for ci, head in enumerate(headers):
            cell = tbl.cell(0, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT
            cell.margin_left = cell.margin_right = Inches(0.15)
            cell.text = head
            cell.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
            for run in cell.text_frame.paragraphs[0].runs:
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = WHITE
                run.font.name = brand_fonts.family(T.TEXT)
        for ri, row in enumerate(rows, start=1):
            for ci, value in enumerate(row):
                cell = tbl.cell(ri, ci)
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if ri % 2 else SOFT_BG
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = cell.margin_right = Inches(0.15)
                cell.margin_top = cell.margin_bottom = Inches(0.08)
                cell.text = value
                cell.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
                run = cell.text_frame.paragraphs[0].runs[0] if cell.text_frame.paragraphs[0].runs else None
                if not run:
                    continue
                run.font.size = Pt(body)
                run.font.name = brand_fonts.family(T.TEXT)
                run.font.color.rgb = INK
                if ci == 0:
                    run.font.bold = True
                if ci == pill_col:
                    run.font.bold = True
                    run.font.color.rgb = LEVEL.get(value.strip().lower(), INK)

    def save(self) -> bytes:
        validate_pptx(self.prs)  # J&J brand rules; raises BrandViolation
        buf = io.BytesIO()
        self.prs.save(buf)
        return buf.getvalue()


def _pages(items: list, size: int = ROWS_PER_SLIDE):
    return [items[i:i + size] for i in range(0, len(items), size)] or [[]]


def _table_pages(rows: List[List[str]], widths: List[float], budget_in: float = 4.6) -> List[List[List[str]]]:
    """Splits table rows across slides by estimated height, so long cells never run off the slide."""
    avail_in = (W - 2 * MARGIN) / 914400
    col_in = [avail_in * w / sum(widths) - 0.3 for w in widths]
    longest = max((len(c) for r in rows for c in r), default=0)
    size = 14 if longest < 120 else 12  # same rule as _Deck.table

    def height(row):
        lines = max(-(-len(c) // max(1, int(w * 72 / (size * 0.52)))) for c, w in zip(row, col_in))
        return max(1, lines) * size * 1.2 / 72 + 0.16

    pages, page, used = [], [], 0.0
    for row in rows:
        h = height(row)
        if page and (used + h > budget_in or len(page) >= ROWS_PER_SLIDE):
            pages.append(page)
            page, used = [], 0.0
        page.append(row)
        used += h
    return pages + [page] if page else pages


def _heading(base: str, page: int, pages: int) -> str:
    return base if pages == 1 else f"{base} ({page} of {pages})"


def solution_to_pptx(content: Dict[str, Any], subtitle: str) -> bytes:
    """Builds the stakeholder deck from a Solution Analyzer artifact's content."""
    title = _clean(content.get("title")) or "Solution Blueprint"
    name = re.sub(r"^solution blueprint:\s*", "", title, flags=re.I) or title
    deck = _Deck(title, f"SAVIA · Solution Blueprint · {name}")

    # 1. Title
    s = deck.prs.slides.add_slide(deck.blank)
    _rect(s, 0, 0, W, H, ACCENT)
    _text(s, MARGIN, Inches(0.8), Inches(6), Inches(0.4), "Solution blueprint", 16, True, WHITE)
    _text(s, MARGIN, Inches(1.6), Inches(10.5), Inches(3.0), name, _size_for(name, 54, 36, 90), True, WHITE,
          anchor=MSO_ANCHOR.BOTTOM, display=True)
    _text(s, MARGIN, Inches(4.9), Inches(10.5), Inches(0.8), subtitle, 18, color=WHITE, display=True)
    _text(s, MARGIN, Inches(6.4), Inches(6), Inches(0.4), date.today().strftime("%d %B %Y"), 14, color=WHITE)

    # 2. Executive summary
    summary = _clean(content.get("executive_summary"))
    if summary:
        s = deck.slide("Executive summary", "In one minute")
        _rect(s, MARGIN, Inches(1.9), Inches(0.08), Inches(4.2), ACCENT)
        _text(s, MARGIN + Inches(0.4), Inches(1.9), W - 2 * MARGIN - Inches(0.4), Inches(4.4), summary,
              _size_for(summary, 28, 18, 300), color=INK)

    # 3. The problem
    problem = content.get("problem") or {}
    if isinstance(problem, str):
        problem = {"statement": problem}
    statement = _clean(problem.get("statement"))
    evidence = [_quote(e) for e in problem.get("evidence") or [] if _clean(e)]
    affected = [_clean(a) for a in problem.get("affected") or [] if _clean(a)]
    if statement or evidence:
        s = deck.slide("The problem", "Where we are today")
        left_w = Inches(7.6) if affected else W - 2 * MARGIN
        if statement:
            _text(s, MARGIN, Inches(1.85), left_w, Inches(1.6), statement, _size_for(statement, 22, 16), True, INK)
        if evidence:
            _text(s, MARGIN, Inches(3.55), left_w, Inches(0.3), "What tells us", 13, True, ACCENT)
            _bullets(s, MARGIN, Inches(3.9), left_w, Inches(2.8), evidence[:4],
                     15 if sum(map(len, evidence[:4])) < 420 else 13, MUTED)
        if affected:
            x = MARGIN + left_w + Inches(0.5)
            pw = W - MARGIN - x
            _rect(s, x, Inches(1.85), pw, Inches(4.8), ACCENT_TINT)
            _text(s, x + Inches(0.3), Inches(2.1), pw - Inches(0.6), Inches(0.3), "Who is affected", 13, True, ACCENT)
            _bullets(s, x + Inches(0.3), Inches(2.55), pw - Inches(0.6), Inches(4), affected[:6], 15, INK, ACCENT_DARK)

    # 4. Constraints
    constraints = [_quote(c) for c in content.get("constraints") or [] if _clean(c)]
    if constraints:
        s = deck.slide("What the solution must respect", "Constraints")
        shown = constraints[:6]
        cols = 2 if len(shown) > 3 else 1
        cw = (W - 2 * MARGIN - Inches(0.4) * (cols - 1)) / cols
        per_col = -(-len(shown) // cols)
        ch = min(Inches(1.4), (Inches(4.7) - Inches(0.25) * (per_col - 1)) / per_col)
        for i, c in enumerate(shown):
            col, row = divmod(i, per_col)
            x = MARGIN + (cw + Inches(0.4)) * col
            y = Inches(1.9) + (ch + Inches(0.25)) * row
            _rect(s, x, y, int(cw), int(ch), WHITE, line=LINE)
            _rect(s, x, y, Inches(0.08), int(ch), ACCENT)
            _text(s, x + Inches(0.3), y, Inches(0.6), int(ch), f"{i + 1:02d}", 24, True, ACCENT, anchor=MSO_ANCHOR.MIDDLE)
            _text(s, x + Inches(1.0), y + Inches(0.1), int(cw) - Inches(1.2), int(ch) - Inches(0.2), c,
                  _size_for(c, 17, 13, 160), color=INK, anchor=MSO_ANCHOR.MIDDLE)

    # 5. Proposed solution
    sol = content.get("proposed_solution") or {}
    if isinstance(sol, str):
        sol = {"approach": sol}
    approach, rationale = _clean(sol.get("approach")), _clean(sol.get("rationale"))
    if approach:
        s = deck.slide("What we propose", "The approach")
        aw = Inches(7.4) if rationale else W - 2 * MARGIN
        _text(s, MARGIN, Inches(1.9), aw, Inches(4.8), approach, _size_for(approach, 20, 14, 420), color=INK)
        if rationale:
            x = MARGIN + aw + Inches(0.5)
            pw = W - MARGIN - x
            _rect(s, x, Inches(1.85), pw, Inches(4.85), ACCENT)
            _text(s, x + Inches(0.35), Inches(2.1), pw - Inches(0.7), Inches(0.3), "Why this approach", 13, True, WHITE)
            _text(s, x + Inches(0.35), Inches(2.55), pw - Inches(0.7), Inches(4), rationale,
                  _size_for(rationale, 16, 12, 380), color=WHITE)

    # 6–9. Tables, paginated so nothing is squeezed off the slide
    def table_slides(key, heading, kicker, headers, widths, row_of, pill_col=-1):
        items = [i for i in content.get(key) or [] if isinstance(i, dict)]
        rows = [r for r in (row_of(i) for i in items) if any(c and c != "→" for c in r)]
        if not rows:
            return
        pages = _table_pages(rows, widths)
        for n, page in enumerate(pages, start=1):
            s = deck.slide(_heading(heading, n, len(pages)), kicker)
            deck.table(s, headers, page, widths, pill_col=pill_col)

    table_slides("components", "The building blocks", "Components", ["Component", "What it does", "Status"],
                 [3, 7, 1.4], lambda c: [_clean(c.get("name")), _clean(c.get("purpose")), _clean(c.get("new_or_existing"))],
                 pill_col=2)
    table_slides("integrations", "How the systems connect", "Integrations", ["From", "", "To", "What flows", "How"],
                 [2.6, 0.5, 2.6, 4.2, 1.6],
                 lambda i: [_clean(i.get("from")), "→", _clean(i.get("to")), _clean(i.get("data")), _clean(i.get("method"))])
    table_slides("alternatives", "Options we considered", "Alternatives", ["Option", "Why we did not choose it"],
                 [4, 7], lambda a: [_clean(a.get("option")), _clean(a.get("why_not"))])
    table_slides("risks", "Risks and how we handle them", "Risks", ["Risk", "Impact", "Mitigation"],
                 [4.5, 1.2, 5.5], lambda r: [_clean(r.get("risk")), _clean(r.get("impact")), _clean(r.get("mitigation"))],
                 pill_col=1)

    # 10. Roadmap as a phase timeline
    phases = [p for p in content.get("roadmap") or [] if isinstance(p, dict)]
    for n, page in enumerate(_pages(phases, 4) if phases else [], start=1):
        s = deck.slide(_heading("How we get there", n, -(-len(phases) // 4)), "Roadmap")
        count = len(page)
        gap = Inches(0.25)
        bw = (W - 2 * MARGIN - gap * (count - 1)) / count
        for i, p in enumerate(page):
            x = MARGIN + (bw + gap) * i
            _rect(s, x, Inches(1.95), int(bw), Inches(0.75), ACCENT,
                  shape=MSO_SHAPE.CHEVRON if count > 1 else MSO_SHAPE.RECTANGLE)
            _text(s, x + Inches(0.35), Inches(1.95), int(bw) - Inches(0.6), Inches(0.75),
                  _clean(p.get("phase")) or f"Phase {i + 1}", 16, True, WHITE, anchor=MSO_ANCHOR.MIDDLE)
            scope, outcome = _clean(p.get("scope")), _clean(p.get("outcome"))
            _rect(s, x, Inches(2.95), int(bw), Inches(3.75), SOFT_BG)
            _text(s, x + Inches(0.2), Inches(3.1), int(bw) - Inches(0.4), Inches(0.3), "Scope", 12, True, ACCENT)
            _text(s, x + Inches(0.2), Inches(3.4), int(bw) - Inches(0.4), Inches(1.9), scope,
                  _size_for(scope, 14, 11, 200), color=INK)
            if outcome:
                _text(s, x + Inches(0.2), Inches(5.3), int(bw) - Inches(0.4), Inches(0.3), "Outcome", 12, True, ACCENT)
                _text(s, x + Inches(0.2), Inches(5.6), int(bw) - Inches(0.4), Inches(1.0), outcome,
                      _size_for(outcome, 13, 11, 140), True, INK)

    # 11. What we need from you (the agent's open questions; never invented figures)
    needs = [_clean(q) for q in content.get("needs_info") or [] if _clean(q)]
    for n, page in enumerate(_pages(needs, 6) if needs else [], start=1):
        s = deck.slide(_heading("What we need from you", n, -(-len(needs) // 6)), "Open questions")
        _text(s, MARGIN, Inches(1.6), W - 2 * MARGIN, Inches(0.4),
              "These are not in the material we received. Answers here firm up the plan, cost and dates.", 14,
              color=MUTED)
        _bullets(s, MARGIN, Inches(2.25), W - 2 * MARGIN, Inches(4.5), page, 18)

    # 12. Discussion
    s = deck.prs.slides.add_slide(deck.blank)
    _rect(s, 0, 0, W, H, ACCENT)
    _text(s, MARGIN, Inches(2.6), W - 2 * MARGIN, Inches(1.2), "Discussion", 54, True, WHITE, display=True)
    first = _clean(phases[0].get("scope")) if phases else ""
    _text(s, MARGIN, Inches(3.8), W - 2 * MARGIN, Inches(1.6),
          f"Proposed first step: {first}" if first else name, _size_for(first or name, 20, 15, 160),
          color=WHITE)
    return deck.save()
