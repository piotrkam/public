from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "data"
RESUMES_DIR    = DATA_DIR / "resumes"
LETTERS_DIR    = DATA_DIR / "cover_letters"
ANALYSES_DIR   = DATA_DIR / "analyses"
LOGS_DIR       = BASE_DIR / "logs"
DB_PATH        = DATA_DIR / "applications.db"
CV_MASTER_PATH = DATA_DIR / "cv_master.json"

# ── Model selection ────────────────────────────────────────────────────────────
# When using a Claude subscription (claude login), set explicit model IDs:
#   MODEL_FAST    = "claude-haiku-4-5"  # Scout, Tracker
#   MODEL_STD    = "claude-sonnet-4-6"  # Tailor,Analyst

MODEL_FAST:    str | None = None
MODEL_STD:     str | None = None

# ── Search configuration ───────────────────────────────────────────────────────
TARGET_ROLES = [
    "Solutions Engineer",
    "Technical Solutions Engineer",
    "Lead Solutions Engineer",
    "Technical Account Manager",
    "Sales Engineer",
    "Solution Consultant",
    "Delivery Manager",
    "Business Solution Architect",
    "Integration Engineer",
    "Technical Consultant",
    "Customer Success Engineer"
    ]

# LinkedIn — generated from TARGET_ROLES so they always stay in sync
SOURCE_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords={}&location=Poland&f_WT=2".format(
        role.replace(" ", "+")
    )
    for role in TARGET_ROLES
]

# justjoin.it via WebSearch — broader queries get more results than exact-quoted role names
WEBSEARCH_QUERIES = [
    "site:justjoin.it solutions engineer Poland",
    "site:justjoin.it technical account manager Poland",
    "site:justjoin.it sales engineer Poland",
    "site:justjoin.it delivery manager Poland",
    "site:justjoin.it integration engineer Poland",
    "site:justjoin.it solution consultant Poland",
    "site:justjoin.it technical consultant Poland",
    "site:justjoin.it customer success engineer Poland",
]

# ── Pipeline settings ──────────────────────────────────────────────────────────
RELEVANCE_THRESHOLD  = 60    # 0-100 — skip jobs below this score (matches "Acceptable fit")
MAX_JOBS_PER_RUN     = 50   # safety cap per pipeline run
REQUIRE_CONFIRMATION = True  # always ask before submitting

# ── Candidate profile (used by Analyst to score relevance) ────────────────────
CANDIDATE_PROFILE = """
Name: Piotr Kaminski
Location: Krakow, Poland
Languages: English (C1/C2), Polish (native)

Target roles: Solutions Engineer, Lead Solutions Engineer, Technical Account Manager,
              Sales Engineer, Solution Consultant, Delivery Manager, Business Solution Architect

Experience: 10+ years in technical delivery and client-facing SaaS roles
  - Lead Solutions Engineer @ Luigi's Box (2025–present)
  - Technical Account Manager @ Flexiroam (2023–2025)
  - Technical Support Engineer @ Rapid/RapidAPI (2020–2023)

Technical skills: REST APIs, API Integration, Webhooks, JSON, Python (basic), SQL (intermediate),
  AWS (Lambda, CloudWatch), SaaS platforms, Postman, JIRA, Confluence, Grafana

Domain expertise:
  - E-commerce / site search / AI-powered search (Luigi's Box)
  - Telecom / eSIM / BSS systems (Flexiroam)
  - Developer tools / API marketplaces (RapidAPI)

Key achievements:
  - 0% churn from integration issues
  - 100% B2B migration success rate
  - 25% account growth YoY
  - 89% Tier 2 support satisfaction rate
  - $300K+ revenue protected via fraud prevention

Salary range: 16,000–30,000 PLN/month (B2B) or 100–190 PLN/hour
Work preference: Remote-first; Krakow office acceptable

NOT interested in: AML/compliance, healthcare, pure sales (quota-only), DevOps/SRE on-call
"""
