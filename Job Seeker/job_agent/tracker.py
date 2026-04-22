"""
Tracker — SQLite-backed application registry.

Responsibilities:
- Persist every job seen and every application submitted
- Prevent duplicate submissions
- Provide run statistics
"""

import sqlite3
import json
import hashlib
from datetime import date
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urlparse, urlunparse

from config import DB_PATH


# ── Schema ─────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id          TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT,
    url             TEXT NOT NULL,
    source          TEXT,
    posted_date     TEXT,
    found_date      TEXT NOT NULL,
    relevance_score INTEGER,
    status          TEXT NOT NULL DEFAULT 'new'
        CHECK(status IN ('new', 'analysed', 'skipped', 'tailored', 'submitted', 'error'))
);

CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL REFERENCES jobs(job_id),
    submitted_date  TEXT NOT NULL,
    method          TEXT,
    confirmation    TEXT,
    cv_file         TEXT,
    letter_file     TEXT,
    outcome         TEXT DEFAULT 'pending'
        CHECK(outcome IN ('pending', 'interview', 'rejected', 'no_response', 'withdrawn')),
    notes           TEXT,
    raw_response    TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status    ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_found     ON jobs(found_date);
CREATE INDEX IF NOT EXISTS idx_apps_job_id    ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_apps_outcome   ON applications(outcome);
"""


# ── Connection helper ──────────────────────────────────────────────────────────

def _normalize_url(url: str) -> str:
    """Strip tracking params and fragments — keep only scheme + host + path."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _ensure_schema_migrations(conn: sqlite3.Connection) -> None:
    """Run any pending schema migrations (one-time per database)."""
    # Migration 1: Add url_normalized column if it doesn't exist, and populate it
    has_column = False
    try:
        conn.execute("SELECT url_normalized FROM jobs LIMIT 1")
        has_column = True
    except sqlite3.OperationalError:
        # Column doesn't exist — add it
        conn.execute("ALTER TABLE jobs ADD COLUMN url_normalized TEXT")

    # Populate url_normalized for all rows where it's NULL
    if has_column or True:  # Always populate, whether we just added or it already existed
        rows = conn.execute("SELECT job_id, url FROM jobs WHERE url_normalized IS NULL").fetchall()
        for row in rows:
            normalized = _normalize_url(row["url"])
            conn.execute(
                "UPDATE jobs SET url_normalized = ? WHERE job_id = ?",
                (normalized, row["job_id"]),
            )

        # Find and consolidate duplicates: for each url_normalized that appears
        # multiple times, keep the row with the best status (submitted > tailored > analysed > skipped > error > new)
        # and delete the others.
        status_rank = {"submitted": 6, "tailored": 5, "analysed": 4, "skipped": 3, "error": 2, "new": 1}

        dups = conn.execute("""
            SELECT url_normalized, COUNT(*) as cnt
            FROM jobs
            WHERE url_normalized IS NOT NULL
            GROUP BY url_normalized
            HAVING cnt > 1
        """).fetchall()

        for dup in dups:
            url_norm = dup["url_normalized"]
            rows = conn.execute(
                "SELECT job_id, status FROM jobs WHERE url_normalized = ?",
                (url_norm,),
            ).fetchall()

            # Keep the one with the highest rank, delete the rest
            if rows:
                # Sort by status rank (submitted > tailored > analysed > skipped > error > new)
                sorted_rows = sorted(rows, key=lambda r: status_rank.get(r["status"], 0), reverse=True)
                keep_id = sorted_rows[0]["job_id"]
                delete_ids = [r["job_id"] for r in sorted_rows[1:]]
                if delete_ids:
                    placeholders = ",".join("?" * len(delete_ids))
                    conn.execute(
                        f"DELETE FROM jobs WHERE job_id IN ({placeholders})",
                        delete_ids,
                    )

        # Now create the unique index (if it doesn't already exist)
        try:
            conn.execute("CREATE UNIQUE INDEX idx_jobs_url_normalized ON jobs(url_normalized) WHERE url_normalized IS NOT NULL")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                pass  # Index already created in a previous run
            elif "UNIQUE constraint failed" in str(e):
                # Still have duplicates — log a warning but continue
                print(f"Warning: Could not create unique index due to remaining duplicates. Upsert logic will handle deduplication.")
            else:
                raise

        conn.commit()


@contextmanager
def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(SCHEMA)
        _ensure_schema_migrations(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Public API ─────────────────────────────────────────────────────────────────

def is_already_applied(job_id: str) -> bool:
    """Return True if we have already submitted an application for this job."""
    with _db() as conn:
        row = conn.execute(
            "SELECT 1 FROM applications WHERE job_id = ?", (job_id,)
        ).fetchone()
        return row is not None


def filter_new_jobs(jobs: list[dict]) -> list[dict]:
    """Return jobs that still need Phase 1 analysis.

    Excluded (already reviewed / decided):
      - 'skipped'   — auto-rejected by analyst OR dismissed by user in Phase 2
      - 'tailored'  — materials already prepared; user applies manually
      - 'submitted' — fully submitted
      - 'analysed'  — passed Phase 1 in a previous run; the Phase 2 resume
                      block in the orchestrator will pick these up separately

    Included (need processing):
      - 'new'   — never seen before
      - 'error' — failed in a previous run; retry
    """
    job_ids = [j["job_id"] for j in jobs]
    if not job_ids:
        return []
    placeholders = ",".join("?" * len(job_ids))
    with _db() as conn:
        rows = conn.execute(
            f"""
            SELECT job_id FROM jobs
            WHERE job_id IN ({placeholders})
              AND status IN ('skipped', 'tailored', 'submitted', 'analysed')
            """,
            job_ids,
        ).fetchall()
    done_ids = {row["job_id"] for row in rows}
    return [j for j in jobs if j["job_id"] not in done_ids]


def upsert_job(job: dict) -> None:
    """Insert or update a job record (idempotent).

    Deduplicates by normalized URL, so the same posting is never inserted twice
    even if it has different job_id values from different runs.
    """
    url_normalized = _normalize_url(job["url"])

    with _db() as conn:
        # Check if this normalized URL already exists
        existing = conn.execute(
            "SELECT job_id FROM jobs WHERE url_normalized = ?",
            (url_normalized,),
        ).fetchone()

        if existing:
            # URL already in DB — update the existing row (keep its job_id)
            job_id = existing["job_id"]
            conn.execute(
                """
                UPDATE jobs
                   SET title        = ?,
                       company      = ?,
                       location     = ?,
                       posted_date  = ?
                 WHERE job_id = ?
                """,
                (
                    job["title"],
                    job["company"],
                    job.get("location", ""),
                    job.get("posted_date", ""),
                    job_id,
                ),
            )
        else:
            # New URL — insert with the provided job_id and url_normalized
            conn.execute(
                """
                INSERT INTO jobs
                    (job_id, title, company, location, url, source, posted_date, found_date, url_normalized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job["job_id"],
                    job["title"],
                    job["company"],
                    job.get("location", ""),
                    job["url"],
                    job.get("source", ""),
                    job.get("posted_date", ""),
                    date.today().isoformat(),
                    url_normalized,
                ),
            )


def update_job_status(job_id: str, status: str, relevance_score: int | None = None) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, relevance_score = COALESCE(?, relevance_score) WHERE job_id = ?",
            (status, relevance_score, job_id),
        )


def log_application(
    job_id: str,
    method: str,
    confirmation: str,
    cv_file: str,
    letter_file: str,
    notes: str = "",
    raw_response: str = "",
) -> None:
    """Record a submitted application."""
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO applications
                (job_id, submitted_date, method, confirmation, cv_file, letter_file, notes, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                date.today().isoformat(),
                method,
                confirmation,
                cv_file,
                letter_file,
                notes,
                raw_response,
            ),
        )
        conn.execute("UPDATE jobs SET status = 'submitted' WHERE job_id = ?", (job_id,))


def log_error(job_id: str, error: str) -> None:
    update_job_status(job_id, "error")
    with _db() as conn:
        conn.execute(
            "INSERT INTO applications (job_id, submitted_date, notes, outcome) VALUES (?, ?, ?, 'pending')",
            (job_id, date.today().isoformat(), f"ERROR: {error}"),
        )


def get_analysed_jobs() -> list[dict]:
    """Return all jobs with status 'analysed' — passed analysis but not yet reviewed by user."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status = 'analysed' ORDER BY relevance_score DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_run_stats() -> dict:
    """Return statistics for the current run and all time."""
    today = date.today().isoformat()
    with _db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        today_found = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE found_date = ?", (today,)
        ).fetchone()[0]
        submitted_total = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE confirmation IS NOT NULL"
        ).fetchone()[0]
        submitted_today = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE submitted_date = ?", (today,)
        ).fetchone()[0]
        skipped = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'skipped'"
        ).fetchone()[0]
        errors = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'error'"
        ).fetchone()[0]

    return {
        "today": {
            "jobs_found":    today_found,
            "submitted":     submitted_today,
        },
        "all_time": {
            "total_jobs":    total,
            "total_applied": submitted_total,
            "skipped":       skipped,
            "errors":        errors,
        },
    }


def reset_jobs(job_ids: list[str]) -> int:
    """Reset the given jobs back to 'new' so they are re-analysed.

    Only resets jobs that have been reviewed/skipped but NOT submitted —
    submitted applications are never touched.

    Returns the number of rows updated.
    """
    if not job_ids:
        return 0
    placeholders = ",".join("?" * len(job_ids))
    with _db() as conn:
        cursor = conn.execute(
            f"""
            UPDATE jobs
               SET status = 'new', relevance_score = NULL
             WHERE job_id IN ({placeholders})
               AND status NOT IN ('submitted')
            """,
            job_ids,
        )
        return cursor.rowcount
