import io
from typing import Any

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE_COLUMNS = [
    "Person Assigned To",
    "Summary",
    "Description",
    "Acceptance Criteria",
    "Reasoning",
]


def build_excel(stories: list[dict], out_path: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "User Stories"

    # Collect custom column headers across all stories
    custom_keys = []
    for s in stories:
        cf = s.get("custom_fields", {})
        if isinstance(cf, dict):
            for k in cf.keys():
                if k not in custom_keys:
                    custom_keys.append(k)

    all_headers = BASE_COLUMNS + custom_keys

    for col_idx, header in enumerate(all_headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)

    for row_idx, story in enumerate(stories, start=2):
        ac = story.get("acceptance_criteria", [])
        ac_text = "\n".join(f"- {c}" for c in ac) if isinstance(ac, list) else str(ac)
        values = [
            story.get("person_assigned_to", ""),
            story.get("summary", ""),
            story.get("description", ""),
            ac_text,
            story.get("reasoning", ""),
        ]
        
        # Add custom field values
        cf = story.get("custom_fields", {})
        for ck in custom_keys:
            val = cf.get(ck, "") if isinstance(cf, dict) else ""
            values.append(val)

        for col_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    widths = [20, 30, 50, 50, 40] + [25] * len(custom_keys)
    for i, w in enumerate(widths, start=1):
        # Support up to AA, AB if many columns
        col_letter = chr(64 + i) if i <= 26 else f"A{chr(64 + i - 26)}"
        ws.column_dimensions[col_letter].width = w

    wb.save(out_path)
    return out_path



# ---------------------------------------------------------------------------
# Agent artifact exports (Word + Excel), styled after the earlier SAVIA build.
# Agent outputs are JSON: strings, lists of strings, lists of records, nested
# objects. One renderer per format handles every agent.
# ---------------------------------------------------------------------------
_NAVY = RGBColor(15, 23, 42)
_SLATE = RGBColor(71, 85, 105)
_BODY = RGBColor(30, 41, 59)


def _label(key: str) -> str:
    return str(key).replace("_", " ").strip().capitalize()


def _cell_text(value: Any) -> str:
    """Flatten a value into readable cell text (no raw JSON)."""
    if value is None or (isinstance(value, str) and value.strip().lower() in {"none", "null", "n/a"}):
        return ""
    if isinstance(value, dict):
        keys = {k.lower() for k in value}
        if {"given", "when", "then"} <= keys:
            return f"Given {value.get('given', '')}\nWhen {value.get('when', '')}\nThen {value.get('then', '')}"
        return "\n".join(f"{_label(k)}: {_cell_text(v)}" for k, v in value.items() if v not in (None, "", [], {}))
    if isinstance(value, list):
        return "\n".join(f"• {_cell_text(v)}" if not isinstance(v, dict) else _cell_text(v) for v in value)
    return str(value)


def _record_columns(rows: list[dict]) -> list[str]:
    cols: list[str] = []
    for row in rows:
        for k in row:
            if k not in cols:
                cols.append(k)
    return cols


def _is_records(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(v, dict) for v in value)


def _unique_sections(content: dict) -> list[tuple[str, Any]]:
    """Top-level sections, skipping alias keys that repeat an earlier section
    (MOM stores decisions under both "decisions" and "decisions_finalized")."""
    seen: list[Any] = []
    out = []
    for key, value in content.items():
        if value in seen:
            continue
        seen.append(value)
        out.append((key, value))
    return out


def artifact_to_docx(title: str, subtitle: str, content: dict) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    style.font.color.rgb = _BODY

    t = doc.add_paragraph().add_run(title)
    t.font.size, t.font.bold, t.font.color.rgb = Pt(22), True, _NAVY
    s = doc.add_paragraph().add_run(subtitle)
    s.font.size, s.font.italic, s.font.color.rgb = Pt(10), True, _SLATE

    def heading(text: str, level: int):
        h = doc.add_heading(text, level=level)
        for run in h.runs:
            run.font.color.rgb = _NAVY

    def table(rows: list[dict]):
        cols = _record_columns(rows)
        tbl = doc.add_table(rows=1, cols=len(cols))
        tbl.style = "Table Grid"
        for i, col in enumerate(cols):
            cell = tbl.rows[0].cells[i]
            cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="1E293B"/>'))
            run = cell.paragraphs[0].add_run(_label(col))
            run.font.bold, run.font.size, run.font.color.rgb = True, Pt(9.5), RGBColor(255, 255, 255)
        for r_idx, row in enumerate(rows):
            cells = tbl.add_row().cells
            for i, col in enumerate(cols):
                if r_idx % 2 == 0:
                    cells[i]._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>'))
                cells[i].paragraphs[0].add_run(_cell_text(row.get(col))).font.size = Pt(9.5)
        doc.add_paragraph()

    def render(key: str, value: Any, level: int):
        if value in (None, "", [], {}):
            return
        heading(_label(key), min(level, 4))
        if _is_records(value):
            table(value)
        elif isinstance(value, list):
            for item in value:
                doc.add_paragraph(_cell_text(item), style="List Bullet")
        elif isinstance(value, dict):
            for k, v in value.items():
                render(k, v, level + 1)
        else:
            doc.add_paragraph(str(value))

    for key, value in _unique_sections(content):
        render(key, value, 1)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def artifact_has_records(content: dict) -> bool:
    return any(_is_records(v) for v in content.values())


def artifact_to_xlsx(title: str, subtitle: str, content: dict) -> bytes:
    """One sheet per list of records (stories, action items, test cases, RTM rows…)."""
    sections = [(k, v) for k, v in _unique_sections(content) if _is_records(v)]
    if not sections:
        raise ValueError("This output has no tables to export to Excel.")

    header_fill = PatternFill("solid", start_color="1E293B")
    zebra = PatternFill("solid", start_color="F8FAFC")
    side = Side(border_style="thin", color="CBD5E1")
    border = Border(left=side, right=side, top=side, bottom=side)
    priority_styles = {
        "high": ("FEE2E2", "991B1B"), "critical": ("FEE2E2", "991B1B"),
        "medium": ("FEF3C7", "92400E"), "low": ("E0F2FE", "075985"),
    }

    wb = Workbook()
    wb.remove(wb.active)
    for key, rows in sections:
        ws = wb.create_sheet(_label(key)[:31])  # Excel caps sheet names at 31 chars
        cols = _record_columns(rows)
        ws.cell(row=1, column=1, value=title).font = Font(size=16, bold=True, color="0F172A")
        ws.cell(row=2, column=1, value=f"{subtitle} · {len(rows)} rows").font = Font(size=10, italic=True, color="64748B")

        for c, col in enumerate(cols, start=1):
            cell = ws.cell(row=4, column=c, value=_label(col))
            cell.fill, cell.border = header_fill, border
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(vertical="center", wrap_text=True)

        for r, row in enumerate(rows, start=5):
            for c, col in enumerate(cols, start=1):
                text = _cell_text(row.get(col))
                cell = ws.cell(row=r, column=c, value=text)
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if (r - 5) % 2 == 0:
                    cell.fill = zebra
                if col.lower() in {"priority", "severity"} and text.lower() in priority_styles:
                    fill, color = priority_styles[text.lower()]
                    cell.fill = PatternFill("solid", start_color=fill)
                    cell.font = Font(bold=True, color=color)

        # Width from content, capped so long criteria wrap instead of running off.
        for c, col in enumerate(cols, start=1):
            longest = max([len(_label(col))] + [max((len(line) for line in _cell_text(row.get(col)).split("\n")), default=0) for row in rows])
            ws.column_dimensions[get_column_letter(c)].width = min(max(12, longest + 2), 60)
        ws.freeze_panes = "A5"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
