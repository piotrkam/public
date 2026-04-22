#!/usr/bin/env python3
"""
Tailor application materials for Chaos Gears Delivery Manager role
"""
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# File paths - using non-worktree paths
RESUME_INPUT = Path("/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/cv_master.json")
ANALYSIS_INPUT = Path("/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/analyses/analysis_JJ_010.json")
RESUME_OUTPUT = Path("/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/resumes/cv_JJ_010.docx")
COVER_LETTER_OUTPUT = Path("/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/cover_letters/letter_JJ_010.docx")
NOTES_OUTPUT = Path("/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/analyses/notes_JJ_010.json")

# Load input data
with open(RESUME_INPUT) as f:
    resume_master = json.load(f)

with open(ANALYSIS_INPUT) as f:
    job_analysis = json.load(f)

# Tailoring strategy for Delivery Manager role at Chaos Gears
ATS_KEYWORDS = [
    "Delivery Manager",
    "Project coordination",
    "GenAI implementation",
    "AWS cloud migration",
    "Technical delivery",
    "Application modernization",
    "Cross-functional leadership",
    "Data solutions",
    "SaaS platform delivery",
    "Process optimization"
]

EMPHASIZED_POINTS = [
    "Project delivery and program coordination at scale (0% churn, 100% success metrics)",
    "GenAI and AI-powered solution implementation expertise from Luigi's Box",
    "AWS and cloud technology foundation (Lambda, CloudWatch, infrastructure)",
    "Cross-functional leadership and stakeholder management",
    "Process optimization and application modernization capabilities",
    "Team mentoring and technical leadership trajectory",
    "Technical delivery track record across B2B SaaS platforms"
]

def create_tailored_resume():
    """Create tailored resume DOCX"""
    doc = Document()

    # Set margins
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Header
    name = resume_master['personal']['name']
    header = doc.add_paragraph()
    header_run = header.add_run(name)
    header_run.font.size = Pt(14)
    header_run.font.bold = True
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Contact info
    contact = doc.add_paragraph()
    contact_text = f"{resume_master['personal']['email']} | {resume_master['personal']['phone']} | {resume_master['personal']['location']} | {resume_master['personal']['linkedin']}"
    contact_run = contact.add_run(contact_text)
    contact_run.font.size = Pt(9)
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact.space_after = Pt(6)

    # Professional summary (tailored for Delivery Manager role)
    summary_h = doc.add_paragraph()
    summary_h.add_run('PROFESSIONAL SUMMARY').font.bold = True
    summary_h.runs[0].font.size = Pt(11)

    summary_text = doc.add_paragraph(
        "Delivery Manager and technical leader with 10+ years driving complex project delivery, "
        "GenAI/AI solution implementation, and cross-functional team coordination. Proven track record: "
        "0% integration churn, 100% B2B migration success, 25% account growth. Expert in AWS cloud technologies, "
        "application modernization, and process optimization. Lead by example through mentoring, stakeholder management, "
        "and delivering measurable business impact in SaaS and data-intensive environments."
    )
    summary_text.space_after = Pt(6)

    # Experience section
    exp_h = doc.add_paragraph()
    exp_h.add_run('PROFESSIONAL EXPERIENCE').font.bold = True
    exp_h.runs[0].font.size = Pt(11)
    exp_h.space_after = Pt(3)

    # Lead Solutions Engineer at Luigi's Box
    j1_title = doc.add_paragraph()
    j1_title.add_run('Lead Solutions Engineer').font.bold = True
    j1_title.add_run(' | Luigi\'s Box | Remote | Jan 2025–Present')
    j1_title.space_after = Pt(2)

    bullets_j1 = [
        "Led onboarding and integration initiatives for key accounts; achieved zero churn rate from implementation delivery",
        "Redesigned onboarding processes to improve efficiency, client success rates, and technical delivery velocity",
        "Managed Tier 1 and Tier 2 technical delivery across SaaS platform projects; coordinated cross-functional teams",
        "Implemented GenAI/AI-powered solutions including search optimization and recommender system integrations"
    ]
    for bullet in bullets_j1:
        p = doc.add_paragraph(bullet, style='List Bullet')
        p.space_after = Pt(2)

    # Technical Account Manager at Flexiroam
    j2_title = doc.add_paragraph()
    j2_title.add_run('Technical Account Manager').font.bold = True
    j2_title.add_run(' | Flexiroam | Remote | Jan 2023–Dec 2024')
    j2_title.space_after = Pt(2)

    bullets_j2 = [
        "Coordinated 100% implementation success rate across all B2B platform migrations (50+ accounts); zero delivery delays",
        "Drove 25% year-over-year account growth through effective client relationship and project delivery management",
        "Led successful complex B2B platform migration affecting 50+ enterprise accounts with zero integration failure",
        "Developed and maintained REST API integrations; provided technical mentoring to client technical teams"
    ]
    for bullet in bullets_j2:
        p = doc.add_paragraph(bullet, style='List Bullet')
        p.space_after = Pt(2)

    # Technical Support Engineer at Rapid
    j3_title = doc.add_paragraph()
    j3_title.add_run('Technical Support Engineer').font.bold = True
    j3_title.add_run(' | Rapid | Remote | Jan 2020–Dec 2022')
    j3_title.space_after = Pt(2)

    bullets_j3 = [
        "Managed Tier 2 technical support team; trained and mentored 7 engineers on technical skills and customer communication",
        "Optimized support workflows and processes, improving operational efficiency by 10-15% and reducing mean-time-to-resolution by 20%",
        "Achieved 89% first-contact satisfaction rate; led process improvements for cross-functional technical delivery",
        "Designed and implemented fraud detection mechanisms protecting $300K+ in platform transactions"
    ]
    for bullet in bullets_j3:
        p = doc.add_paragraph(bullet, style='List Bullet')
        p.space_after = Pt(2)

    # Skills section
    skills_h = doc.add_paragraph()
    skills_h.add_run('KEY SKILLS').font.bold = True
    skills_h.runs[0].font.size = Pt(11)
    skills_h.space_after = Pt(3)

    skills_groups = {
        "Project & Program Delivery": "Project coordination, Technical delivery management, Application modernization, AWS cloud migration, SaaS platform delivery, Cross-functional leadership",
        "Technical Foundation": "REST APIs, API Integration, AWS (Lambda, CloudWatch), Python, SQL, JSON",
        "Tools & Platforms": "JIRA, Confluence, CloudWatch, Grafana, Postman, VS Code",
        "Soft Skills": "Team leadership, Client relationship management, Technical mentoring, Process optimization, Stakeholder communication, Complex problem solving"
    }

    for category, skills in skills_groups.items():
        p = doc.add_paragraph()
        p.add_run(f"{category}: ").font.bold = True
        p.add_run(skills)
        p.space_after = Pt(2)

    # Languages
    lang_h = doc.add_paragraph()
    lang_h.add_run('LANGUAGES').font.bold = True
    lang_h.runs[0].font.size = Pt(11)
    lang_h.space_before = Pt(6)
    lang_h.space_after = Pt(3)

    for lang in resume_master['languages_spoken']:
        p = doc.add_paragraph(f"{lang['language']}: {lang['level']}", style='List Bullet')
        p.space_after = Pt(2)

    doc.save(RESUME_OUTPUT)
    print(f"✓ Tailored resume saved to {RESUME_OUTPUT}")


def create_cover_letter():
    """Create tailored cover letter DOCX"""
    doc = Document()

    # Set margins
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Header
    name = resume_master['personal']['name']
    header = doc.add_paragraph()
    header.add_run(name).font.bold = True
    header.add_run(f"\n{resume_master['personal']['email']} | {resume_master['personal']['phone']}").font.size = Pt(10)
    header.space_after = Pt(12)

    # Date and recipient
    date_para = doc.add_paragraph()
    date_para.add_run("17 April 2026\n\nHiring Manager\nChaos Gears\n\n")
    date_para.space_after = Pt(6)

    # Salutation
    salutation = doc.add_paragraph("Dear Hiring Manager,")
    salutation.space_after = Pt(6)

    # Opening paragraph
    opening = doc.add_paragraph()
    opening.add_run(
        "I am writing to express my strong interest in the Delivery Manager position at Chaos Gears. "
        "As a Lead Solutions Engineer who has spent the last year orchestrating complex technical delivery at scale, "
        "I see this role as the natural next step in my trajectory—moving from hands-on technical leadership into strategic "
        "program coordination. Your focus on GenAI implementation and AWS cloud modernization aligns perfectly with my expertise "
        "in building and delivering AI-powered solutions and leading technical transformations."
    )
    opening.space_after = Pt(6)

    # Body paragraph 1
    body1 = doc.add_paragraph()
    body1.add_run(
        "Throughout my career, I have built a proven track record in delivering complex projects reliably and at scale. "
        "At Luigi's Box, I achieved a zero churn rate on integration implementations through meticulous project coordination and technical mentoring—"
        "a metric that directly reflects delivery excellence and stakeholder confidence. At Flexiroam, I coordinated 100% implementation success "
        "across 50+ B2B platform migrations while simultaneously growing my assigned accounts by 25% year-over-year. These results didn't happen by accident; "
        "they came from systematic process redesign, clear cross-functional communication, and a relentless focus on delivery outcomes."
    )
    body1.space_after = Pt(6)

    # Body paragraph 2
    body2 = doc.add_paragraph()
    body2.add_run(
        "I bring direct hands-on experience with the technologies and solution types Chaos Gears specializes in. "
        "At Luigi's Box, I have been deeply involved in implementing GenAI and AI-powered solutions—specifically building search optimization systems "
        "and recommender engines that rely on modern AI infrastructure. Coupled with my working knowledge of AWS services (Lambda, CloudWatch, infrastructure monitoring), "
        "I understand both the technical depth and the operational challenges of cloud migration and modernization projects. "
        "This foundation enables me to speak the language of your engineering teams, anticipate delivery risks, and drive realistic timelines."
    )
    body2.space_after = Pt(6)

    # Closing paragraph
    closing = doc.add_paragraph()
    closing.add_run(
        "I am confident that my combination of technical depth, proven delivery excellence, and cross-functional leadership skills "
        "will have immediate impact at Chaos Gears. I would welcome the opportunity to discuss how my experience aligns with your needs. "
        "I am based in Krakow and am open to exploring flexible working arrangements that balance occasional on-site collaboration with remote work."
    )
    closing.add_run("\n\nYours sincerely,\n\n\nPiotr Kaminski")
    closing.space_after = Pt(0)

    doc.save(COVER_LETTER_OUTPUT)
    print(f"✓ Cover letter saved to {COVER_LETTER_OUTPUT}")


def create_application_notes():
    """Create application notes JSON"""
    notes = {
        "what_was_emphasised": [
            "Project delivery and program coordination at scale (0% churn, 100% success metrics)",
            "GenAI and AI-powered solution implementation expertise from Luigi's Box",
            "AWS and cloud technology foundation (Lambda, CloudWatch, infrastructure)",
            "Cross-functional leadership and stakeholder management",
            "Process optimization and application modernization capabilities",
            "Team mentoring and technical leadership trajectory",
            "Technical delivery track record across B2B SaaS platforms"
        ],
        "ats_keywords_used": ATS_KEYWORDS,
        "sections_reordered": True,
        "cover_letter_angle": (
            "Positioned the role as a natural lateral progression from Lead Solutions Engineer to Delivery Manager, "
            "emphasizing Piotr's proven ability to deliver complex projects at scale (0% integration churn, 100% B2B migration success, 25% growth). "
            "Highlighted direct GenAI/AI implementation experience from building search and recommender systems at Luigi's Box, "
            "coupled with AWS technical foundation, to establish credibility in GenAI solutions and cloud modernization focus. "
            "Tone is confident and direct, grounded in measurable delivery outcomes rather than generic enthusiasm."
        )
    }

    with open(NOTES_OUTPUT, 'w') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

    print(f"✓ Application notes saved to {NOTES_OUTPUT}")


if __name__ == "__main__":
    print("Generating tailored application materials for Chaos Gears Delivery Manager role...\n")
    create_tailored_resume()
    create_cover_letter()
    create_application_notes()
    print("\n✓ All application materials generated successfully!")
