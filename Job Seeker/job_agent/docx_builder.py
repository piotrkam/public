"""
DOCX builder — converts the Tailor agent's JSON output into Word documents
styled to match Piotr's resume template.

Layout reference
----------------
• Name:          ~26 pt, bold, ALL CAPS, centered
• HR rule:       full-width paragraph bottom-border (thick, before and after contact)
• Contact:       10 pt, centered
• Summary:       10 pt, left-aligned body text
• Section heads: 11 pt, bold, ALL CAPS, with full-width rule underneath
• Job row:       "Title, Company" bold left  |  "YYYY - YYYY" bold right (right tab)
• Bullets:       bullet char (•), bold label followed by colon, plain continuation text
• Skills:        bold category label, plain items — no bullet
• Margins:       1 inch all sides
• Font:          Calibri throughout

Expected JSON schema saved by the Tailor agent (content_{job_id}.json):

{
  "resume": {
    "name": "PIOTR KAMINSKI",
    "contact": "Krakow, Poland | email | phone | LinkedIn",
    "summary": "One tailored paragraph.",
    "experience": [
      {
        "title": "Lead Solutions Engineer",
        "company": "Luigi's Box",
        "period": "2025 - 2026",
        "bullets": [
          { "label": "Integration delivery", "text": "Led technical delivery..." },
          ...
        ]
      }
    ],
    "skills": [
      { "category": "Technical", "items": "REST APIs, Python, SQL" },
      { "category": "Soft",      "items": "Communication, Problem-Solving" },
      { "category": "Tools",     "items": "Postman, JIRA, Confluence" }
    ],
    "additional": [
      { "label": "Languages", "text": "English (C1), Polish (native)" }
    ]
  },
  "cover_letter": {
    "recipient_name": "Hiring Manager",
    "recipient_company": "Acme Corp",
    "paragraphs": ["Opening...", "Body 1...", "Body 2...", "Closing..."]
  },
  "notes": {
    "what_was_emphasised": [],
    "ats_keywords_used": [],
    "sections_reordered": true,
    "cover_letter_angle": "..."
  }
}

Bullet items may be supplied as either:
  { "label": "Bold label", "text": "rest of sentence" }   ← preferred
  "Plain string with no bold label"                        ← also accepted
"""

import json
from datetime import date
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsmap


FONT_NAME   = "Calibri"
BODY_SIZE   = Pt(10)
HEAD_SIZE   = Pt(11)
NAME_SIZE   = Pt(26)
MARGIN_IN   = Inches(1.0)
# Right-tab position = page width (8.27 in A4) minus two 1-in margins
RIGHT_TAB_TWIPS = int((8.27 - 2) * 1440)   # twips (1 in = 1440 twips)


# ── Low-level XML helpers ──────────────────────────────────────────────────────

def _add_bottom_border(paragraph, size_eighth_pt: int = 6, color: str = "000000") -> None:
    """Add a bottom border (rule line) to a paragraph."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    str(size_eighth_pt))   # 6 = 0.75 pt, 12 = 1.5 pt
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _add_right_tab(paragraph) -> None:
    """Add a right-aligned tab stop at the right margin."""
    pPr = paragraph._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:pos"), str(RIGHT_TAB_TWIPS))
    tabs.append(tab)
    pPr.append(tabs)


def _run(paragraph, text: str, bold: bool = False, size: object = BODY_SIZE,
         font: str = FONT_NAME) -> None:
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = font
    run.font.size = size


# ── Document-level helpers ─────────────────────────────────────────────────────

def _new_doc() -> Document:
    doc = Document()
    for section in doc.sections:
        section.top_margin    = MARGIN_IN
        section.bottom_margin = MARGIN_IN
        section.left_margin   = MARGIN_IN
        section.right_margin  = MARGIN_IN
    # Remove default styles' extra spacing
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = BODY_SIZE
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after  = Pt(0)
    return doc


def _hr_paragraph(doc: Document, space_before: int = 0, space_after: int = 4) -> None:
    """Empty paragraph whose bottom border acts as a horizontal rule."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    _add_bottom_border(p, size_eighth_pt=12)   # 1.5 pt thick line


def _section_heading(doc: Document, text: str) -> None:
    """ALL-CAPS bold heading with a rule line underneath."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(2)
    _add_bottom_border(p, size_eighth_pt=6)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.name = FONT_NAME
    run.font.size = HEAD_SIZE


# ── Resume builder ─────────────────────────────────────────────────────────────

def build_resume(data: dict, output_path: Path) -> None:
    doc = _new_doc()
    r   = data["resume"]

    # ── Name ──────────────────────────────────────────────────
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(r["name"].upper())
    run.bold = True
    run.font.name = FONT_NAME
    run.font.size = NAME_SIZE

    # ── HR + contact + HR ─────────────────────────────────────
    _hr_paragraph(doc, space_before=0, space_after=6)

    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_p.paragraph_format.space_after = Pt(6)
    _run(contact_p, r["contact"])

    _hr_paragraph(doc, space_before=0, space_after=8)

    # ── Summary ───────────────────────────────────────────────
    summary_p = doc.add_paragraph(r["summary"])
    summary_p.paragraph_format.space_after = Pt(4)
    for run in summary_p.runs:
        run.font.name = FONT_NAME
        run.font.size = BODY_SIZE

    # ── SKILLS ────────────────────────────────────────────────
    if r.get("skills"):
        _section_heading(doc, "Skills")
        for skill in r["skills"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            _run(p, skill["category"] + ": ", bold=True)
            _run(p, skill["items"])

    # ── RECENT EXPERIENCE ─────────────────────────────────────
    if r.get("experience"):
        _section_heading(doc, "Recent Experience")

        for job in r["experience"]:
            # "Title, Company    <TAB>    YYYY - YYYY"
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after  = Pt(2)
            _add_right_tab(p)
            _run(p, f"{job['title']}, {job['company']}", bold=True, size=HEAD_SIZE)
            _run(p, "\t")
            _run(p, job["period"], bold=True, size=HEAD_SIZE)

            # Bullets
            for bullet in job.get("bullets", []):
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.left_indent  = Inches(0.25)
                bp.paragraph_format.first_line_indent = Inches(-0.25)
                bp.paragraph_format.space_after  = Pt(3)

                if isinstance(bullet, dict):
                    _run(bp, bullet["label"] + ": ", bold=True)
                    _run(bp, bullet["text"])
                else:
                    _run(bp, str(bullet))

    # ── ADDITIONAL INFORMATION ────────────────────────────────
    additional = r.get("additional") or r.get("languages")
    if additional:
        _section_heading(doc, "Additional Information")
        # Normalise: accept list of dicts OR list of plain strings
        for item in additional:
            bp = doc.add_paragraph(style="List Bullet")
            bp.paragraph_format.left_indent       = Inches(0.25)
            bp.paragraph_format.first_line_indent = Inches(-0.25)
            bp.paragraph_format.space_after       = Pt(3)
            if isinstance(item, dict):
                _run(bp, item.get("label", "") + ": ", bold=True)
                _run(bp, item.get("text", ""))
            else:
                _run(bp, str(item))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


# ── Cover letter builder ───────────────────────────────────────────────────────

def build_cover_letter(data: dict, candidate_name: str, candidate_contact: str,
                       output_path: Path) -> None:
    doc = _new_doc()
    cl  = data["cover_letter"]

    # Sender block
    p = doc.add_paragraph()
    _run(p, candidate_name + "\n", bold=True, size=Pt(12))
    _run(p, candidate_contact)
    p.paragraph_format.space_after = Pt(12)

    # Date
    date_p = doc.add_paragraph(date.today().strftime("%-d %B %Y"))
    date_p.paragraph_format.space_after = Pt(6)
    for run in date_p.runs:
        run.font.name = FONT_NAME
        run.font.size = BODY_SIZE

    # Recipient
    recipient_name    = cl.get("recipient_name", "Hiring Manager")
    recipient_company = cl.get("recipient_company", "")
    rec_text = recipient_name + ("\n" + recipient_company if recipient_company else "")
    rec_p = doc.add_paragraph(rec_text)
    rec_p.paragraph_format.space_after = Pt(12)
    for run in rec_p.runs:
        run.font.name = FONT_NAME
        run.font.size = BODY_SIZE

    # Salutation
    sal_p = doc.add_paragraph(f"Dear {recipient_name},")
    sal_p.paragraph_format.space_after = Pt(10)
    for run in sal_p.runs:
        run.font.name = FONT_NAME
        run.font.size = BODY_SIZE

    # Body paragraphs
    for para_text in cl.get("paragraphs", []):
        p = doc.add_paragraph(para_text)
        p.paragraph_format.space_after  = Pt(10)
        p.paragraph_format.line_spacing = 1.15
        for run in p.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(11)

    # Sign-off
    sign_p = doc.add_paragraph("Best regards,")
    sign_p.paragraph_format.space_after = Pt(20)
    for run in sign_p.runs:
        run.font.name = FONT_NAME
        run.font.size = BODY_SIZE

    doc.add_paragraph(candidate_name).runs[0].font.name = FONT_NAME

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


# ── Main entry point ───────────────────────────────────────────────────────────

def build_documents(content_file: Path, cv_output: Path, letter_output: Path) -> None:
    """Read the Tailor agent's content JSON and write both DOCX files."""
    content = json.loads(content_file.read_text(encoding="utf-8"))

    resume            = content.get("resume", {})
    candidate_name    = resume.get("name", "Candidate")
    candidate_contact = resume.get("contact", "")

    build_resume(content, cv_output)
    build_cover_letter(content, candidate_name, candidate_contact, letter_output)
