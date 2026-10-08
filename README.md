# Office delivery agents

Four specialist agents help a team write backlog, build a story, and test it. A person still approves scope and accepts the result. Agents draft JIRA issues. They do not move an issue to Ready, Done, or Closed.

This repository is the shareable copy. On this machine the same skills are also installed under `%USERPROFILE%\.grok\skills`, and the workflow is installed at `%USERPROFILE%\.grok\workflows\office-delivery.rhai`.

## Roles

| Agent | Skill | Job |
| --- | --- | --- |
| Requirements | `office-requirements` | Turns a client note into an epic, stories, and sub-tasks. Missing or conflicting fields become questions. Assumptions stay empty. |
| Frontend | `office-frontend` | Implements one approved story from that story and the contract, and adds unit or component tests. |
| Backend | `office-backend` | Writes the contract, then implements the same story and its unit tests. |
| Automation | `office-automation` | Builds scenarios from acceptance criteria, runs the test pyramid, files defects, and writes the report. |

Shared gates live in `office-pipeline`. Required story fields live only in `ready_checklist.json`.

A story can be built only when all of these are true:

- Every field in `ready_checklist.json` is filled from the client note or an answer.
- `docs/questions.md` has no unanswered row for that story.
- `docs/approvals.md` contains a line `Approved: Full Name — story-key` written by a person.
- The story names its parent epic.

Frontend and backend read the approved story and one contract. They send product questions back to the requirements agent. The automation agent owns API and end-to-end coverage. Unit tests stay with the change that adds the behavior.

## Manager demo

The demo uses a mock fleet-status note. It does not call a model and it does not connect to JIRA. The fleet page, the approval gate, the draft tickets, and the pytest run are real.

From this folder:

```powershell
python demo\server.py
```

Open `http://127.0.0.1:8877`. If Windows refuses that port, start again with `python demo\server.py --port 8899` and use the printed address.

Click through in this order:

1. Read the client note: "The client wants a dashboard of fleet status."
2. **Ask the requirements agent.** The story stays blocked and lists the missing fields.
3. **Record the client answer.** The story is now complete and still blocked.
4. Leave the name as Alex Morgan, or type your own, then **Approve the story.** The contract and four local JIRA drafts appear.
5. Open the fleet board as **Technician**, **Empty fleet**, and **Unknown person.**
6. **Run the test pyramid.** Unit, API, and end-to-end counts come from pytest.
7. **Accept the story.** That records the approver in the demo. It does not close a JIRA issue.

**Start over** returns the demo to the vague note. Say this while you click: the note is too thin to build, the agent asks, you answer, you approve, the board matches the contract, the tests pass, and you accept.

## Checks

From this folder:

```powershell
python -m pytest tests mock-run\tests -q
python scripts\run_mock_pipeline.py
```

Pytest checks the ready-field list, the 10 ambiguous requirement cases, the JIRA draft payload, the demo walkthrough, and the fleet pyramid. The mock pipeline rehearses the gates in the terminal and writes `mock-run\reports\MOCK-1-2026-10-08.md`.

Pass means the vague note is blocked, an open question is blocked, a missing approval is blocked, the named person can approve, drafts contain no status transition, and the fleet tests pass. The story is still waiting for a person at the end of the terminal run.

The 10 cases in `evals\requirements_ambiguous.json` check that the case file is well formed. A live pass still requires one requirements-agent reply per case: at least one question, an empty assumptions list, and no acceptance criterion that invents the missing field.

## JIRA

Drafts are created only when all of these environment variables are set: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, and `JIRA_PROJECT`. The token stays in the environment. Do not commit it.

```powershell
python scripts\jira_draft.py --type Story --summary "Technician sees aircraft status" --description "Draft only" --external-id "mock-2" --dry-run
```

`--dry-run`, or a missing variable, prints the payload and exits 2. The script posts to `/rest/api/2/issue` when the variables are present. It never transitions status. A Sub-task needs `--parent-key`. Set `JIRA_EPIC_NAME_FIELD` only when that JIRA site requires an epic name.

## Workflow

`office-delivery` runs Clarify, Approve, Contract, Build, Test, and Sign-off. Pass a client `brief`. Pass `repo` when the run should reach the contract, the build, and the tests. Leave `harness_check` unset. That flag is only for the canned smoke check.

Build runs the backend agent and then the frontend agent in the same repo so the test phase can see both changes. The workflow pauses for questions, for the approval line, and for sign-off. Prove it on one epic and read that report before the next epic.

## Layout

```text
ready_checklist.json          Required story fields
.grok/skills/                 Agent charters
.grok/workflows/              office-delivery workflow
demo/                         Manager walkthrough
mock-data/                    Vague note and completed story
mock-run/                     Fleet app, tests, and sample report
scripts/jira_draft.py         Draft-only JIRA create
scripts/run_mock_pipeline.py  Terminal rehearsal
evals/                        Ambiguous requirement cases
tests/                        Kit and demo checks
docs/                         Decision, question, and approval templates
contracts/                    Contract template
```

Product repos use the same `docs/`, `contracts/`, and `reports/` names. This kit's `docs/` files are the empty templates. The mock run keeps its own copies under `mock-run/docs/`.
