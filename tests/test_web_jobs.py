"""R6/R13 transport: isolation, queue bounds, restart and expired capability failures."""
import json
import sqlite3
import threading

from src.web_jobs import AnswerJobs


def test_single_worker_capacity_and_private_question_results(tmp_path):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def answer(payload):
        calls.append(payload["question"])
        entered.set()
        assert release.wait(5)
        return {"status": "ok", "answer": payload["question"]}

    store = tmp_path / "jobs.sqlite3"
    jobs = AnswerJobs(store, answer, max_pending=2)
    try:
        first = jobs.submit({"question": "first"})
        assert entered.wait(5)
        second = jobs.submit({"question": "second"})
        assert second["job_id"] != first["job_id"]
        assert jobs.poll(first["job_id"]) == {"status": "running"}
        assert jobs.poll(second["job_id"]) == {"status": "queued"}
        assert jobs.submit({"question": "third"})["status"] == "busy"
        assert jobs.poll("x" * 43) == {"status": "not_found"}
        assert calls == ["first"]
    finally:
        release.set()
        jobs.close()
    result = jobs.poll(first["job_id"])
    assert result["result"]["answer"] == "first"
    assert result["request"] == {"question": "first"}
    assert jobs.poll(second["job_id"])["result"]["answer"] == "second"
    assert store.stat().st_mode & 0o077 == 0
    with sqlite3.connect(store) as db:
        assert db.execute("SELECT count(*) FROM jobs WHERE payload IS NOT NULL").fetchone()[0] == 0


def test_restart_never_replays_interrupted_jobs_and_expiry_hides_outputs(tmp_path):
    now = [1000.0]
    path = tmp_path / "jobs.sqlite3"
    jobs = AnswerJobs(path, lambda _: {"status": "ok"}, clock=lambda: now[0])
    jobs.close()
    identity = "a" * 43
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO jobs VALUES (?,?,?,?,NULL)", (identity, now[0], "running", json.dumps({"question": "private"})))
    calls = []
    restarted = AnswerJobs(path, lambda value: calls.append(value), clock=lambda: now[0])
    try:
        result = restarted.poll(identity)["result"]
        assert result["status"] == "service_error" and result["answer"] == ""
        assert "restarted" in result["message"] and not calls
        now[0] += 901
        assert restarted.poll(identity) == {"status": "not_found"}
    finally:
        restarted.close()


def test_provider_exception_does_not_leak_details(tmp_path):
    def answer(_):
        raise RuntimeError("private-provider-credential")

    jobs = AnswerJobs(tmp_path / "jobs.sqlite3", answer)
    job = jobs.submit({"question": "valid question"})
    jobs.close()
    result = jobs.poll(job["job_id"])
    assert result["result"]["status"] == "service_error"
    assert "private-provider" not in json.dumps(result)
