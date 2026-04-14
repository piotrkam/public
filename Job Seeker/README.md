# Job Seeker Agent

An autonomous AI pipeline that scans job boards, scores opportunities against your profile, and generates tailored CVs and cover letters — so you apply to the right roles with the right materials.

> **You may use this codebase with other LLMs with slight modifications.**
> The pipeline is decoupled from any specific provider via `job_agent/llm_agent.py`.
> See [Using a different LLM](#using-a-different-llm) for the migration guide.

Built on the [Claude Agent SDK](https://docs.anthropic.com/claude-agent-sdk) by default, designed to run with a Claude subscription (no API credits needed).

---

## How it works

The pipeline runs in two phases so you don't have to sit in front of the computer while it works.

```
Phase 1 — Unattended (walk away)
  Scout   → crawls LinkedIn and justjoin.it for matching roles
  Filter  → skips jobs already seen in previous runs
  Analyst → scores every job 0–100 against your profile
            auto-rejects hard disqualifiers (wrong sector, below salary floor, etc.)

Phase 2 — Interactive (sit down when Phase 1 finishes)
  Review  → shows you each passing job: score, salary, rationale,
             your competitive advantages, warnings, talking points
  Tailor  → generates a tailored CV and cover letter (DOCX) for jobs you accept
  Output  → clickable links to the files + the job posting URL
             you apply manually
```

At the end of Phase 1 a full summary table is printed — every job scanned with its title, company, score, outcome, and URL — so you can spot any that were incorrectly rejected before Phase 2 begins.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Node.js 18+ | Required for Claude Code CLI (default backend) |
| Python 3.11+ | |
| Claude subscription | claude.ai Pro or Team — no API key needed |

### Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
claude login          # authenticates with your subscription
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/job-seeker-agent.git
cd job-seeker-agent

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r job_agent/requirements.txt
```

---

## Configuration

There are two files to edit before running.

### 1. Your master resume — `job_agent/data/cv_master.json`

This is the single source of truth for your experience. The Tailor agent reads it and selectively assembles a customised version for each job. Fill in your real data:

```json
{
  "personal": {
    "name": "Your Name",
    "email": "you@example.com",
    "phone": "+00 000 000 000",
    "location": "City, Country",
    "linkedin": "https://linkedin.com/in/yourprofile"
  },
  "summary": "One paragraph positioning statement.",
  "experience": [
    {
      "title": "Senior Solutions Engineer",
      "company": "Acme Corp",
      "location": "Remote",
      "start": "2022-03",
      "end": "present",
      "highlights": [
        "Led onboarding for 40+ enterprise accounts with zero churn",
        "Grew assigned accounts by 30% YoY through API upsell"
      ],
      "tech": ["REST APIs", "Python", "SQL", "AWS"]
    }
  ],
  "skills": {
    "technical": ["REST APIs", "Python", "SQL", "Postman"],
    "tools": ["JIRA", "Confluence", "Grafana"],
    "soft_skills": ["Team Leadership", "Client Relationship Management"]
  },
  "languages_spoken": [
    { "language": "English", "level": "C1/C2" },
    { "language": "Polish",  "level": "Native" }
  ],
  "key_metrics": {
    "growth":  ["30% account growth YoY"],
    "quality": ["89% first-contact satisfaction rate"],
    "impact":  ["$300K+ revenue protected"]
  }
}
```

### 2. Search settings — `job_agent/config.py`

```python
# Roles to search for (drives both LinkedIn and justjoin.it queries automatically)
TARGET_ROLES = [
    "Solutions Engineer",
    "Technical Account Manager",
    "Sales Engineer",
    # add or remove roles here
]

# Only show jobs that score at or above this threshold (0–100)
RELEVANCE_THRESHOLD = 60

# Maximum jobs to process per run (safety cap)
MAX_JOBS_PER_RUN = 20

# Your profile — used by the Analyst to score relevance
CANDIDATE_PROFILE = """
Name: Your Name
Location: City, Country
...
Salary range: X–Y PLN/month or X–Y EUR/month
NOT interested in: AML/compliance, healthcare, pure quota sales
"""
```

---

## Running the pipeline

```bash
cd job-seeker-agent
source venv/bin/activate
python3 job_agent/orchestrator.py
```

Start it and walk away. When Phase 1 finishes you'll see the summary table and a prompt to start reviewing.

### Terminal recommendation

Use **iTerm2** or **VS Code integrated terminal** for clickable file and URL links (OSC 8 hyperlinks). macOS Terminal.app does not support them.

To verify your terminal supports links:
```bash
printf '\033]8;;https://example.com\033\\click me\033]8;;\033\\\n'
```

---

## Project structure

```
job-seeker-agent/
├── job_agent/
│   ├── orchestrator.py       # main pipeline — run this
│   ├── config.py             # your roles, profile, thresholds
│   ├── tracker.py            # SQLite deduplication + run history
│   ├── llm_agent.py          # LLM adapter — swap backend here
│   ├── agents/
│   │   ├── definitions.py    # Scout, Analyst, Tailor agent prompts
│   │   └── __init__.py
│   ├── data/
│   │   ├── cv_master.json    # your master resume (edit this)
│   │   ├── analyses/         # per-job JSON scoring reports
│   │   ├── resumes/          # tailored CVs (DOCX)
│   │   └── cover_letters/    # tailored cover letters (DOCX)
│   └── logs/                 # daily run logs
├── requirements.txt
└── README.md
```

---

## Job sources

| Source | Method | Notes |
|---|---|---|
| LinkedIn | WebFetch search results | Fetches individual job detail pages for full descriptions |
| justjoin.it | WebSearch `site:justjoin.it` | JS-rendered site — data extracted from Google snippets |

Both sources are generated automatically from `TARGET_ROLES` in `config.py`. Add a role there and both LinkedIn and justjoin.it queries update automatically.

To add a new job board, add its URLs to `SOURCE_URLS` in `config.py` and describe the fetching strategy in the Scout agent prompt in `agents/definitions.py`.

---

## Scoring framework

The Analyst scores each job across four dimensions:

| Dimension | Points | What it measures |
|---|---|---|
| Technical Alignment | 40 | API/integration skills, platform tools, relevant tech stack |
| Role Responsibilities | 35 | Client-facing work, project ownership, career progression |
| Domain Fit | 15 | Industry match (e-commerce, SaaS, telecom, etc.) |
| Leadership Context | 10 | Team management, cross-functional scope |

**Score bands:**
- 85–100 — Excellent fit, apply immediately
- 70–84 — Good fit, strong candidate
- 60–69 — Acceptable fit (default threshold)
- 40–59 — Weak fit, low priority
- 0–39 — Poor fit, skipped

**Auto-disqualifiers** (immediately rejected regardless of score):
- Requires AML / healthcare domain expertise
- Pure quota sales with no technical component
- Full-time coding / DevOps on-call role
- Salary below your configured floor

---

## Output files

For each job you accept in Phase 2:

| File | Location | Contents |
|---|---|---|
| `cv_{job_id}.docx` | `data/resumes/` | Tailored CV with ATS keywords mirrored from the job description |
| `letter_{job_id}.docx` | `data/cover_letters/` | Cover letter (≤300 words) with role-specific angle |
| `analysis_{job_id}.json` | `data/analyses/` | Full scoring breakdown, green flags, warnings, talking points |
| `notes_{job_id}.json` | `data/analyses/` | What the Tailor emphasised and why |
| `applications.db` | `data/` | SQLite database — full job history and application log |

---

## Adapting for your profile

Everything that makes this personal to you lives in two places:

1. **`cv_master.json`** — your experience, skills, and metrics
2. **`config.py`** → `CANDIDATE_PROFILE` and `TARGET_ROLES`

The agent prompts in `agents/definitions.py` are generic and role-agnostic. You don't need to touch them unless you want to change the scoring framework or add new job sources.

---

## Using a different LLM

All LLM coupling is isolated in **`job_agent/llm_agent.py`**. You only need to touch that one file plus `requirements.txt` to swap backends.

### What to change

| # | File | What to do |
|---|---|---|
| 1 | `job_agent/llm_agent.py` | Replace the `from claude_agent_sdk import ...` block with your SDK's equivalents (see contract below) |
| 2 | `job_agent/requirements.txt` | Remove `claude-agent-sdk` and add your SDK's package |
| 3 | `job_agent/config.py` | Update `MODEL_FAST` and `MODEL_STD` to your provider's model IDs |
| 4 | `job_agent/agents/definitions.py` | The `tools` lists on each agent (`WebFetch`, `WebSearch`, `Write`, etc.) are Claude Code tool names — map them to your SDK's equivalent tool identifiers |

### The adapter contract

`llm_agent.py` must export four names:

```python
AgentDefinition   # dataclass / object: description: str, prompt: str, tools: list[str]

AgentOptions      # options for a single query call, must accept:
                  #   system_prompt: str
                  #   allowed_tools: list[str]
                  #   cwd: str
                  #   permission_mode: str   (may be ignored by non-Claude SDKs)
                  #   model: str | None

ResultMessage     # message type whose .result: str holds the agent's final output

query             # async generator:
                  #   query(prompt: str, options: AgentOptions) -> AsyncIterator[message]
```

### Example: OpenAI Agents SDK

```python
# llm_agent.py — OpenAI Agents SDK backend (illustrative)
from openai_agents import AgentDefinition, run as _run, RunOptions, FinalOutputMessage

AgentOptions = RunOptions
ResultMessage = FinalOutputMessage

async def query(prompt, options):
    async for msg in _run(prompt, options):
        yield msg
```

### Notes on tool availability

- `WebFetch` and `WebSearch` are Claude Code built-in tools. Other SDKs may not provide them natively — you may need to implement them as custom tools or replace them with equivalent library calls.
- `Write` and `Read` are file-system tools also provided by Claude Code. Most SDKs support file operations through custom tools.
- If your SDK has no built-in browser/search tools, the Scout agent will need its `tools` list and prompt updated to call your equivalents.

---

## Dependencies

```
claude-agent-sdk>=0.1.0   # default LLM backend — replace via llm_agent.py
anyio>=4.0.0              # async runtime
python-docx>=1.1.0        # DOCX generation
```

---

## License

MIT
