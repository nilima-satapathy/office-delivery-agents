"""Presenter demo API. No browser and no live server."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))

import app  # noqa: E402


def test_walkthrough_blocks_until_a_person_approves_then_fleet_works():
    status, content_type, body = app.dispatch("POST", "/api/reset")
    assert status == 200
    state = json.loads(body)
    assert state["allowed"] is False
    assert "actor" in state["missing_fields"]

    state = json.loads(app.dispatch("POST", "/api/ask")[2])
    assert state["allowed"] is False
    assert state["open_questions"]

    state = json.loads(app.dispatch("POST", "/api/answer")[2])
    assert state["story"]["actor"] == "signed-in technician"
    assert state["allowed"] is False

    refused = app.dispatch("POST", "/api/approve", b'{"name":"agent"}')
    assert refused[0] == 400

    state = json.loads(app.dispatch("POST", "/api/approve", b'{"name":"Alex Morgan"}')[2])
    assert state["allowed"] is True
    assert state["approver"] == "Alex Morgan"
    assert [item["type"] for item in state["drafts"]] == ["Epic", "Story", "Sub-task", "Bug"]
    assert all(item["connected"] is False for item in state["drafts"])

    fleet = json.loads(app.dispatch("GET", "/api/fleet?token=tech-1")[2])
    assert fleet["status"] == 200
    assert "N123 serviceable" in fleet["page"]
    empty = json.loads(app.dispatch("GET", "/api/fleet?token=tech-1&empty=1")[2])
    assert empty["page"] == "No aircraft"
    stranger = json.loads(app.dispatch("GET", "/api/fleet?token=visitor")[2])
    assert stranger["status"] == 403
    assert stranger["page"] == "Forbidden"

    tested = json.loads(app.dispatch("POST", "/api/test")[2])
    assert tested["tests"]["unit_failed"] == 0
    assert tested["tests"]["e2e_passed"] == 2
    accepted = json.loads(app.dispatch("POST", "/api/accept")[2])
    assert accepted["accepted_by"] == "Alex Morgan"

    page = app.dispatch("GET", "/")
    assert page[0] == 200
    assert b"Four agents. One approved story." in page[2]
    assert content_type.startswith("application/json")


def test_fleet_stays_locked_and_accept_waits_for_tests():
    app.dispatch("POST", "/api/reset")
    locked = app.dispatch("GET", "/api/fleet?token=tech-1")
    assert locked[0] == 400
    app.dispatch("POST", "/api/ask")
    app.dispatch("POST", "/api/answer")
    early = app.dispatch("POST", "/api/accept")
    assert early[0] == 400
