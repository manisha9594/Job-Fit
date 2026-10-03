"""Saved job analyses: a local table of JDs you've analyzed, exportable to PDF.

Lives in the same gitignored SQLite file as the tracker. List-valued columns
(top skills, gaps, questions) are stored as JSON.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from io import BytesIO
from pathlib import Path

from .tracker import DEFAULT_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT DEFAULT '',
    url TEXT DEFAULT '',
    fit_score INTEGER,
    verdict TEXT DEFAULT '',
    top_skills TEXT NOT NULL DEFAULT '[]',
    gaps TEXT NOT NULL DEFAULT '[]',
    questions TEXT NOT NULL DEFAULT '[]',
    notes TEXT DEFAULT '',
    resume TEXT DEFAULT '',
    saved_at REAL NOT NULL
);
"""
JSON_COLS = ("top_skills", "gaps", "questions")
EDITABLE = ("title", "company", "url", "notes")


class SavedJobs:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or os.getenv("TRACKER_DB") or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        d = dict(row)
        for col in JSON_COLS:
            d[col] = json.loads(d[col] or "[]")
        return d

    def add(self, job: dict) -> dict:
        title = (job.get("title") or "").strip()
        if not title:
            raise ValueError("title is required")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO saved_jobs (title, company, url, fit_score, verdict,"
                " top_skills, gaps, questions, notes, resume, saved_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, job.get("company", ""), job.get("url", ""),
                 job.get("fit_score"), job.get("verdict", ""),
                 *(json.dumps(job.get(c) or []) for c in JSON_COLS),
                 job.get("notes", ""), job.get("resume", ""), time.time()),
            )
            return self.get(cur.lastrowid, conn)

    def get(self, job_id: int, conn=None) -> dict | None:
        conn = conn or self._connect()
        row = conn.execute("SELECT * FROM saved_jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row(row) if row else None

    def list(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM saved_jobs ORDER BY saved_at DESC").fetchall()
        return [self._row(r) for r in rows]

    def update(self, job_id: int, fields: dict) -> dict | None:
        fields = {k: v for k, v in fields.items() if k in EDITABLE and v is not None}
        with self._connect() as conn:
            if fields:
                sets = ", ".join(f"{k} = ?" for k in fields)
                conn.execute(f"UPDATE saved_jobs SET {sets} WHERE id = ?",
                             (*fields.values(), job_id))
            return self.get(job_id, conn)

    def delete(self, job_id: int) -> bool:
        with self._connect() as conn:
            return conn.execute("DELETE FROM saved_jobs WHERE id = ?", (job_id,)).rowcount > 0


def export_pdf(jobs: list[dict]) -> bytes:
    """Summary table of all saved jobs, then one page section per job with its
    interview questions."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)
    from xml.sax.saxutils import escape

    styles = getSampleStyleSheet()
    cell = styles["BodyText"].clone("cell", fontSize=8.5, leading=11)
    head = cell.clone("head", fontName="Helvetica-Bold", textColor=colors.white)

    def p(text, style=cell):
        return Paragraph(escape(str(text or "")), style)

    def skills_text(job):
        return ", ".join(s["skill"] if isinstance(s, dict) else str(s)
                         for s in job["top_skills"])

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), title="Saved Jobs",
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = [Paragraph("Saved Jobs", styles["Title"]),
             p(f"{len(jobs)} job(s) · exported {time.strftime('%Y-%m-%d %H:%M')}"),
             Spacer(1, 10)]

    header = ["Saved", "Role", "Company", "Fit", "Top skills", "Gaps", "Notes"]
    rows = [[p(h, head) for h in header]]
    for j in jobs:
        rows.append([
            p(time.strftime("%Y-%m-%d", time.localtime(j["saved_at"]))),
            p(j["title"]), p(j["company"]),
            p("" if j["fit_score"] is None else f"{j['fit_score']}/100"),
            p(skills_text(j)), p(", ".join(j["gaps"])), p(j["notes"]),
        ])
    table = Table(rows, repeatRows=1, colWidths=[
        0.8 * inch, 1.6 * inch, 1.3 * inch, 0.6 * inch, 2.4 * inch, 1.6 * inch, 1.7 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a68")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fa")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c5cddb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)

    for j in jobs:
        if not j["questions"]:
            continue
        title = j["title"] + (f" @ {j['company']}" if j["company"] else "")
        block = [Spacer(1, 16), Paragraph(escape(title), styles["Heading2"])]
        if j["url"]:
            block.append(p(j["url"]))
        block.append(Paragraph("Interview prep", styles["Heading4"]))
        block += [p(f"{i}. {q}") for i, q in enumerate(j["questions"], 1)]
        story.append(KeepTogether(block))

    doc.build(story)
    return buf.getvalue()
