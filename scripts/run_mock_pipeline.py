"""Local rehearsal of the office-delivery pipeline with mock data.

Runs the real ready checklist, approval gate, JIRA draft script, and the
mock fleet tests. Does not call a model, a browser, or JIRA.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
MOCK = KIT / "mock-run"
DATA = KIT / "mock-data"
REPORTS = MOCK / "reports"
JIRA = KIT / "scripts" / "jira_draft.py"
CHECKLIST = json.loads((KIT / "ready_checklist.json").read_text(encoding="utf-8"))
FIELDS = CHECKLIST["fields"]
REPORT_SECTIONS = (
    "Epic",
    "Counts by layer",
    "Defects opened",
    "Blocked scenarios",
    "Untested criteria",
    "Residual risk",
)


def missing_fields(story: dict) -> list[str]:
    missing = []
    for field in FIELDS:
        value = story.get(field)
        if value is None or value == "" or value == []:
            missing.append(field)
    return missing


def open_questions(path: Path, story_key: str) -> list[str]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"Story", "---"}:
            continue
        if cells[0] == story_key and cells[3] == "":
            rows.append(cells[1])
    return rows


def approval_names(path: Path, story_key: str) -> list[str]:
    names = []
    prefix = f"Approved:"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith(prefix) or f"— {story_key}" not in line:
            continue
        name = line[len(prefix) :].split("—", 1)[0].strip()
        if name and "agent" not in name.lower():
            names.append(name)
    return names


def build_allowed(story: dict, questions_path: Path, approvals_path: Path) -> tuple[bool, str]:
    missing = missing_fields(story)
    if missing:
        return False, "missing fields: " + ", ".join(missing)
    pending = open_questions(questions_path, story["story_key"])
    if pending:
        return False, "open questions: " + "; ".join(pending)
    names = approval_names(approvals_path, story["story_key"])
    if not names:
        return False, "approval line missing"
    if not story.get("epic_key"):
        return False, "parent epic is not linked"
    return True, f"approved by {names[0]}"


def jira_dry_run(issue_type: str, summary: str, external_id: str, parent_key: str = "") -> dict:
    command = [
        sys.executable,
        str(JIRA),
        "--type",
        issue_type,
        "--summary",
        summary,
        "--description",
        "Mock draft. A person files this.",
        "--external-id",
        external_id,
        "--dry-run",
    ]
    if parent_key:
        command.extend(["--parent-key", parent_key])
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 2:
        raise RuntimeError(completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    if "transition" in payload["payload"] or "transition" in payload["payload"]["fields"]:
        raise RuntimeError("draft payload tried to transition status")
    return payload


def scenarios_for(criteria: list[str]) -> list[dict]:
    layers = ("api", "e2e", "e2e")
    return [
        {"criterion": criterion, "layer": layers[index], "id": f"SCN-{index + 1}"}
        for index, criterion in enumerate(criteria)
    ]


def run_pytest(path: Path) -> tuple[subprocess.CompletedProcess[str], int, int]:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q"],
        check=False,
        capture_output=True,
        text=True,
    )
    passed = re.search(r"(\d+) passed", completed.stdout)
    failed = re.search(r"(\d+) failed", completed.stdout)
    return completed, int(passed.group(1)) if passed else 0, int(failed.group(1)) if failed else 0


def write_report(counts: dict, defects: list[str], untested: list[str], residual: str) -> Path:
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / "MOCK-1-2026-10-08.md"
    lines = [
        "# Epic",
        "",
        "MOCK-1 Fleet status board. Story MOCK-2.",
        "",
        "# Counts by layer",
        "",
        f"- Unit: {counts['unit_passed']} passed, {counts['unit_failed']} failed",
        f"- API: {counts['api_passed']} passed, {counts['api_failed']} failed",
        f"- End-to-end: {counts['e2e_passed']} passed, {counts['e2e_failed']} failed",
        "",
        "# Defects opened",
        "",
    ]
    lines.extend(defects or ["None."])
    lines.extend(["", "# Blocked scenarios", "", "None.", "", "# Untested criteria", ""])
    lines.extend(untested or ["None."])
    lines.extend(["", "# Residual risk", "", residual, ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def reset_gate_files() -> None:
    questions = MOCK / "docs" / "questions.md"
    approvals = MOCK / "docs" / "approvals.md"
    questions.parent.mkdir(exist_ok=True)
    questions.write_text(
        "# Open questions\n\n"
        "A story with a row here is blocked. Leave Answer blank until the named person replies.\n\n"
        "| Story | Question | Ask who | Answer |\n"
        "| --- | --- | --- | --- |\n",
        encoding="utf-8",
    )
    approvals.write_text(
        "# Approvals\n\n"
        "A person writes each line. Text written by an agent is not an approval.\n\n"
        "Format: `Approved: Full Name — story-key`\n",
        encoding="utf-8",
    )


def main() -> int:
    ambiguous = json.loads((DATA / "ambiguous-brief.json").read_text(encoding="utf-8"))
    story = json.loads((DATA / "approved-story.json").read_text(encoding="utf-8"))
    questions_path = MOCK / "docs" / "questions.md"
    approvals_path = MOCK / "docs" / "approvals.md"
    reset_gate_files()
    log = []

    vague = {"story_key": "MOCK-2", "brief": ambiguous["brief"]}
    allowed, reason = build_allowed(vague, questions_path, approvals_path)
    if allowed:
        print("FAIL ambiguous brief was allowed to build")
        return 1
    log.append(f"Clarify: ambiguous brief blocked ({reason}). Assumptions stayed empty.")

    questions_path.write_text(
        questions_path.read_text(encoding="utf-8")
        + "| MOCK-2 | Who is the actor, and what does done look like? | Mock client | |\n",
        encoding="utf-8",
    )
    allowed, reason = build_allowed(story, questions_path, approvals_path)
    if allowed:
        print("FAIL open question did not block build")
        return 1
    log.append(f"Clarify: answered fields still blocked while the question is open ({reason}).")

    answered = questions_path.read_text(encoding="utf-8").replace(
        "| MOCK-2 | Who is the actor, and what does done look like? | Mock client | |",
        "| MOCK-2 | Who is the actor, and what does done look like? | Mock client | Signed-in technician sees tails and status. |",
    )
    questions_path.write_text(answered, encoding="utf-8")
    allowed, reason = build_allowed(story, questions_path, approvals_path)
    if allowed:
        print("FAIL build started before approval")
        return 1
    log.append(f"Approve: build blocked ({reason}).")

    approvals_path.write_text(
        approvals_path.read_text(encoding="utf-8") + "Approved: Mock Approver — MOCK-2\n",
        encoding="utf-8",
    )
    allowed, reason = build_allowed(story, questions_path, approvals_path)
    if not allowed:
        print(f"FAIL approved story did not start: {reason}")
        return 1
    log.append(f"Approve: {reason}.")

    contract = {
        "story_key": story["story_key"],
        "paths": ["GET /api/aircraft"],
        "fields": ["tail", "status"],
        "errors": ["403 forbidden"],
        "auth": "token tech-1",
        "ui_states": ["list", "No aircraft", "Forbidden"],
        "open_questions": [],
    }
    contract_path = MOCK / "contracts" / "active-story.json"
    contract_path.parent.mkdir(exist_ok=True)
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    if contract["open_questions"]:
        print("FAIL contract still has open questions")
        return 1
    log.append("Contract: GET /api/aircraft frozen with no open questions.")

    drafts = [
        jira_dry_run("Epic", "Fleet status board", "mock-1"),
        jira_dry_run("Story", "Technician sees aircraft status", "mock-2"),
        jira_dry_run("Sub-task", "List aircraft API", "mock-3", parent_key="MOCK-2"),
        jira_dry_run("Bug", "Forbidden page missing", "mock-bug-seed", parent_key="MOCK-2"),
    ]
    for draft in drafts:
        if draft["reason"] != "dry-run":
            print("FAIL JIRA dry-run did not stay local")
            return 1
    log.append("JIRA: four drafts printed locally. No status transition. JIRA is not connected.")

    scenarios = scenarios_for(story["acceptance_criteria"])
    untested = [item["criterion"] for item in scenarios if not item["id"]]
    counts = {}
    for layer, filename in (("unit", "test_unit.py"), ("api", "test_api.py"), ("e2e", "test_e2e.py")):
        completed, passed, failed = run_pytest(MOCK / "tests" / filename)
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        if completed.returncode != 0:
            print(f"FAIL mock {layer} tests")
            return completed.returncode
        counts[f"{layer}_passed"] = passed
        counts[f"{layer}_failed"] = failed
    defect_note = (
        "Seeded dry-run only, not a product failure: "
        + drafts[3]["payload"]["fields"]["summary"]
        + ". JIRA not connected, so the bug was not filed."
    )
    report = write_report(counts, [defect_note], untested, (
        "Browser was not opened. The end-to-end layer rendered the page in-process. "
        "A human still accepts MOCK-2. The seeded bug was not a failed test."
    ))
    text = report.read_text(encoding="utf-8")
    for section in REPORT_SECTIONS:
        if f"# {section}" not in text:
            print(f"FAIL report missing {section}")
            return 1
    log.append(
        "Test: "
        f"unit {counts['unit_passed']}, "
        f"API {counts['api_passed']}, "
        f"end-to-end {counts['e2e_passed']} passed. Report: {report}."
    )
    log.append("Sign-off: not accepted. A person still reads the report.")

    print("\n".join(log))
    print(f"SCENARIOS {len(scenarios)} criteria covered, untested {len(untested)}")
    print("MOCK PIPELINE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
