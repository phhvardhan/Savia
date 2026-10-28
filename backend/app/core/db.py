import os
import sqlite3
import threading
from contextlib import contextmanager
from app.core.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    version INTEGER NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT,
    UNIQUE (workflow_id, agent_name, version)
);
CREATE INDEX IF NOT EXISTS ix_artifacts_workflow ON artifacts (workflow_id);
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL,
    input_hash TEXT,
    artifact_id TEXT,
    error TEXT,
    created_at TEXT,
    started_at TEXT,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_runs_workflow ON runs (workflow_id);
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    purpose TEXT,
    provider TEXT,
    model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms INTEGER,
    finish_reason TEXT,
    ok INTEGER,
    error TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_llm_calls_run ON llm_calls (run_id);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        with self.transaction() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def transaction(self):
        with self._lock:
            conn = self._connect()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        conn = self._connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.transaction() as conn:
            conn.execute(sql, params)


db = Database(settings.DB_PATH)
