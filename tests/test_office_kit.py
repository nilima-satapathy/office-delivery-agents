"""Checks for the office-agent kit. These do not call a model or JIRA."""

import json
import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
CHECKLIST = KIT / "ready_checklist.json"
EVALS = KIT / "evals" / "requirements_ambiguous.json"
JIRA = KIT / "scripts" / "jira_draft.py"

sys.path.insert(0, str(KIT / "scripts"))
import jira_draft  # noqa: E402


def test_checklist_fields_are_unique():
    data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    fields = data["fields"]
    assert len(fields) == len(set(fields))
    assert "acceptance_criteria" in fields
    assert data["start_rules"]


def test_ambiguous_cases_cover_ten_and_only_known_fields():
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == 10
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    allowed = set(checklist["fields"])
    for case in cases:
        assert case["missing_field"] in allowed
        assert case["brief"].strip()
    assert "assumptions" in data["pass_rule"]


def test_draft_payload_has_no_transition_and_labels_role():
    payload = jira_draft.issue_payload(
        project="AERO",
        issue_type="Story",
        summary="Show fleet status",
        description="Draft only",
        external_id="show-fleet-status",
    )
    assert "transition" not in payload
    assert "transition" not in payload["fields"]
    assert payload["fields"]["labels"] == ["agent:requirements", "agent-ext-show-fleet-status"]
    assert payload["fields"]["issuetype"]["name"] == "Story"


def test_bug_label_and_subtask_parent_rule():
    bug = jira_draft.issue_payload(
        project="AERO",
        issue_type="Bug",
        summary="Status code 500",
        description="steps",
        external_id="status-500",
    )
    assert bug["fields"]["labels"][0] == "agent:qa"
    try:
        jira_draft.issue_payload(
            project="AERO",
            issue_type="Sub-task",
            summary="Write the query",
            description="",
            external_id="write-query",
        )
    except ValueError as error:
        assert "parent_key" in str(error)
    else:
        raise AssertionError("Sub-task without a parent was accepted")


def test_missing_env_does_not_create():
    result = jira_draft.create_issue({"fields": {}}, {})
    assert result["created"] is False
    assert result["reason"] == "JIRA not connected"


def test_dry_run_cli_exits_2_without_token_in_output():
    completed = subprocess.run(
        [
            sys.executable,
            str(JIRA),
            "--type",
            "Bug",
            "--summary",
            "Export failed",
            "--description",
            "See trace",
            "--external-id",
            "export-failed",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "JIRA_API_TOKEN": "secret-token-value"},
    )
    assert completed.returncode == 2
    assert "secret-token-value" not in completed.stdout
    body = json.loads(completed.stdout)
    assert body["reason"] == "dry-run"
    assert "transition" not in body["payload"]
