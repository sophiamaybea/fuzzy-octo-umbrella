"""Small inspectable registry; only local CLI can change human-review status."""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    repo TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('CANDIDATE', 'APPROVED', 'REJECTED')),
    reviewer_note TEXT NOT NULL DEFAULT '',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    reviewed_at TEXT
);
"""

def db_path() -> Path:
    return Path(os.getenv("HUNTER_DATABASE", "./capability-hunter.sqlite3"))

def connect(path: str | Path | None = None):
    location = Path(path) if path is not None else db_path()
    location.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(location)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def upsert(conn: sqlite3.Connection, repo: dict, query: str):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
      INSERT INTO candidates(repo, query, metadata_json, status, first_seen, last_seen)
      VALUES (?, ?, ?, 'CANDIDATE', ?, ?)
      ON CONFLICT(repo) DO UPDATE SET
      query=excluded.query, metadata_json=excluded.metadata_json, last_seen=excluded.last_seen
    """, (repo["repo"], query, json.dumps(repo, ensure_ascii=False), now, now))
    conn.commit()

def review(conn: sqlite3.Connection, repo: str, decision: str, note: str):
    if decision not in {"APPROVED", "REJECTED", "CANDIDATE"}:
        raise ValueError("Decision must be APPROVED, REJECTED, or CANDIDATE")
    result = conn.execute("""
      UPDATE candidates SET status=?, reviewer_note=?, reviewed_at=? WHERE repo=?
    """, (decision, note[:1500], datetime.now(timezone.utc).isoformat(), repo))
    conn.commit()
    if result.rowcount != 1:
        raise ValueError("Unknown candidate: run scan first")

def list_records(conn: sqlite3.Connection, status: str | None = None, limit: int = 50):
    limit = max(1, min(int(limit), 100))
    if status and status not in {"CANDIDATE", "APPROVED", "REJECTED"}:
        raise ValueError("Invalid status")
    sql = "SELECT * FROM candidates"
    params: list = []
    if status:
        sql += " WHERE status=?"
        params.append(status)
    sql += " ORDER BY last_seen DESC LIMIT ?"
    params.append(limit)
    out = []
    for item in conn.execute(sql, params):
        out.append({
            "repo": item["repo"], "query": item["query"],
            "status": item["status"], "reviewer_note": item["reviewer_note"],
            "reviewed_at": item["reviewed_at"], "last_seen": item["last_seen"],
            "metadata": json.loads(item["metadata_json"]),
        })
    return out
