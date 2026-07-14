import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from lib import config
from lib.types import ReviewResult

_DB_PATH = config.DATABASE_PATH if os.path.isabs(config.DATABASE_PATH) else os.path.join(os.getcwd(), config.DATABASE_PATH)
os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_runs (
    id TEXT PRIMARY KEY,
    document_title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_reference TEXT,
    template_type TEXT NOT NULL,
    review_timestamp TEXT NOT NULL,
    completeness_score INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    llm_used INTEGER NOT NULL DEFAULT 0,
    llm_provider TEXT NOT NULL DEFAULT 'none',
    llm_model TEXT,
    llm_input_tokens INTEGER NOT NULL DEFAULT 0,
    llm_output_tokens INTEGER NOT NULL DEFAULT 0,
    llm_estimated_cost_usd REAL NOT NULL DEFAULT 0,
    result_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    review_run_id TEXT NOT NULL,
    section_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    suggested_question TEXT NOT NULL,
    origin TEXT NOT NULL,
    FOREIGN KEY (review_run_id) REFERENCES review_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(review_run_id);
"""


@contextmanager
def _connect():
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.executescript(_SCHEMA)
    try:
        yield conn
    finally:
        conn.close()


def save_review_run(result: ReviewResult) -> None:
    result_dict = asdict(result)
    with _connect() as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO review_runs (
                    id, document_title, source_type, source_reference, template_type, review_timestamp,
                    completeness_score, status, error_message, duration_ms,
                    llm_used, llm_provider, llm_model, llm_input_tokens, llm_output_tokens, llm_estimated_cost_usd,
                    result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.document_title,
                    result.source_type,
                    result.source_reference,
                    result.template_type,
                    result.review_timestamp,
                    result.completeness_score,
                    result.status,
                    None,
                    result.duration_ms,
                    1 if result.llm_usage.used else 0,
                    result.llm_usage.provider,
                    result.llm_usage.model,
                    result.llm_usage.input_tokens,
                    result.llm_usage.output_tokens,
                    result.llm_usage.estimated_cost_usd,
                    json.dumps(result_dict),
                ),
            )
            for f in result.findings:
                conn.execute(
                    """
                    INSERT INTO findings (
                        id, review_run_id, section_name, severity, issue_type, description,
                        why_it_matters, suggested_question, origin
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f.id,
                        result.id,
                        f.section_name,
                        f.severity,
                        f.issue_type,
                        f.description,
                        f.why_it_matters,
                        f.suggested_question,
                        f.origin,
                    ),
                )


def list_review_runs() -> list[dict]:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, document_title, source_type, template_type, review_timestamp, completeness_score, status
            FROM review_runs ORDER BY review_timestamp DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_review_run(run_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT result_json FROM review_runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return json.loads(row[0])


def _window_start_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def get_usage_stats() -> dict:
    since_24h = _window_start_iso(24)

    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        totals = conn.execute(
            """
            SELECT
                COUNT(*) as total_analyses,
                COALESCE(SUM(llm_used), 0) as llm_used_runs,
                COALESCE(SUM(llm_input_tokens), 0) as llm_input_tokens_total,
                COALESCE(SUM(llm_output_tokens), 0) as llm_output_tokens_total,
                COALESCE(SUM(llm_estimated_cost_usd), 0) as estimated_cost_usd_total
            FROM review_runs
            """
        ).fetchone()

        window_24h = conn.execute(
            """
            SELECT
                COUNT(*) as analyses_24h,
                COALESCE(SUM(llm_used), 0) as llm_used_runs_24h,
                COALESCE(AVG(duration_ms), 0) as avg_duration_ms_24h,
                COALESCE(SUM(llm_input_tokens + llm_output_tokens), 0) as llm_tokens_total_24h,
                COALESCE(SUM(llm_estimated_cost_usd), 0) as estimated_cost_usd_24h
            FROM review_runs WHERE review_timestamp >= ?
            """,
            (since_24h,),
        ).fetchone()

    return {
        "data_refreshed_at": datetime.now(timezone.utc).isoformat(),
        "total_analyses": totals["total_analyses"],
        "analyses_24h": window_24h["analyses_24h"],
        "avg_duration_seconds_24h": round((window_24h["avg_duration_ms_24h"] / 1000) * 10) / 10,
        "llm_enabled": config.LLM_REVIEW_ENABLED,
        "llm_used_runs": totals["llm_used_runs"],
        "llm_used_runs_24h": window_24h["llm_used_runs_24h"],
        "rule_only_runs": totals["total_analyses"] - totals["llm_used_runs"],
        "llm_input_tokens_total": totals["llm_input_tokens_total"],
        "llm_output_tokens_total": totals["llm_output_tokens_total"],
        "llm_tokens_total": totals["llm_input_tokens_total"] + totals["llm_output_tokens_total"],
        "llm_tokens_total_24h": window_24h["llm_tokens_total_24h"],
        "estimated_cost_usd_total": totals["estimated_cost_usd_total"],
        "estimated_cost_usd_24h": window_24h["estimated_cost_usd_24h"],
    }
