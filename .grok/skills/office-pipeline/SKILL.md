---
name: office-pipeline
description: >
  Shared gates for the office delivery agents. Use when coordinating the
  requirements, frontend, backend, and automation agents, approving a JIRA
  story, or running the office delivery pipeline. Use with /office-delivery.
metadata:
  short-description: "Gates for the four office agents"
---

# Office pipeline

Four roles share one approved story. The requirements agent owns client intent. Frontend and backend read that story and one contract. The automation agent owns API tests, end-to-end tests, defects, and the test report. Frontend and backend write the unit tests for the change they make.

## Files

Use the product repo when the workflow is given `repo`. Otherwise use `C:\Users\admin\office-agents`.

- `docs/decisions.md` — confirmed stakeholder decisions
- `docs/questions.md` — an open row blocks that story
- `docs/approvals.md` — human approval lines
- `contracts/<story>.json` — paths, fields, errors, auth, UI states
- `reports/<epic>-<date>.md` — test report

Required story fields live only in `C:\Users\admin\office-agents\ready_checklist.json`.

## Gates

- Create JIRA issues as drafts. A person moves Ready, Done, and Closed.
- Build starts only when that story has no open question and `docs/approvals.md` contains `Approved: Full Name — story-key`.
- Wording produced by an agent is not approval.
- Do not merge, deploy, or email the client.
- Keep tokens and client secrets out of prompts and repo files.

## JIRA

When `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, and `JIRA_PROJECT` are all set, create a draft with:

```powershell
python "C:\Users\admin\office-agents\scripts\jira_draft.py" --type Story --summary "..." --description "..." --external-id "story-summary-slug"
```

If any variable is missing, say JIRA is not connected and leave the draft in the approval packet. The script creates issues. It does not transition them. Epic Name is site-specific: set `JIRA_EPIC_NAME_FIELD` only when the site requires it.

## Workflow

Run the `office-delivery` workflow with `brief` and, once a story is approved, `repo`. Do not set `harness_check`. That flag is only for the automated smoke check.

Prove the pipeline on one epic. Read that epic's test report before starting the next epic.
