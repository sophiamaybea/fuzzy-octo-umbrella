"""Reviewable correction ledger, not model training or unquestioned self-learning.

Stores small corrections only when explicitly submitted. Runtime deployments need a
persistent private disk; hosted ephemeral storage is NOT durable learning.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

MAX_NOTE = 1500
SCHEMA = """
CREATE TABLE IF NOT EXISTS philosophy_lessons (
    id TEXT PRIMARY KEY,
    question_sha256 TEXT NOT NULL,
    alleged_error TEXT NOT NULL,
    proposed_correction TEXT NOT NULL,
    evidence_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
      CHECK(status IN ('PENDING','VERIFIED','REJECTED')),
    reviewer_note TEXT NOT NULL DEFAULT '',
    created_at_utc TEXT NOT NULL,
    reviewed_at_utc TEXT
);
"""


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    dbpath = Path(path or os.environ.get('PHILOSOPHY_LESSON_DB', './data/philosophy-lessons.sqlite3'))
    dbpath.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(dbpath, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _note(s: str, label: str) -> str:
    if not isinstance(s, str) or not 8 <= len(s.strip()) <= MAX_NOTE:
        raise ValueError(f'{label} must contain 8–{MAX_NOTE} characters')
    return s.strip()


def record_correction(
    question: str, alleged_error: str, proposed_correction: str,
    evidence_url: str = '', *, db_path: str | Path | None = None,
) -> dict:
    if not isinstance(question, str) or not 8 <= len(question) <= 4000:
        raise ValueError('Question must be 8–4,000 characters')
    err = _note(alleged_error, 'alleged_error')
    corrected = _note(proposed_correction, 'proposed_correction')
    if not isinstance(evidence_url, str) or len(evidence_url) > 600:
        raise ValueError('Invalid evidence_url')
    if evidence_url and not re.fullmatch(r'https://[^\s\x00-\x1f]+', evidence_url):
        raise ValueError('evidence_url must be HTTPS (or empty)')
    item_id = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as db:
        db.execute('''INSERT INTO philosophy_lessons
            (id,question_sha256,alleged_error,proposed_correction,evidence_url,created_at_utc)
            VALUES (?,?,?,?,?,?)''', (
            item_id, hashlib.sha256(question.encode('utf8')).hexdigest(),
            err, corrected, evidence_url, now))
    return {'id': item_id, 'status': 'PENDING', 'created_at_utc': now,
            'notice': 'Candidate correction saved; NOT accepted as a verified fact.'}


def list_lessons(
    status: str = 'VERIFIED', limit: int = 20, *, db_path: str | Path | None = None,
) -> list[dict]:
    if status not in ('VERIFIED','PENDING','REJECTED'):
        raise ValueError('Invalid status')
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1 <= limit <= 100:
        raise ValueError('limit must be 1–100')
    with connect(db_path) as db:
        rows = db.execute('''SELECT id,question_sha256,alleged_error,proposed_correction,
            evidence_url,status,reviewer_note,created_at_utc,reviewed_at_utc
            FROM philosophy_lessons WHERE status=? ORDER BY created_at_utc DESC LIMIT ?''',
                          (status,limit)).fetchall()
    return [dict(r) for r in rows]


def review_correction(
    lesson_id: str, decision: str, reviewer_note: str,
    *, db_path: str | Path | None = None,
) -> dict:
    """Local CLI/human-only review: never expose this operation through remote MCP."""
    if decision not in ('VERIFIED','REJECTED'):
        raise ValueError('Only VERIFIED or REJECTED review decisions are supported')
    note = _note(reviewer_note, 'reviewer_note')
    if not re.fullmatch(r'[a-f0-9]{32}', lesson_id):
        raise ValueError('Invalid lesson id')
    with connect(db_path) as db:
        row = db.execute('SELECT status FROM philosophy_lessons WHERE id=?', (lesson_id,)).fetchone()
        if not row or row['status'] != 'PENDING':
            raise ValueError('Lesson does not exist or is already reviewed')
        db.execute('''UPDATE philosophy_lessons SET status=?,reviewer_note=?,reviewed_at_utc=?
            WHERE id=?''', (decision,note,datetime.now(timezone.utc).isoformat(),lesson_id))
    return {'id': lesson_id, 'status': decision, 'reviewer_note': note}
