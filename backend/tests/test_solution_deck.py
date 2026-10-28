import io

from pptx import Presentation

from app.core.deck import solution_to_pptx


def _slides(content):
    return Presentation(io.BytesIO(solution_to_pptx(content, "Prepared with SAVIA"))).slides


def test_full_blueprint_gets_one_slide_per_section():
    content = {
        "title": "Solution Blueprint: Stock sync",
        "executive_summary": "Move from a nightly file to events.",
        "problem": {"statement": "Stock is a day late.", "evidence": ["'nightly batch'"], "affected": ["Planners"]},
        "constraints": ["GxP audit trail"],
        "proposed_solution": {"approach": "Event-driven sync.", "rationale": "Removes the delay."},
        "components": [{"name": "Middleware", "purpose": "Maps events", "new_or_existing": "New"}],
        "integrations": [{"from": "WMS", "to": "SAP", "data": "Stock moves", "method": "event"}],
        "alternatives": [{"option": "Hourly batch", "why_not": "Still late"}],
        "risks": [{"risk": "Volume", "impact": "High", "mitigation": "Queue"}],
        "roadmap": [{"phase": "Phase 1", "scope": "Pilot", "outcome": "Live at one site"}],
        "needs_info": ["Daily volumes?"],
    }
    # title + 10 sections + discussion
    assert len(_slides(content)) == 12


def test_missing_sections_are_skipped_not_padded():
    assert len(_slides({"title": "Solution Blueprint: X", "executive_summary": "Only this."})) == 3
