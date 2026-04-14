"""
Tracker — SQLite-backed application registry.

Responsibilities:
- Persist every job seen and every application submitted
- Prevent duplicate submissions
- Provide run statistics
"""

import sqlite3
import json
from datetime import date
from pathlib import Path
from contextlib import contextmanager

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

@contextmanager
def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(SCHEMA)
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
    """Return only jobs that have not been applied to yet."""
    return [j for j in jobs if not is_already_applied(j["job_id"])]


def upsert_job(job: dict) -> None:
    """Insert or update a job record (idempotent)."""
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO jobs (job_id, title, company, location, url, source, posted_date, found_date)
            VALUES (:job_id, :title, :company, :location, :url, :source, :posted_date, :found_date)
            ON CONFLICT(job_id) DO UPDATE SET
                title        = excluded.title,
                company      = excluded.company,
                location     = excluded.location,
                posted_date  = excluded.posted_date
            """,
            {
                "job_id":      job["job_id"],
                "title":       job["title"],
                "company":     job["company"],
                "location":    job.get("location", ""),
                "url":         job["url"],
                "source":      job.get("source", ""),
                "posted_date": job.get("posted_date", ""),
                "found_date":  date.today().isoformat(),
            },
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
