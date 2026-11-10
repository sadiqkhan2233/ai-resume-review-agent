"""Generate a downloadable PDF report with ReportLab."""
from datetime import date
from io import BytesIO
from typing import Dict, List, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .config import APP_NAME, DISCLAIMER
from .schemas import ResumeReview

_styles = getSampleStyleSheet()
TITLE = ParagraphStyle("T", parent=_styles["Title"], fontSize=20, textColor=colors.HexColor("#1e3a8a"))
H2 = ParagraphStyle("H2", parent=_styles["Heading2"], textColor=colors.HexColor("#1e3a8a"), spaceBefore=12)
BODY = ParagraphStyle("B", parent=_styles["BodyText"], fontSize=10, leading=14)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8.5, textColor=colors.HexColor("#555555"))
BULLET = ParagraphStyle("BL", parent=BODY, leftIndent=14, bulletIndent=4)


def _clean(text: object) -> str:
    """Escape XML and replace characters the built-in PDF font cannot draw."""
    text = str(text or "")
    for old, new in {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-", "\u2022": "-", "\u2026": "..."}.items():
        text = text.replace(old, new)
    text = text.encode("cp1252", "replace").decode("cp1252")
    return escape(text).replace("\n", "<br/>")


def _p(text: object, style=BODY) -> Paragraph:
    return Paragraph(_clean(text), style)


def _bullets(items: List[str]) -> List[Paragraph]:
    return [Paragraph(_clean(i), BULLET, bulletText="-") for i in items if str(i).strip()]


def _section(story: list, title: str, items: List[str]) -> None:
    if any(str(i).strip() for i in items):
        story.append(_p(title, H2))
        story.extend(_bullets(items))


def build_pdf_report(
    review: ResumeReview,
    rows: List[Dict],
    overall: float,
    grade: str,
    job_match: Optional[Dict],
    job_title: str = "",
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm, title="Resume Review Report")
    story: list = [_p(f"{APP_NAME} - Report", TITLE)]

    meta = f"Generated on {date.today():%d %B %Y}"
    if review.candidate_name:
        meta += f"  |  Candidate: {review.candidate_name}"
    if job_title or review.target_role:
        meta += f"  |  Target role: {job_title or review.target_role}"
    story += [_p(meta, SMALL), Spacer(1, 6), _p(DISCLAIMER, SMALL)]

    story.append(_p(f"Overall Score: {overall:g} / 100  ({grade})", H2))
    table_data = [[_p("Category", BODY), _p("Score", BODY), _p("Explanation", BODY)]]
    for r in rows:
        table_data.append([_p(r["label"], BODY), _p(f"{r['score']:g} / {r['max']}", BODY), _p(r["explanation"], SMALL)])
    table = Table(table_data, colWidths=[3.6 * cm, 2.2 * cm, 11.2 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9ca3af")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)

    if job_match:
        story.append(_p(f"Job Match Score: {job_match['percent']}%", H2))
        story.append(_p(job_match["formula"], SMALL))
        story.append(_p("Matching skills: " + (", ".join(job_match["matched"]) or "none"), BODY))
        story.append(_p("Missing skills: " + (", ".join(job_match["missing"]) or "none"), BODY))

    if review.section_analysis:
        story.append(_p("Section-by-Section Analysis", H2))
        for s in review.section_analysis:
            story.append(_p(f"{s.section} [{s.status}]: {s.feedback}", BODY))
            story.append(Spacer(1, 3))

    _section(story, "Strengths", review.strengths)
    _section(story, "Weaknesses", review.weaknesses)
    _section(story, "Missing Information", review.missing_information)
    _section(story, "Suggested Skills", review.suggested_skills)

    if review.rewritten_bullets:
        story.append(_p("Rewritten Bullet Points", H2))
        for b in review.rewritten_bullets:
            story.append(_p(f"Original: {b.original}", SMALL))
            story.append(_p(f"Improved: {b.improved}", BODY))
            if b.note:
                story.append(_p(f"Why: {b.note}", SMALL))
            story.append(Spacer(1, 5))

    if review.improved_summary:
        story.append(_p("Improved Professional Summary", H2))
        story.append(_p(review.improved_summary))

    _section(story, "Recommended Certifications", review.recommended_certifications)
    _section(story, "Education Suggestions", review.education_suggestions)
    _section(story, "Experience Suggestions", review.experience_suggestions)
    _section(story, "Job-Specific Recommendations", review.job_specific_recommendations)
    _section(story, "Action Plan", review.action_plan)

    story += [Spacer(1, 12), _p(DISCLAIMER, SMALL)]
    doc.build(story)
    return buffer.getvalue()
