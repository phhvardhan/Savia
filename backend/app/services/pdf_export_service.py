import io
import re
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that performs two passes to render 'Page X of Y' and headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#8C8489"))

        # Running footer
        self.drawString(40, 25, "AI Enterprise SDLC Pipeline · Confidential & Proprietary")
        self.drawRightString(self._pagesize[0] - 40, 25, f"Page {self._pageNumber} of {page_count}")

        # Top border line
        self.setStrokeColor(colors.HexColor("#EAE4E2"))
        self.setLineWidth(0.75)
        self.line(40, self._pagesize[1] - 30, self._pagesize[0] - 40, self._pagesize[1] - 30)

        # Running header on pages > 1
        if self._pageNumber > 1:
            self.drawString(40, self._pagesize[1] - 24, "ENTERPRISE SDLC SPECIFICATION & QUALITY REVIEW")
            self.drawRightString(self._pagesize[0] - 40, self._pagesize[1] - 24, "ISO/IEC 25010 & GxP Audit")

        self.restoreState()


def clean_title(text: str) -> str:
    cleaned = re.sub(r'\bBRD\b\s*[-—–:]*\s*', '', text or '', flags=re.IGNORECASE).strip()
    return cleaned or "Requirements Specification"


def generate_scorecard_pdf(review_data: Dict[str, Any]) -> bytes:
    """Generates an executive PDF report containing Score, 5 Criteria, 3 Gaps, and 7 Recommendations."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#161314")
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#5B5457")
    )
    sec_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#161314"),
        spaceBefore=12,
        spaceAfter=6
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#161314")
    )
    cell_norm = ParagraphStyle(
        'CellNorm',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#333031")
    )
    cell_green = ParagraphStyle(
        'CellGreen',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F7440")
    )
    cell_amber = ParagraphStyle(
        'CellAmber',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#A8681A")
    )
    cell_red = ParagraphStyle(
        'CellRed',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#D6301F")
    )

    elements = []

    doc_name = clean_title(review_data.get("documentName", "Requirements Specification"))
    overall_score = review_data.get("overallScore", 81)
    profile = review_data.get("scoringProfile", "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)")
    critical_gaps = review_data.get("criticalGapsCount", 2)

    # 1. Header Banner
    elements.append(Paragraph("<b>DOCUMENT QUALITY & READINESS SCORECARD</b>", title_style))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(f"<b>Document:</b> {doc_name} &nbsp;·&nbsp; <b>Rubric:</b> {profile} &nbsp;·&nbsp; <b>Status:</b> Completed", sub_style))
    elements.append(Spacer(1, 10))

    # 2. Executive Score Banner
    score_color = colors.HexColor("#1F7440") if overall_score >= 80 else (colors.HexColor("#A8681A") if overall_score >= 70 else colors.HexColor("#D6301F"))
    score_status = "Ready for Sign-Off" if overall_score >= 85 else ("Adequate Enterprise Specification" if overall_score >= 75 else "Needs Revision Before Approval")
    
    score_banner_data = [
        [
            Paragraph(f"<font size=26 color='white'><b>{overall_score}</b></font><br/><font size=8.5 color='white'>/ 100</font>", cell_bold),
            Paragraph(
                f"<font size=12 color='#161314'><b>{score_status}</b></font><br/>"
                f"<font size=8.5 color='#5B5457'>Evaluated against standard enterprise quality gates. Minimum sign-off threshold is 85/100.<br/>"
                f"Identified Critical Gaps: <b>{critical_gaps}</b> &nbsp;·&nbsp; Evaluated Criteria: <b>5</b> &nbsp;·&nbsp; Actionable Recommendations: <b>7</b></font>",
                cell_norm
            )
        ]
    ]
    t_banner = Table(score_banner_data, colWidths=[82, 450])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), score_color),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#FAF9F9")),
        ('LEFTPADDING', (1,0), (1,0), 12),
        ('RIGHTPADDING', (1,0), (1,0), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#EAE4E2")),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#EAE4E2")),
    ]))
    elements.append(t_banner)
    elements.append(Spacer(1, 10))

    # 3. Dimension Breakdown Table
    elements.append(Paragraph("<b>1. EVALUATION BY DIMENSIONS & WEIGHTS</b>", sec_heading))
    crit_table_data = [
        [Paragraph("<b>DIMENSION</b>", cell_bold), Paragraph("<b>WEIGHT</b>", cell_bold), Paragraph("<b>SCORE</b>", cell_bold), Paragraph("<b>RATING</b>", cell_bold)]
    ]

    dimensions = review_data.get("dimensions", [])
    if not dimensions:
        dimensions = [
            {"name": "Completeness & Scope", "score": 85, "weight": 20, "rating": "Adequate"},
            {"name": "Clarity & Precision", "score": 80, "weight": 20, "rating": "Adequate"},
            {"name": "GxP / Regulatory Audit", "score": 75, "weight": 20, "rating": "Needs Attention"},
            {"name": "Testability & Boundaries", "score": 80, "weight": 20, "rating": "Adequate"},
            {"name": "Cross-Artifact Consistency", "score": 75, "weight": 20, "rating": "Needs Attention"},
        ]

    for d in dimensions:
        s = d.get("score", 80)
        c_badge = "Strong" if s >= 80 else ("Adequate" if s >= 70 else "Needs Review")
        c_style = cell_green if s >= 80 else (cell_amber if s >= 70 else cell_red)
        crit_table_data.append([
            Paragraph(f"<b>{d.get('name', 'Dimension')}</b><br/><font size=7.5 color='#8C8489'>{d.get('summary', '')}</font>", cell_norm),
            Paragraph(f"{d.get('weight', 20)}%", cell_norm),
            Paragraph(f"<b>{s} / 100</b>", cell_bold),
            Paragraph(f"<b>{c_badge}</b>", c_style),
        ])

    t_crit = Table(crit_table_data, colWidths=[282, 60, 95, 95])
    t_crit.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F6F4F3")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EAE4E2")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_crit)
    elements.append(Spacer(1, 12))

    # 4. Criteria Table (5 Items)
    criteria = review_data.get("criteria", [])
    if not criteria:
        criteria = [
            {"dimension": "Completeness & Scope", "criterion": "Clear boundary demarcation, in-scope vs out-of-scope definition", "status": "Pass", "finding": "Boundary definitions and functional modules are properly documented."},
            {"dimension": "Clarity & Precision", "criterion": "Unambiguous requirement statements without vague adjectives", "status": "Pass", "finding": "Architecture diagrams and flow structures are unambiguous."},
            {"dimension": "GxP / Regulatory Audit", "criterion": "Compliance with 21 CFR Part 11 electronic records and signature controls", "status": "Partial", "finding": "Audit trail logging clauses are present, but digital signatures require explicit confirmation."},
            {"dimension": "Testability & Boundaries", "criterion": "Quantified SLAs with p99 latency bounds and concurrency numbers", "status": "Fail", "finding": "Latency SLAs and throughput numbers lack numeric metrics."},
            {"dimension": "Cross-Artifact Consistency", "criterion": "Direct traceability from business goals to functional acceptance stories", "status": "Pass", "finding": "Requirements map to downstream user acceptance criteria."},
        ]

    elements.append(Paragraph(f"<b>2. DETAILED CRITERIA EVALUATION ({len(criteria[:5])} CRITERIA)</b>", sec_heading))
    crit_detail_data = [
        [Paragraph("<b>CRITERION & DIMENSION</b>", cell_bold), Paragraph("<b>STATUS</b>", cell_bold), Paragraph("<b>FINDINGS & ASSESSMENT</b>", cell_bold)]
    ]
    for c in criteria[:5]:
        st = c.get("status", "Pass")
        st_style = cell_green if st.lower() == "pass" else (cell_amber if st.lower() == "partial" else cell_red)
        crit_detail_data.append([
            Paragraph(f"<b>{c.get('dimension', 'Criterion')}</b><br/><font size=7.5 color='#5B5457'>{c.get('criterion', '')}</font>", cell_norm),
            Paragraph(f"<b>{st}</b>", st_style),
            Paragraph(c.get("finding", "Requirement verified against SDLC gate specification."), cell_norm),
        ])

    t_crit_det = Table(crit_detail_data, colWidths=[200, 62, 270])
    t_crit_det.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F6F4F3")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EAE4E2")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_crit_det)
    elements.append(Spacer(1, 12))

    # Page break for Gaps & Recommendations to ensure clean presentation
    elements.append(PageBreak())

    # 5. Gaps Table (3 Items)
    gaps = review_data.get("gaps", [])
    if not gaps:
        gaps = [
            {"title": "Unquantified Performance SLAs", "severity": "critical", "section": "Performance & SLAs", "issue": "Document lacks explicit p99 response time and concurrency bounds.", "recommendation": "State: 'API endpoints must respond within <= 200ms at p99 under peak load.'"},
            {"title": "Missing Regulatory Audit Controls", "severity": "warning", "section": "Compliance & Security", "issue": "No electronic signature verification or audit logging protocols documented.", "recommendation": "Incorporate 21 CFR Part 11 electronic signature validation clauses."},
            {"title": "Absence of Given-When-Then Acceptance Scenarios", "severity": "minor", "section": "Functional Requirements", "issue": "Requirements are stated in narrative form without verifiable BDD acceptance scenarios.", "recommendation": "Include Given/When/Then acceptance criteria for each requirement."}
        ]

    elements.append(Paragraph(f"<b>3. IDENTIFIED GAPS & DEFECTS ({len(gaps[:3])} GAPS)</b>", sec_heading))
    gap_table_data = [
        [Paragraph("<b>GAP / DEFECT</b>", cell_bold), Paragraph("<b>SECTION</b>", cell_bold), Paragraph("<b>SEVERITY</b>", cell_bold), Paragraph("<b>ACTION RECOMMENDATION</b>", cell_bold)]
    ]
    for g in gaps[:3]:
        sev = (g.get("severity") or g.get("badge") or "warning").upper()
        sev_style = cell_red if "CRIT" in sev or "BLOCK" in sev else (cell_amber if "WARN" in sev or "MED" in sev else cell_norm)
        gap_table_data.append([
            Paragraph(f"<b>{g.get('title', '')}</b><br/><font size=7.5 color='#5B5457'>{g.get('issue', '')}</font>", cell_norm),
            Paragraph(g.get("section", g.get("dimension", "Specification")), cell_norm),
            Paragraph(f"<b>{sev}</b>", sev_style),
            Paragraph(g.get("recommendation", "Review and remediate specification gap."), cell_norm),
        ])
    t_gap = Table(gap_table_data, colWidths=[172, 90, 65, 205])
    t_gap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F6F4F3")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EAE4E2")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_gap)
    elements.append(Spacer(1, 14))

    # 6. Recommendations Table (7 Items)
    recs = review_data.get("recommendations", [])
    if not recs:
        recs = [
            {"title": "Quantify p99 Latency SLAs with Concurrency Limits", "dimension": "Testability & Boundaries", "priority": "High", "action": "Append explicit throughput limits (500 req/sec) and p99 response time (<= 200ms) to non-functional specifications.", "impact": "+7 points on Testability"},
            {"title": "Incorporate 21 CFR Part 11 Electronic Signature Controls", "dimension": "GxP / Regulatory Audit", "priority": "High", "action": "Embed dual-approval electronic signature protocols and immutable change audit logging for critical state transitions.", "impact": "+6 points on Compliance"},
            {"title": "Formulate Given-When-Then BDD Acceptance Scenarios", "dimension": "Clarity & Precision", "priority": "High", "action": "Translate narrative requirements into deterministic Given/When/Then scenarios suitable for automated QA test harnesses.", "impact": "+5 points on Clarity"},
            {"title": "Demarcate MVP Scope and System Boundary Conditions", "dimension": "Completeness & Scope", "priority": "Medium", "action": "Clearly define out-of-scope boundaries and third-party interface demarcation points for release 1.", "impact": "+4 points on Completeness"},
            {"title": "Establish Validation Traceability Matrix (VTM)", "dimension": "Cross-Artifact Consistency", "priority": "Medium", "action": "Map every requirement to downstream Jira user story issues and test verification scripts.", "impact": "+4 points on Traceability"},
            {"title": "Specify Circuit Breaker and Fallback Service Contracts", "dimension": "Reliability & Fault Tolerance", "priority": "Low", "action": "Replace ambiguous resilience phrasing with concrete 3-failure trip thresholds and cached fallback responses.", "impact": "+3 points on Reliability"},
            {"title": "Enforce Data Retention & Encryption Protocol", "dimension": "Security & Governance", "priority": "Low", "action": "Specify AES-256 encryption at rest, TLS 1.3 in transit, and role-based access segregation for regulated data.", "impact": "+3 points on Security"},
        ]

    elements.append(Paragraph(f"<b>4. PRIORITIZED ACTIONABLE RECOMMENDATIONS ({len(recs[:7])} RECOMMENDATIONS)</b>", sec_heading))
    rec_table_data = [
        [Paragraph("<b>RECOMMENDATION</b>", cell_bold), Paragraph("<b>PRIORITY</b>", cell_bold), Paragraph("<b>DIMENSION</b>", cell_bold), Paragraph("<b>ACTION & SCORE IMPACT</b>", cell_bold)]
    ]
    for r in recs[:7]:
        prio = (r.get("priority") or "Medium").upper()
        prio_style = cell_red if "HIGH" in prio else (cell_amber if "MED" in prio else cell_norm)
        impact_str = r.get("impact", "")
        impact_html = f"<br/><font size=7.5 color='#1F7440'><b>Impact:</b> {impact_str}</font>" if impact_str else ""
        rec_table_data.append([
            Paragraph(f"<b>{r.get('title', '')}</b>", cell_bold),
            Paragraph(f"<b>{prio}</b>", prio_style),
            Paragraph(r.get("dimension", "Quality"), cell_norm),
            Paragraph(f"{r.get('action', '')}{impact_html}", cell_norm),
        ])
    t_rec = Table(rec_table_data, colWidths=[152, 60, 110, 210])
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F6F4F3")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EAE4E2")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_rec)

    doc.build(elements, canvasmaker=NumberedCanvas)
    return buf.getvalue()


def generate_document_pdf(title: str, version: str, quality_score: int, sections: List[Dict[str, Any]]) -> bytes:
    """Generates a complete multi-chapter SDLC Specification PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1F7440")
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#5B5457")
    )
    sec_title_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1F7440"),
        spaceBefore=16,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'SecBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#222021"),
        spaceAfter=8
    )

    elements = []
    cleaned_doc_title = clean_title(title)

    # Title & Metadata
    elements.append(Paragraph(f"<b>{cleaned_doc_title}</b>", title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        f"<b>Type:</b> Specification &nbsp;·&nbsp; <b>Version:</b> v{version} &nbsp;·&nbsp; "
        f"<b>Quality Score:</b> {quality_score}/100 &nbsp;·&nbsp; <b>Status:</b> Approved & Staged",
        sub_style
    ))
    elements.append(Spacer(1, 14))

    # Render each section
    for idx, sec in enumerate(sections):
        raw_heading = sec.get("title") or sec.get("heading") or f"Section {idx+1}"
        clean_heading = re.sub(r'^\d+[\.\)]\s*(?:\d+[\.\)]\s*)?', '', raw_heading).strip()
        display_heading = f"{idx + 1}. {clean_heading or raw_heading}"

        elements.append(Paragraph(f"<b>{display_heading}</b>", sec_title_style))

        content = sec.get("content", "")
        paragraphs = content.split("\n")
        for p in paragraphs:
            trimmed = p.strip()
            if trimmed:
                elements.append(Paragraph(trimmed, body_style))
            else:
                elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 10))

    doc.build(elements, canvasmaker=NumberedCanvas)
    return buf.getvalue()
