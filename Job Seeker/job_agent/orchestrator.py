"""
Orchestrator — Python-controlled pipeline (Option B).

Phase 1 (unattended — leave it running):
  Scout → filter duplicates → Analyst runs on every job

Phase 2 (interactive — sit down when Phase 1 is done):
  For each job that passed analysis → show review card → user accepts/skips
  → [accepted] → Tailor → show CV + cover letter links

Applications are submitted manually by the user.
"""

import anyio
import json
import hashlib
import logging
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from llm_agent import query, AgentOptions as ClaudeAgentOptions, ResultMessage

import config
import tracker
import docx_builder
from agents import SCOUT, ANALYST, TAILOR

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / f"run_{date.today().isoformat()}.log"),
    ],
)
log = logging.getLogger(__name__)


# ── Helper: run a single agent and return its ResultMessage text ───────────────

async def run_agent(
    agent_def,
    prompt: str,
    label: str,
    model: str | None = config.MODEL_STD,
) -> str:
    log.info("▶  %s", label)
    result = ""

    # Only pass model if explicitly configured — with a subscription the CLI
    # selects the best available model automatically when model=None.
    options_kwargs = dict(
        allowed_tools=agent_def.tools,
        system_prompt=agent_def.prompt,
        cwd=str(config.BASE_DIR),
        permission_mode="acceptEdits",
    )
    if model is not None:
        options_kwargs["model"] = model

    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(**options_kwargs),
    ):
        if isinstance(msg, ResultMessage):
            result = msg.result
    log.info("✓  %s", label)
    return result


# ── URL normalisation & stable job_id ─────────────────────────────────────────

def normalize_url(url: str) -> str:
    """Strip tracking/query parameters and fragments, keeping only scheme + host + path.

    LinkedIn:   https://www.linkedin.com/jobs/view/1234567890/?tracking=... → .../view/1234567890/
    justjoin:   https://justjoin.it/job-offer/company-role?utm_source=...  → .../job-offer/company-role
    Generic:    any URL — query string and fragment dropped
    """
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def stable_job_id(url: str) -> str:
    """Deterministic job ID derived from the normalised URL."""
    return hashlib.md5(normalize_url(url).encode()).hexdigest()[:12]


# ── Step 1: Scout ──────────────────────────────────────────────────────────────

async def step_scout() -> list[dict]:
    output_file = config.DATA_DIR / "jobs_raw.json"

    await run_agent(
        SCOUT,
        prompt=f"""
        Search for IT job listings matching these roles:
        {json.dumps(config.TARGET_ROLES, indent=2)}

        ## Source A — LinkedIn (WebFetch each URL):
        {json.dumps(config.SOURCE_URLS, indent=2)}

        ## Source B — justjoin.it (WebSearch each query, then WebFetch each result URL):
        {json.dumps(config.WEBSEARCH_QUERIES, indent=2)}

        Save results as a JSON array to: {output_file}

        Each item must have:
          job_id, title, company, location, url, description, posted_date, application_method
        """,
        label="Scout — crawling job boards",
        model=config.MODEL_FAST,
    )

    if not output_file.exists():
        log.warning("Scout produced no output file.")
        return []

    jobs = json.loads(output_file.read_text(encoding="utf-8"))

    # Always recompute job_id from the normalised URL — never trust the agent's
    # value, which varies across runs due to tracking parameters or naming.
    for job in jobs:
        job["job_id"] = stable_job_id(job["url"])
        tracker.upsert_job(job)

    log.info("Scout found %d listings", len(jobs))
    return jobs


# ── Step 2: Filter duplicates ──────────────────────────────────────────────────

def step_filter(jobs: list[dict]) -> list[dict]:
    new_jobs = tracker.filter_new_jobs(jobs)
    skipped = len(jobs) - len(new_jobs)
    log.info("Tracker: %d to analyse, %d already reviewed/submitted — skipping", len(new_jobs), skipped)
    return new_jobs[:config.MAX_JOBS_PER_RUN]


# ── Step 2b: Ask user how to proceed when previous results exist ───────────────

def step_confirm_mode(all_jobs: list[dict], new_jobs: list[dict]) -> list[dict]:
    """If previous-run jobs exist, ask whether to continue or start fresh.

    Returns the final list of jobs to analyse in Phase 1.

    Options presented to the user:
      c — continue  : analyse only the new/unreviewed jobs (default)
      r — restart   : reset ALL previously-reviewed jobs and re-analyse everything
      q — quit
    """
    already_reviewed = len(all_jobs) - len(new_jobs)
    if already_reviewed == 0:
        # First-ever run or clean slate — nothing to decide
        return new_jobs

    W = 60
    print()
    print(f"╔{'═' * W}╗")
    print(f"║  {'PREVIOUS RUN DETECTED':<{W - 2}}  ║")
    print(f"╠{'═' * W}╣")
    print(f"║  {'Jobs found this scan:':<30}{len(all_jobs):<{W - 32}}  ║")
    print(f"║  {'Already reviewed / submitted:':<30}{already_reviewed:<{W - 32}}  ║")
    print(f"║  {'New / not yet analysed:':<30}{len(new_jobs):<{W - 32}}  ║")
    print(f"╚{'═' * W}╝")
    print()
    print("  [c] Continue  — analyse only the new jobs  (default)")
    print("  [r] Restart   — reset previous results and re-analyse everything")
    print("  [q] Quit")
    print()

    while True:
        answer = input("How would you like to proceed? [c / r / q]: ").strip().lower()
        if answer in ("", "c"):
            log.info("Mode: continue — %d new jobs to analyse", len(new_jobs))
            return new_jobs
        if answer == "r":
            ids_to_reset = [j["job_id"] for j in all_jobs]
            reset_count = tracker.reset_jobs(ids_to_reset)
            log.info("Mode: restart — reset %d jobs to 'new'", reset_count)
            # After reset all jobs are 'new', so re-run the filter to get a
            # clean, capped list in the right order.
            return tracker.filter_new_jobs(all_jobs)[:config.MAX_JOBS_PER_RUN]
        if answer == "q":
            raise SystemExit("Session ended by user.")


# ── Step 0: Startup mode — resume / retry errors / full run ───────────────────

def step_startup_mode() -> str:
    """Check for pending work from previous runs and ask the user how to start.

    Returns:
      "resume" — skip Scout + Phase 1, load analysed jobs and go to Phase 2
      "retry"  — re-analyse errored jobs (mini Phase 1), then Phase 2 for all
      "full"   — run the full pipeline (Scout → Phase 1 → Phase 2)
    """
    pending  = tracker.get_pending_work()
    analysed = pending["analysed"]
    errored  = pending["errored"]

    if not analysed and not errored:
        return "full"

    W = 62
    print()
    print(f"╔{'═' * W}╗")
    print(f"║  {'UNFINISHED WORK FROM PREVIOUS RUN':<{W - 2}}  ║")
    print(f"╠{'═' * W}╣")
    if analysed:
        print(f"║  {'Awaiting your review:':<40}{len(analysed):<{W - 42}}  ║")
        for job in analysed[:3]:
            label = f"    • {job['title'][:42]} @ {job['company'][:16]}"
            print(f"║  {label:<{W - 2}}  ║")
        if len(analysed) > 3:
            print(f"║  {'    … and more':<{W - 2}}  ║")
    if errored:
        print(f"║  {'Failed (need retry):':<40}{len(errored):<{W - 42}}  ║")
        for job in errored[:3]:
            label = f"    • {job['title'][:42]} @ {job['company'][:16]}"
            print(f"║  {label:<{W - 2}}  ║")
        if len(errored) > 3:
            print(f"║  {'    … and more':<{W - 2}}  ║")
    print(f"╚{'═' * W}╝")
    print()

    options = []
    if analysed:
        options.append("  [r] Resume   — go straight to Phase 2 (skip Scout)")
    if errored:
        options.append("  [e] Retry    — re-analyse failed jobs, then Phase 2 (skip Scout)")
    options.append("  [f] Full run — scout new jobs, retry errors, then review all")
    options.append("  [q] Quit")
    for opt in options:
        print(opt)
    print()

    valid = {"f", "q"}
    if analysed:
        valid.add("r")
    if errored:
        valid.add("e")

    while True:
        answer = input("How would you like to start? [" + " / ".join(sorted(valid)) + "]: ").strip().lower()
        if answer == "r" and "r" in valid:
            log.info("Startup mode: resume — %d pending jobs", len(analysed))
            return "resume"
        if answer == "e" and "e" in valid:
            log.info("Startup mode: retry — %d errored jobs", len(errored))
            return "retry"
        if answer == "f":
            log.info("Startup mode: full run")
            return "full"
        if answer == "q":
            raise SystemExit("Session ended by user.")


# ── Step 3: Analyst ────────────────────────────────────────────────────────────

async def step_analyse(job: dict) -> dict:
    """
    Returns a result dict always — check result["outcome"]:
      "passed"        — above threshold, proceed to review
      "auto_rejected" — hard disqualifier flagged by analyst
      "low_score"     — below RELEVANCE_THRESHOLD
      "error"         — analyst produced no output
    """
    output_file = config.ANALYSES_DIR / f"analysis_{job['job_id']}.json"

    await run_agent(
        ANALYST,
        prompt=f"""
        Analyse this job posting for the following candidate profile:

        {config.CANDIDATE_PROFILE}

        Job URL:   {job['url']}
        Job title: {job['title']}
        Company:   {job['company']}
        Salary shown on listing: {job.get('salary_raw', 'not listed')}
        Description snippet (use if URL is not fetchable): {job.get('description', '')}

        Save the analysis JSON to: {output_file}
        """,
        label=f"Analyst — {job['title']} @ {job['company']}",
    )

    if not output_file.exists():
        log.warning("Analyst produced no output for job %s", job["job_id"])
        tracker.update_job_status(job["job_id"], "error")
        return {"job": job, "analysis": {}, "score": 0, "outcome": "error", "reject_reason": "no output"}

    analysis = json.loads(output_file.read_text(encoding="utf-8"))
    score = analysis.get("relevance_score", 0)
    tracker.update_job_status(job["job_id"], "analysed", relevance_score=score)

    # Auto-reject: analyst flagged hard disqualifier
    if analysis.get("auto_reject"):
        reason = analysis.get("auto_reject_reason", "auto-rejected by analyst")
        log.info("  ✗ Auto-rejected: %s", reason)
        tracker.update_job_status(job["job_id"], "skipped")
        return {"job": job, "analysis": analysis, "score": score, "outcome": "auto_rejected", "reject_reason": reason}

    if score < config.RELEVANCE_THRESHOLD:
        log.info("  ✗ Score %d < threshold %d", score, config.RELEVANCE_THRESHOLD)
        tracker.update_job_status(job["job_id"], "skipped")
        return {"job": job, "analysis": analysis, "score": score, "outcome": "low_score", "reject_reason": f"score {score} < {config.RELEVANCE_THRESHOLD}"}

    priority = analysis.get("application_priority", "medium")
    salary = analysis.get("salary_raw") or job.get("salary_raw") or "not listed"
    log.info("  ✓ Score %d/100 | priority: %s | salary: %s", score, priority, salary)

    if analysis.get("warnings"):
        for w in analysis["warnings"]:
            log.warning("  ⚠  %s", w)

    return {"job": job, "analysis": analysis, "score": score, "outcome": "passed", "reject_reason": None}


# ── Step 4: Tailor ─────────────────────────────────────────────────────────────

async def step_tailor(data: dict) -> dict:
    job = data["job"]
    job_id = job["job_id"]

    # Stage 1: agent writes structured content JSON (plain text — it cannot create binary files)
    content_file = config.ANALYSES_DIR / f"content_{job_id}.json"
    notes_file   = config.ANALYSES_DIR / f"notes_{job_id}.json"
    cv_file      = config.RESUMES_DIR  / f"cv_{job_id}.docx"
    letter_file  = config.LETTERS_DIR  / f"letter_{job_id}.docx"

    await run_agent(
        TAILOR,
        prompt=f"""
        Create tailored application content for this job:

        Company:   {job['company']}
        Title:     {job['title']}
        Job URL:   {job['url']}

        Master resume:  {config.CV_MASTER_PATH}
        Job analysis:   {config.ANALYSES_DIR / f"analysis_{job_id}.json"}

        Save the full JSON output (resume + cover_letter + notes) to: {content_file}
        """,
        label=f"Tailor — crafting content for {job['company']}",
    )

    if not content_file.exists():
        raise RuntimeError(f"Tailor produced no content file for job {job_id}")

    # Stage 2: build the actual DOCX files locally from the agent's JSON
    log.info("  Building DOCX files from content JSON...")
    try:
        docx_builder.build_documents(
            content_file=content_file,
            cv_output=cv_file,
            letter_output=letter_file,
        )
    except Exception as exc:
        raise RuntimeError(f"DOCX build failed for job {job_id}: {exc}") from exc

    # Extract notes into a separate file for consistency with previous runs
    content = json.loads(content_file.read_text(encoding="utf-8"))
    if "notes" in content:
        notes_file.write_text(
            json.dumps(content["notes"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    tracker.update_job_status(job_id, "tailored")
    log.info("  CV:           file://%s", cv_file)
    log.info("  Cover letter: file://%s", letter_file)
    return {**data, "cv_file": cv_file, "letter_file": letter_file}


# ── Step 5: Present analysis to user, ask whether to prepare materials ────────

def _link(path_or_url: str, label: str) -> str:
    """Return an OSC 8 hyperlink for terminals that support it, plain text fallback."""
    uri = path_or_url if path_or_url.startswith("http") else f"file://{path_or_url}"
    return f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"


def step_review(data: dict) -> bool:
    """Show the analyst report and ask the user whether to prepare CV + cover letter."""
    job      = data["job"]
    analysis = data["analysis"]

    salary    = analysis.get("salary_raw") or job.get("salary_raw") or "not listed"
    score     = analysis.get("relevance_score", 0)
    priority  = analysis.get("application_priority", "?").upper()
    traj      = analysis.get("career_trajectory", "?")
    verdict   = analysis.get("salary_verdict", "?").upper()
    rationale = analysis.get("relevance_rationale", "")
    warnings  = analysis.get("warnings", [])
    green     = analysis.get("green_flags", [])
    adv       = analysis.get("competitive_advantages", [])
    gaps      = analysis.get("skill_gaps", [])
    points    = analysis.get("key_talking_points", [])

    W = 60  # box width

    def row(label: str, value: str) -> str:
        content = f"  {label:<14}{value}"
        return f"║  {content:<{W - 4}}  ║"

    print()
    print(f"╔{'═' * W}╗")
    print(f"║  {'JOB OPPORTUNITY':<{W - 2}}  ║")
    print(f"╠{'═' * W}╣")
    print(row("Company:",   job["company"]))
    print(row("Role:",      job["title"]))
    print(row("Location:",  job.get("location", "?")))
    print(row("Salary:",    salary))
    print(row("Verdict:",   verdict))
    print(f"╠{'═' * W}╣")
    print(row("Score:",     f"{score}/100"))
    print(row("Priority:",  priority))
    print(row("Trajectory:", traj))
    print(f"╚{'═' * W}╝")

    print(f"\n  {_link(job['url'], '→ Open job posting')}")

    if rationale:
        print(f"\n  Rationale\n    {rationale}")

    if green:
        print("\n  Green flags")
        for g in green:
            print(f"    ✓  {g}")

    if adv:
        print("\n  Your advantages")
        for a in adv:
            print(f"    ★  {a}")

    if points:
        print("\n  Key talking points")
        for p in points:
            print(f"    •  {p}")

    if gaps:
        print("\n  Skill gaps")
        for g in gaps:
            print(f"    △  {g}")

    if warnings:
        print("\n  Warnings")
        for w in warnings:
            print(f"    ⚠  {w}")

    answer = input("\nPrepare CV + cover letter? [y / n / q to quit]: ").strip().lower()
    if answer == "q":
        raise SystemExit("Session ended by user.")
    return answer == "y"


# ── Step 6: Show output links after tailoring ─────────────────────────────────

def step_show_outputs(data: dict) -> None:
    print(f"\n  CV:           {_link(str(data['cv_file']), str(data['cv_file']))}")
    print(f"  Cover letter: {_link(str(data['letter_file']), str(data['letter_file']))}")
    print(f"  Apply here:   {_link(data['job']['url'], data['job']['url'])}")
    print()


# ── Main pipeline ──────────────────────────────────────────────────────────────

async def orchestrate() -> None:
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    submitted, skipped, auto_rejected, errors = [], [], [], []

    log.info("=" * 60)
    log.info("JOB AGENT — pipeline start")
    log.info("Targeting: %s", ", ".join(config.TARGET_ROLES))
    log.info("=" * 60)

    # ── 0. Startup mode — resume Phase 2 or run full pipeline ─
    startup_mode = step_startup_mode()

    all_results = []   # every result dict regardless of outcome
    analysed    = []   # only "passed" results

    if startup_mode in ("resume", "retry"):
        # ── Resume / retry path: skip Scout ───────────────────────

        # Load previously-analysed jobs for Phase 2
        for job in tracker.get_analysed_jobs():
            analysis_file = config.ANALYSES_DIR / f"analysis_{job['job_id']}.json"
            if not analysis_file.exists():
                log.warning("  Resume: no analysis file for %s — re-queueing as new", job["job_id"])
                tracker.update_job_status(job["job_id"], "new")
                continue
            analysis = json.loads(analysis_file.read_text(encoding="utf-8"))
            score = analysis.get("relevance_score", 0)
            log.info("  Loaded: %s @ %s (score %d)", job["title"], job["company"], score)
            analysed.append({"job": job, "analysis": analysis, "score": score, "outcome": "passed"})

        # Re-analyse errored jobs (mini Phase 1) if retry mode
        if startup_mode == "retry":
            errored_jobs = tracker.get_pending_work()["errored"]
            if errored_jobs:
                log.info("=" * 60)
                log.info("RETRY PHASE — Re-analysing %d errored jobs", len(errored_jobs))
                log.info("=" * 60)
                for i, job in enumerate(errored_jobs, 1):
                    log.info("-" * 50)
                    log.info("[%d/%d] %s @ %s", i, len(errored_jobs), job["title"], job["company"])
                    # Reset to 'new' so it gets analysed cleanly
                    tracker.update_job_status(job["job_id"], "new")
                    try:
                        result = await step_analyse(job)
                        all_results.append(result)
                        if result["outcome"] == "passed":
                            analysed.append(result)
                        elif result["outcome"] in ("auto_rejected", "low_score"):
                            auto_rejected.append(result["job"])
                        else:
                            errors.append(result["job"])
                    except Exception as exc:
                        log.error("  Retry error for %s: %s", job.get("title"), exc, exc_info=True)
                        tracker.log_error(job["job_id"], str(exc))
                        errors.append(job)

        jobs = [r["job"] for r in analysed]

    else:
        # ── Full run path: Scout → Phase 1 ────────────────────────

        # ── 1. Scout ──────────────────────────────────────────────
        jobs = await step_scout()
        if not jobs:
            log.info("No jobs found. Exiting.")
            return

        # ── 2. Filter duplicates ──────────────────────────────────
        new_jobs = step_filter(jobs)

        # ── 2b. Ask user: continue with new jobs or restart? ──────
        new_jobs = step_confirm_mode(jobs, new_jobs)
        if not new_jobs:
            log.info("No jobs to analyse. Exiting.")
            return

        # ── Phase 1: Analyse ALL jobs unattended ──────────────────
        log.info("=" * 60)
        log.info("PHASE 1 — Analysing %d jobs (no input needed)", len(new_jobs))
        log.info("=" * 60)

        for i, job in enumerate(new_jobs, 1):
            log.info("-" * 50)
            log.info("[%d/%d] %s @ %s", i, len(new_jobs), job["title"], job["company"])
            try:
                result = await step_analyse(job)
                all_results.append(result)
                if result["outcome"] == "passed":
                    analysed.append(result)
                elif result["outcome"] in ("auto_rejected", "low_score"):
                    auto_rejected.append(result["job"])
                else:
                    errors.append(result["job"])
            except Exception as exc:
                log.error("  Analyst error for %s: %s", job.get("title"), exc, exc_info=True)
                tracker.log_error(job["job_id"], str(exc))
                errors.append(job)
                all_results.append({"job": job, "score": 0, "outcome": "error", "reject_reason": str(exc)})

        # ── Phase 1 summary table ──────────────────────────────
        W = 70
        print(f"\n{'═' * W}")
        print(f"  PHASE 1 COMPLETE — {len(new_jobs)} scanned | "
              f"{len(analysed)} passed | "
              f"{len(auto_rejected)} rejected | "
              f"{len(errors)} errors")
        print(f"{'═' * W}")
        print(f"  {'#':<3} {'Score':<7} {'Status':<14} {'Title + Company':<38} URL")
        print(f"  {'-'*3} {'-'*6} {'-'*13} {'-'*37} {'-'*20}")

        ICONS = {
            "passed":        "✓",
            "low_score":     "✗",
            "auto_rejected": "⊘",
            "error":         "!",
        }

        for i, result in enumerate(all_results, 1):
            job    = result["job"]
            score  = result.get("score", 0)
            outcome = result.get("outcome", "error")
            icon   = ICONS.get(outcome, "?")
            label  = f"{icon} {outcome.replace('_', ' ')}"
            title  = f"{job['title']} @ {job['company']}"
            url    = _link(job["url"], job["url"])
            print(f"  {i:<3} {score:<7} {label:<14} {title[:37]:<38} {url}")

        print(f"{'═' * W}\n")

        # ── Merge: add any analysed jobs from previous runs not in this run ──
        current_ids = {r["job"]["job_id"] for r in analysed}
        for job in tracker.get_analysed_jobs():
            if job["job_id"] in current_ids:
                continue
            analysis_file = config.ANALYSES_DIR / f"analysis_{job['job_id']}.json"
            if not analysis_file.exists():
                log.warning("  Resume: no analysis file for %s — re-queueing as new", job["job_id"])
                tracker.update_job_status(job["job_id"], "new")
                continue
            analysis = json.loads(analysis_file.read_text(encoding="utf-8"))
            score = analysis.get("relevance_score", 0)
            log.info("  Carrying forward: %s @ %s (score %d)", job["title"], job["company"], score)
            analysed.insert(0, {"job": job, "analysis": analysis, "score": score, "outcome": "passed"})

    # ── end of full-run else block ─────────────────────────────

    if not analysed:
        log.info("No jobs passed analysis. Exiting.")
    else:
        # ── Phase 2: Review + Tailor (user interaction) ────────
        print(f"\n{'=' * 60}")
        print(f"  PHASE 2 — Review {len(analysed)} analysed jobs")
        print(f"{'=' * 60}\n")

        for i, data in enumerate(analysed, 1):
            job = data["job"]
            print(f"\n[{i}/{len(analysed)}]")
            try:
                # Show analysis card — user decides
                if not step_review(data):
                    log.info("  Skipped by user: %s", job["url"])
                    tracker.update_job_status(job["job_id"], "skipped")
                    skipped.append(job)
                    continue

                # Tailor — only for accepted jobs
                data = await step_tailor(data)

                # Show output links — user applies manually
                step_show_outputs(data)
                tracker.log_application(
                    job_id=job["job_id"],
                    method=job.get("application_method", "manual"),
                    confirmation="",
                    cv_file=str(data["cv_file"]),
                    letter_file=str(data["letter_file"]),
                    notes="Materials prepared — to be submitted manually.",
                )
                submitted.append(job)
                log.info("  ✓ Materials ready — apply manually at: %s", job["url"])

            except SystemExit:
                raise
            except Exception as exc:
                log.error("  Error for %s: %s", job.get("title"), exc, exc_info=True)
                tracker.log_error(job["job_id"], str(exc))
                errors.append(job)

    # ── Final report ───────────────────────────────────────────
    stats = tracker.get_run_stats()
    log.info("=" * 60)
    log.info("PIPELINE COMPLETE")
    log.info("  This run  — found: %d | prepared: %d | skipped: %d | auto-rejected: %d | errors: %d",
             len(jobs), len(submitted), len(skipped), len(auto_rejected), len(errors))
    log.info("  All time  — total jobs: %d | total prepared: %d",
             stats["all_time"]["total_jobs"], stats["all_time"]["total_applied"])

    if skipped:
        print("\n── Jobs you skipped ─────────────────────────────────────")
        for job in skipped:
            print(f"  {job['title']:<40} {_link(job['url'], job['url'])}")

    if auto_rejected:
        print("\n── Auto-rejected (below threshold / disqualified) ───────")
        for job in auto_rejected:
            print(f"  {job['title']:<40} {_link(job['url'], job['url'])}")

    log.info("=" * 60)


if __name__ == "__main__":
    anyio.run(orchestrate)
