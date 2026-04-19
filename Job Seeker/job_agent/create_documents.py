#!/usr/bin/env python3
"""
Create tailored resume and cover letter DOCX files using python-docx
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import json

def create_resume():
    """Create the tailored resume DOCX file"""
    doc = Document()

    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Header with name
    name = doc.add_paragraph()
    name_run = name.add_run("PIOTR KAMINSKI")
    name_run.font.size = Pt(16)
    name_run.font.bold = True
    name.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Contact information
    contact = doc.add_paragraph()
    contact_text = "piotrkaminski1@protonmail.com | +48 510 934 702 | Krakow, Poland | LinkedIn"
    contact.add_run(contact_text)
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_format = contact.paragraph_format
    contact_format.space_after = Pt(6)

    # Professional Summary
    summary_heading = doc.add_paragraph()
    summary_run = summary_heading.add_run("PROFESSIONAL SUMMARY")
    summary_run.font.bold = True
    summary_run.font.size = Pt(11)

    summary_text = doc.add_paragraph(
        "Delivery-focused technical leader with 6+ years driving project coordination, cross-functional team leadership, "
        "and GenAI/AI implementation across cloud platforms. Proven track record of systematic delivery excellence: zero churn "
        "rate on implementation delivery, 100% success across 50+ B2B platform migrations, and 25% YoY account growth. Expertise "
        "in AWS cloud infrastructure, REST API integration, and technical team mentoring. Passionate about optimizing processes "
        "and enabling team success through clear communication and strategic oversight."
    )
    summary_text.paragraph_format.space_after = Pt(12)
    summary_text.paragraph_format.line_spacing = 1.15

    # Experience section
    exp_heading = doc.add_paragraph()
    exp_run = exp_heading.add_run("PROFESSIONAL EXPERIENCE")
    exp_run.font.bold = True
    exp_run.font.size = Pt(11)

    # Job 1: Lead Solutions Engineer
    job1 = doc.add_paragraph()
    job1_title = job1.add_run("Lead Solutions Engineer")
    job1_title.font.bold = True
    job1.add_run(" | Luigi's Box | Jan 2025 – Present")

    job1_bullets = [
        "Led onboarding and integration initiatives for key accounts, achieving zero churn rate from implementation delivery. Redesigned onboarding processes to improve efficiency and client success outcomes.",
        "Managed Tier 1/2 technical delivery across multiple concurrent projects; coordinated cross-functional teams (engineering, product, support) to ensure seamless project execution.",
        "Implemented GenAI/AI-powered solutions including search optimization and recommender systems to enhance product capabilities.",
        "Mentored junior team members on technical delivery best practices and customer-centric approaches."
    ]

    for bullet in job1_bullets:
        p = doc.add_paragraph(bullet, style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15

    # Job 2: Technical Account Manager
    job2 = doc.add_paragraph()
    job2_title = job2.add_run("Technical Account Manager")
    job2_title.font.bold = True
    job2.add_run(" | Flexiroam | Jan 2023 – Dec 2024")

    job2_bullets = [
        "Coordinated 100% implementation success rate across all B2B platform migrations (50+ accounts) with zero integration failures. Drove 25% YoY account growth through effective client relationship management and proactive project delivery oversight.",
        "Led complex B2B platform migration affecting 50+ enterprise accounts with custom requirements; managed technical dependencies, timeline coordination, and stakeholder communication.",
        "Developed and maintained REST API integrations for third-party systems; provided ongoing technical mentoring to client engineering teams and internal support staff."
    ]

    for bullet in job2_bullets:
        p = doc.add_paragraph(bullet, style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15

    # Job 3: Technical Support Engineer
    job3 = doc.add_paragraph()
    job3_title = job3.add_run("Technical Support Engineer")
    job3_title.font.bold = True
    job3.add_run(" | Rapid | Jan 2020 – Dec 2022")

    job3_bullets = [
        "Managed Tier 2 technical support team, training and mentoring 7 engineers on escalation handling and customer-centric support delivery.",
        "Optimized support workflows and processes, improving team efficiency by 10–15% and reducing mean-time-to-resolution by 20%. Achieved 89% first-contact resolution satisfaction rating through process standardization and team skill development.",
        "Led cross-functional process improvement initiatives with product and engineering teams to address systemic issues.",
        "Designed and implemented fraud detection mechanisms protecting $300K+ in transactions."
    ]

    for bullet in job3_bullets:
        p = doc.add_paragraph(bullet, style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15

    # Skills section
    skills_heading = doc.add_paragraph()
    skills_run = skills_heading.add_run("CORE COMPETENCIES")
    skills_run.font.bold = True
    skills_run.font.size = Pt(11)

    skills_categories = [
        ("Project & Program Delivery", "Project coordination, Technical delivery, AWS cloud migration, SaaS platform delivery, Cross-functional leadership, Delivery management, Process optimization"),
        ("Technical Skills", "REST APIs, API integration, AWS Lambda, AWS CloudWatch, Python, SQL, JSON"),
        ("Tools & Platforms", "JIRA, Confluence, AWS CloudWatch, Grafana"),
        ("Leadership & Soft Skills", "Team leadership, Client management, Technical mentoring, Process optimization, Stakeholder communication"),
    ]

    for category, skills in skills_categories:
        skill_para = doc.add_paragraph(style='List Bullet')
        skill_run = skill_para.add_run(category + ": ")
        skill_run.bold = True
        skill_para.add_run(skills)
        skill_para.paragraph_format.left_indent = Inches(0.25)
        skill_para.paragraph_format.line_spacing = 1.15

    # Languages section
    lang_heading = doc.add_paragraph()
    lang_run = lang_heading.add_run("LANGUAGES")
    lang_run.font.bold = True
    lang_run.font.size = Pt(11)

    lang_para1 = doc.add_paragraph("English – C1/C2 (Professional fluency)", style='List Bullet')
    lang_para1.paragraph_format.left_indent = Inches(0.25)
    lang_para2 = doc.add_paragraph("Polish – Native", style='List Bullet')
    lang_para2.paragraph_format.left_indent = Inches(0.25)

    # Save the document
    resume_path = "/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/resumes/cv_JJ_010.docx"
    doc.save(resume_path)
    print(f"Resume created successfully: {resume_path}")


def create_cover_letter():
    """Create the cover letter DOCX file"""
    doc = Document()

    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Header
    header_para = doc.add_paragraph()
    header_para.space_after = Pt(0)
    header_para.add_run('Piotr Kaminski\n')
    header_para.add_run('piotrkaminski1@protonmail.com | +48 510 934 702 | Krakow, Poland')
    header_para.paragraph_format.line_spacing = 1.0

    doc.add_paragraph()

    # Date
    date_para = doc.add_paragraph('17 April 2026')
    date_para.space_after = Pt(12)

    # Recipient info
    recipient = doc.add_paragraph('Hiring Manager\nChaos Gears')
    recipient.paragraph_format.space_after = Pt(12)

    # Salutation
    salutation = doc.add_paragraph('Dear Hiring Manager,')
    salutation.paragraph_format.space_after = Pt(12)

    # Opening paragraph
    opening = doc.add_paragraph(
        'I am writing to express my strong interest in the Delivery Manager position at Chaos Gears. '
        'This role represents a natural progression from my current position as Lead Solutions Engineer at Luigi\'s Box, '
        'where I have been driving delivery excellence and cross-functional project coordination. '
        'Your focus on GenAI implementation and AWS cloud modernization directly aligns with my hands-on expertise—I have '
        'implemented GenAI-powered search optimization and recommender systems while managing complex technical delivery, '
        'and I bring deep knowledge of AWS infrastructure and team leadership.'
    )
    opening.paragraph_format.line_spacing = 1.15
    opening.space_after = Pt(10)

    # Body paragraph 1: Delivery track record
    body1 = doc.add_paragraph(
        'My delivery track record speaks to systematic excellence. At Luigi\'s Box, I achieved zero churn rate on implementation delivery '
        'by redesigning onboarding processes and ensuring Tier 1/2 technical success. At Flexiroam, I coordinated 100% implementation success '
        'across 50+ B2B platform migrations with zero integration failures, while driving 25% YoY account growth through proactive project management. '
        'These results are not luck—they are the outcome of disciplined delivery practices, clear accountability, and a relentless focus on client success.'
    )
    body1.paragraph_format.line_spacing = 1.15
    body1.space_after = Pt(10)

    # Body paragraph 2: Technical depth and GenAI/AWS expertise
    body2 = doc.add_paragraph(
        'Beyond delivery metrics, I bring direct technical depth that enables credible collaboration with engineering teams. '
        'I have designed and implemented GenAI/AI solutions, developed REST API integrations, and worked extensively with AWS services '
        '(Lambda, CloudWatch). This technical foundation allows me to understand not just what needs to be delivered, but the operational '
        'challenges and trade-offs inherent in modern cloud systems. At Rapid, I mentored technical teams and led process improvements that '
        'reduced mean-time-to-resolution by 20%—demonstrating that delivery excellence comes from both strategy and tactical execution.'
    )
    body2.paragraph_format.line_spacing = 1.15
    body2.space_after = Pt(10)

    # Closing paragraph
    closing = doc.add_paragraph(
        'I am confident I can deliver measurable results for Chaos Gears. I am based in Krakow and open to flexible working arrangements. '
        'I would welcome the opportunity to discuss how my delivery expertise, technical knowledge, and team leadership can support your '
        'product and organizational goals.'
    )
    closing.paragraph_format.line_spacing = 1.15
    closing.space_after = Pt(12)

    # Sign-off
    sign_off = doc.add_paragraph('Best regards,')
    sign_off.paragraph_format.space_after = Pt(24)

    # Name
    signature = doc.add_paragraph('Piotr Kaminski')
    signature.paragraph_format.space_after = Pt(0)

    # Save the document
    letter_path = "/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/cover_letters/letter_JJ_010.docx"
    doc.save(letter_path)
    print(f"Cover letter created successfully: {letter_path}")


def create_application_notes():
    """Create application notes JSON file"""
    notes = {
        "what_was_emphasised": [
            "Delivery management and project coordination excellence (zero churn, 100% success rate)",
            "GenAI/AI implementation experience (search optimization, recommender systems)",
            "AWS cloud expertise (Lambda, CloudWatch, platform migration)",
            "Cross-functional team leadership and coordination",
            "Process optimization and efficiency improvements (10-15% efficiency gains, 20% MTTR reduction)",
            "Technical mentoring and team development",
            "Technical delivery track record across Tier 1/2 support and enterprise migrations",
            "Proven business impact (25% YoY growth, $300K+ fraud protection)"
        ],
        "ats_keywords_used": [
            "Delivery Manager",
            "Project coordination",
            "GenAI implementation",
            "AWS cloud migration",
            "Technical delivery",
            "Application modernization",
            "Cross-functional leadership",
            "SaaS platform delivery",
            "Process optimization",
            "Team leadership"
        ],
        "sections_reordered": True,
        "cover_letter_angle": "Natural progression from Lead Solutions Engineer to Delivery Manager role, positioning proven delivery excellence metrics (0% churn rate, 100% B2B migration success across 50+ accounts, 25% YoY growth) as core strength. Emphasized direct GenAI/AI implementation expertise and AWS technical foundation, demonstrating credibility to work with engineering teams. Confident and direct tone focused on measurable outcomes and operational impact rather than generic enthusiasm. Highlighted disciplined delivery practices, tactical execution capability, and team mentoring as differentiators."
    }

    notes_path = "/Users/bill/Work/codeworkspace/Job Seeker/job_agent/data/analyses/notes_JJ_010.json"
    with open(notes_path, 'w') as f:
        json.dump(notes, f, indent=2)
    print(f"Application notes created successfully: {notes_path}")


if __name__ == "__main__":
    try:
        create_resume()
        create_cover_letter()
        create_application_notes()
        print("\nAll documents created successfully!")
    except Exception as e:
        print(f"Error creating documents: {e}")
        raise
