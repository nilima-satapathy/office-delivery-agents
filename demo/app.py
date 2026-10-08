"""Presenter API for the office-delivery demo. No model and no JIRA."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "scripts"))
sys.path.insert(0, str(KIT / "mock-run"))

from backend.fleet import SAMPLE, list_aircraft  # noqa: E402
from frontend.page import render  # noqa: E402
from run_mock_pipeline import (  # noqa: E402
    DATA,
    MOCK,
    approval_names,
    build_allowed,
    jira_dry_run,
    missing_fields,
    open_questions,
    reset_gate_files,
    run_pytest,
    scenarios_for,
    write_report,
)

PAGE = Path(__file__).resolve().parent / "static" / "index.html"
STATE_PATH = MOCK / "docs" / "demo-state.json"
QUESTIONS = MOCK / "docs" / "questions.md"
APPROVALS = MOCK / "docs" / "approvals.md"
CONTRACT = MOCK / "contracts" / "active-story.json"
STORY_KEY = "MOCK-2"
QUESTION = "Who is the actor, and what does done look like?"
ANSWER = "Signed-in technician sees tails and status."
LOCK = threading.Lock()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _blank_state() -> dict:
    return {"asked": False, "answered": False, "drafts": [], "tests": None, "accepted_by": ""}


def _read_state() -> dict:
    if not STATE_PATH.exists():
        return _blank_state()
    data = _load_json(STATE_PATH)
    base = _blank_state()
    base.update(data)
    return base


def _write_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _story() -> dict:
    return _load_json(DATA / "approved-story.json")


def _brief() -> str:
    return _load_json(DATA / "ambiguous-brief.json")["brief"]


def _active_story(state: dict) -> dict:
    if state["answered"]:
        return _story()
    return {"story_key": STORY_KEY, "brief": _brief()}


def snapshot(state: dict | None = None) -> dict:
    state = _read_state() if state is None else state
    story = _active_story(state)
    allowed, reason = build_allowed(story, QUESTIONS, APPROVALS)
    names = approval_names(APPROVALS, STORY_KEY)
    contract = None
    if allowed and CONTRACT.exists():
        contract = _load_json(CONTRACT)
    tests = state["tests"]
    if not state["asked"]:
        phase = "clarify"
    elif not state["answered"]:
        phase = "clarify"
    elif not allowed:
        phase = "approve"
    elif not tests:
        phase = "build"
    elif not state["accepted_by"]:
        phase = "test"
    else:
        phase = "sign-off"
    return {
        "brief": _brief(),
        "phase": phase,
        "asked": state["asked"],
        "answered": state["answered"],
        "missing_fields": [] if state["answered"] else missing_fields(story),
        "open_questions": open_questions(QUESTIONS, STORY_KEY),
        "allowed": allowed,
        "reason": reason,
        "approver": names[0] if names else "",
        "story": _story() if state["answered"] else None,
        "contract": contract,
        "drafts": state["drafts"],
        "tests": tests,
        "accepted_by": state["accepted_by"],
        "scenarios": scenarios_for(_story()["acceptance_criteria"]) if state["answered"] else [],
    }


def reset() -> dict:
    with LOCK:
        reset_gate_files()
        if CONTRACT.exists():
            CONTRACT.unlink()
        state = _blank_state()
        _write_state(state)
        return snapshot(state)


def ask() -> dict:
    with LOCK:
        state = _read_state()
        if not state["asked"]:
            with QUESTIONS.open("a", encoding="utf-8") as handle:
                handle.write(f"| {STORY_KEY} | {QUESTION} | Mock client | |\n")
            state["asked"] = True
            state["answered"] = False
            state["accepted_by"] = ""
            _write_state(state)
        return snapshot(state)


def answer() -> dict:
    with LOCK:
        state = _read_state()
        if not state["asked"]:
            raise ValueError("Ask the requirements agent before recording an answer.")
        text = QUESTIONS.read_text(encoding="utf-8")
        blank = f"| {STORY_KEY} | {QUESTION} | Mock client | |"
        filled = f"| {STORY_KEY} | {QUESTION} | Mock client | {ANSWER} |"
        if blank in text:
            QUESTIONS.write_text(text.replace(blank, filled), encoding="utf-8")
        elif filled not in text:
            raise ValueError("The open question row is missing.")
        state["answered"] = True
        _write_state(state)
        return snapshot(state)


def approve(name: str) -> dict:
    with LOCK:
        state = _read_state()
        if not state["answered"]:
            raise ValueError("Record the client answer before approval.")
        clean = " ".join(name.split())
        if not clean or "agent" in clean.lower():
            raise ValueError("Enter the stakeholder's name.")
        line = f"Approved: {clean} — {STORY_KEY}"
        current = APPROVALS.read_text(encoding="utf-8")
        if line not in current:
            APPROVALS.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8")
        contract = {
            "story_key": STORY_KEY,
            "paths": ["GET /api/aircraft"],
            "fields": ["tail", "status"],
            "errors": ["403 forbidden"],
            "auth": "token tech-1",
            "ui_states": ["list", "No aircraft", "Forbidden"],
            "open_questions": [],
        }
        CONTRACT.parent.mkdir(exist_ok=True)
        CONTRACT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        created = [
            jira_dry_run("Epic", "Fleet status board", "mock-1"),
            jira_dry_run("Story", "Technician sees aircraft status", "mock-2"),
            jira_dry_run("Sub-task", "List aircraft API", "mock-3", parent_key=STORY_KEY),
            jira_dry_run("Bug", "Forbidden page missing", "mock-bug-seed", parent_key=STORY_KEY),
        ]
        state["drafts"] = [
            {
                "type": item["payload"]["fields"]["issuetype"]["name"],
                "summary": item["payload"]["fields"]["summary"],
                "labels": item["payload"]["fields"]["labels"],
                "connected": item["created"],
            }
            for item in created
        ]
        state["accepted_by"] = ""
        _write_state(state)
        return snapshot(state)


def run_tests() -> dict:
    with LOCK:
        state = _read_state()
        story = _active_story(state)
        allowed, reason = build_allowed(story, QUESTIONS, APPROVALS)
        if not allowed:
            raise ValueError(reason)
        counts = {}
        for layer, filename in (("unit", "test_unit.py"), ("api", "test_api.py"), ("e2e", "test_e2e.py")):
            completed, passed, failed = run_pytest(MOCK / "tests" / filename)
            if completed.returncode != 0:
                raise RuntimeError(completed.stdout + completed.stderr)
            counts[f"{layer}_passed"] = passed
            counts[f"{layer}_failed"] = failed
        state["tests"] = counts
        state["accepted_by"] = ""
        _write_state(state)
        write_report(
            counts,
            ["Seeded dry-run only, not a product failure: Forbidden page missing. JIRA is not connected."],
            [],
            "A person still accepts the story. The demo records that name locally and does not close JIRA.",
        )
        return snapshot(state)


def accept() -> dict:
    with LOCK:
        state = _read_state()
        view = snapshot(state)
        if not view["allowed"]:
            raise ValueError(view["reason"])
        tests = state["tests"] or {}
        failed = sum(tests.get(key, 0) for key in ("unit_failed", "api_failed", "e2e_failed"))
        if not tests or failed:
            raise ValueError("Run the tests before accepting the story.")
        state["accepted_by"] = view["approver"]
        _write_state(state)
        return snapshot(state)


def fleet(query: str) -> dict:
    view = snapshot()
    if not view["allowed"]:
        raise ValueError(view["reason"])
    params = parse_qs(query)
    token = params.get("token", [""])[0] or None
    empty = params.get("empty", ["0"])[0] == "1"
    status, body = list_aircraft(() if empty else SAMPLE, token)
    return {"status": status, "page": render(status, body), "aircraft": body.get("aircraft", [])}


def dispatch(method: str, path: str, body: bytes = b"") -> tuple[int, str, bytes]:
    parsed = urlparse(path)
    route = parsed.path
    try:
        if method == "GET" and route == "/":
            return 200, "text/html; charset=utf-8", PAGE.read_bytes()
        if method == "GET" and route == "/api/state":
            payload = snapshot()
        elif method == "POST" and route == "/api/reset":
            payload = reset()
        elif method == "POST" and route == "/api/ask":
            payload = ask()
        elif method == "POST" and route == "/api/answer":
            payload = answer()
        elif method == "POST" and route == "/api/approve":
            data = json.loads(body.decode() or "{}")
            payload = approve(str(data.get("name", "")))
        elif method == "POST" and route == "/api/test":
            payload = run_tests()
        elif method == "POST" and route == "/api/accept":
            payload = accept()
        elif method == "GET" and route == "/api/fleet":
            payload = fleet(parsed.query)
        else:
            return 404, "application/json", b'{"error":"not found"}'
    except ValueError as error:
        return 400, "application/json", json.dumps({"error": str(error)}).encode()
    except RuntimeError as error:
        return 500, "application/json", json.dumps({"error": str(error)}).encode()
    return 200, "application/json", json.dumps(payload).encode()
