import sqlite3
from typing import Iterable
from models import Job, FitResult

DB_PATH = "jobs.db"

def conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            url TEXT,
            description TEXT,
            posted_at TEXT,
            UNIQUE(source, source_id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS fits (
            job_id INTEGER PRIMARY KEY,
            fit_score REAL NOT NULL,
            recommend_apply INTEGER NOT NULL,
            rationale TEXT,
            strengths TEXT,
            gaps TEXT,
            resume_tailoring TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
        """)

def upsert_jobs(jobs: Iterable[Job]) -> int:
    inserted = 0
    with conn() as c:
        for j in jobs:
            try:
                c.execute("""
                INSERT INTO jobs (source, source_id, company, title, location, url, description, posted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (j.source, j.source_id, j.company, j.title, j.location, j.url, j.description, j.posted_at))
                inserted += 1
            except sqlite3.IntegrityError:
                pass
    return inserted

def list_jobs(where_sql="", params=()):
    with conn() as c:
        rows = c.execute(f"""
            SELECT id, source, source_id, company, title, location, url, description, posted_at
            FROM jobs
            {where_sql}
            ORDER BY posted_at DESC, id DESC
        """, params).fetchall()
    return rows

def save_fit(job_id: int, fit: FitResult):
    import json
    with conn() as c:
        c.execute("""
        INSERT INTO fits (job_id, fit_score, recommend_apply, rationale, strengths, gaps, resume_tailoring)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            fit_score=excluded.fit_score,
            recommend_apply=excluded.recommend_apply,
            rationale=excluded.rationale,
            strengths=excluded.strengths,
            gaps=excluded.gaps,
            resume_tailoring=excluded.resume_tailoring
        """, (
            job_id,
            float(fit.fit_score),
            1 if fit.recommend_apply else 0,
            fit.rationale,
            json.dumps(fit.strengths),
            json.dumps(fit.gaps),
            json.dumps(fit.resume_tailoring),
        ))

def get_fit(job_id: int):
    with conn() as c:
        row = c.execute("SELECT fit_score, recommend_apply, rationale, strengths, gaps, resume_tailoring FROM fits WHERE job_id=?",
                        (job_id,)).fetchone()
    return row
