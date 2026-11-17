"""R6/R13: bounded single-worker answer jobs, with private durable status.

The random job ID is a bearer capability. Never log it. A restart marks unfinished
jobs interrupted rather than silently repeating model calls. This queue changes
HTTP transport only; it does not change model controls or open acceptance gates.
"""
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def failed(message):
    return {"status": "service_error", "message": message, "answer": "", "evidence": [],
            "calculations": [], "included_evidence_ids": []}


class AnswerJobs:
    def __init__(self, path, answer, *, max_pending=2, ttl=900, clock=time.time):
        self.path, self.answer, self.clock = Path(path), answer, clock
        if max_pending < 1 or ttl < 1:
            raise ValueError("Positive queue bounds are required")
        self.max_pending, self.ttl = max_pending, ttl
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink() or (self.path.exists() and
                (not self.path.is_file() or self.path.stat().st_mode & 0o077)):
            raise ValueError("Job state must be an owner-only regular file")
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600) if not self.path.exists() else None
        if fd is not None:
            os.close(fd)
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="finrag-answer")
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, created REAL, state TEXT, payload TEXT, result TEXT)")
            db.execute("UPDATE jobs SET state='completed', payload=NULL, result=? WHERE state IN ('queued','running')",
                       (json.dumps(failed("The backend restarted before completion. Submit the question again.")),))
            db.execute("DELETE FROM jobs WHERE created < ?", (self.clock() - self.ttl,))

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def submit(self, payload):
        # The HTTP boundary validates the query; never persist unbounded bodies.
        encoded = json.dumps(payload)
        if not isinstance(payload, dict) or len(encoded.encode()) > 12000:
            raise ValueError("Invalid job payload")
        with self.lock, self.connect() as db:
            db.execute("DELETE FROM jobs WHERE created < ? AND state='completed'", (self.clock() - self.ttl,))
            count = db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0]
            if count >= self.max_pending:
                return {"status": "busy", "message": "The model is busy. Try again after the current questions finish."}
            if db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= 100:
                return {"status": "busy", "message": "The temporary job store is full. Try again later."}
            identity = secrets.token_urlsafe(32)
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,NULL)", (identity, self.clock(), "queued", encoded))
        self.pool.submit(self.execute, identity)
        return {"status": "queued", "job_id": identity, "expires_in_seconds": self.ttl}

    def execute(self, identity):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM jobs WHERE id=? AND state='queued'", (identity,)).fetchone()
            if row is None:
                return
            db.execute("UPDATE jobs SET state='running' WHERE id=?", (identity,))
        try:
            payload = json.loads(row[0])
            result = self.answer(payload)
            if not isinstance(result, dict):
                raise ValueError("Invalid engine result")
            encoded_result = json.dumps({"request": payload, "result": result})
        except Exception:
            result = failed("Financial execution failed; no fallback was used.")
            encoded_result = json.dumps({"request": json.loads(row[0]), "result": result})
        with self.connect() as db:
            db.execute("UPDATE jobs SET state='completed',payload=NULL,result=? WHERE id=?",
                       (encoded_result, identity))

    def poll(self, identity):
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", identity):
            return {"status": "not_found"}
        with self.connect() as db:
            row = db.execute("SELECT created,state,result FROM jobs WHERE id=?", (identity,)).fetchone()
        if row is None or self.clock() - row[0] >= self.ttl:
            return {"status": "not_found"}
        if row[1] != "completed":
            return {"status": row[1]}
        saved = json.loads(row[2])
        # Interrupted jobs have only a sanitized failure, never a stale answer.
        return {"status": "completed", **(saved if "result" in saved else {"result": saved})}

    def close(self):
        self.pool.shutdown(wait=True)
