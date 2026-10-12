from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

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

