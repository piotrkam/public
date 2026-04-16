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
    "Customer Success Engineer",
    "Integration Consultant",
    "Technical Integration Consultant",
    "Project Manager",
    "Technical Project Manager",
    "Technical Customer Success Manager",

    # PM / Delivery variants
    "Implementation Manager",
    "Implementation Project Manager",
    "IT Project Manager",
    "Technical Delivery Manager",
    "Program Manager",
    "Technical Program Manager",
    "Onboarding Manager",
    "Customer Onboarding Manager",

    # TAM / CSM variants
    "Enterprise Account Manager",
    "Technical Success Manager",
    "Senior Customer Success Manager",
    "Strategic Customer Success Manager",

    # Integration / API focused
    "API Solutions Engineer",
    "Integration Specialist",
    "Technical Integration Specialist",
    "Implementation Specialist",
    "Implementation Engineer",

    # Broader but worth catching
    "Client Solutions Manager",
    "Client Success Manager",
    "Digital Implementation Manager",
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

Target roles: Solutions Engineer, Technical Solutions Engineer, Lead Solutions Engineer,
              Technical Account Manager, Sales Engineer, Solution Consultant, Delivery Manager,
              Business Solution Architect, Integration Engineer, Technical Consultant,
              Customer Success Engineer, Integration Consultant, Technical Integration Consultant,
              Project Manager, Technical Project Manager, Technical Customer Success Manager,
              Implementation Manager, Implementation Project Manager, Technical Delivery Manager,
              Program Manager, Technical Program Manager, Onboarding Manager,
              Pre-Sales Engineer, Solutions Architect, Enterprise Solutions Engineer,
              Technical Integration Specialist, Implementation Specialist, Implementation Engineer

Experience: 10+ years in technical delivery, client-facing SaaS, and project/program management
  - Lead Solutions Engineer @ Luigi's Box (2025–present)
    • Led delivery team; zero churn from integration issues
    • Managed Tier 1 & 2 integrations; cross-functional coordination (Sales, Product, Engineering)
    • Redesigned SE framework; introduced agile delivery and KPI tracking
  
  - Technical Account Manager @ Flexiroam (2023–2025)
    • Owned full sales cycle; 25% account growth; 100% implementation success
    • Led B2B platform migration (100% success, zero disruption)
    • Managed eSIM platform implementation and device onboarding workflows
    • Built customer-R&D feedback loops; contributed to 50% revenue growth for key accounts
  
  - Technical Support Engineer @ Rapid/RapidAPI (2020–2023)
    • Tier 2 support; 89% satisfaction rate
    • Onboarded and trained 7 support engineers; built documentation
    • Led fraud prevention initiative; cut customer disputes 80%; protected $300K+ annual revenue
    • Primary liaison between Support and R&D; improved first-contact resolution 10%

Technical skills: REST APIs, API Integration, Webhooks, Event-driven architecture, JSON,
  Python (basic scripting), SQL (intermediate data analysis), AWS (Lambda, CloudWatch),
  SaaS platforms, Multi-tenant systems, Postman, JIRA, Confluence, Grafana, CloudWatch

Domain expertise:
  - E-commerce / site search / AI-powered search / product indexing (Luigi's Box)
  - Telecom / eSIM / BSS systems / TM Forum frameworks (Flexiroam)
  - Developer tools / API marketplaces / multi-tenant SaaS (RapidAPI)
  - Enterprise B2B SaaS onboarding and implementation

Project/Program management experience:
  - End-to-end integration delivery ownership (complex, multi-team projects)
  - Cross-functional coordination: C-level to developers
  - Agile delivery practices; process design and documentation ownership
  - Risk management; stakeholder communication; team leadership

Key achievements:
  - 0% client churn from integration issues (Luigi's Box)
  - 100% B2B migration and implementation success rate (Flexiroam)
  - 25% account growth YoY (Flexiroam)
  - 50% revenue growth contribution for key accounts (Flexiroam)
  - 89% Tier 2 support satisfaction (RapidAPI)
  - 80% reduction in customer disputes (RapidAPI)
  - $300K+ annual revenue protected via fraud prevention (RapidAPI)
  - 10% improvement in first-contact resolution; 15% reduction in L1 tickets (RapidAPI)
  - Led and managed integration team as Lead Solutions Engineer

Salary range: 16,000–30,000 PLN/month (B2B) or 100–190 PLN/hour
Work preference: Remote-first; Krakow office acceptable; flexible on-site days acceptable

Open to: Technical PM / Implementation PM roles (sidestep); formal PM methodology learning
NOT interested in: AML/compliance, healthcare, pure sales (quota-only), DevOps/SRE on-call,
                   non-technical project management (construction, events, HR)
"""