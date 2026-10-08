---
name: office-automation
description: >
  Generate test scenarios from an epic, run the testing pyramid, file JIRA
  defects, and write the test report. Use when testing an office-delivery
  story or /office-automation.
metadata:
  short-description: "Pyramid tests, defects, and the report"
---

# Automation agent

Read the `office-pipeline` skill and follow its gates.

## Scenarios

Read one epic's approved stories and their acceptance criteria. Write one scenario per criterion. Tag each scenario with the criterion. A criterion with no scenario stays in the report under untested criteria.

## Pyramid

| Layer | Owner | What this run includes |
| --- | --- | --- |
| Unit | Frontend and backend, with the human author | Run the unit tests those agents added. Do not replace them with UI tests. |
| API / integration | This agent | One check for each criterion that crosses a service boundary |
| End-to-end | This agent | The few browser paths that prove the story. Use the page object. |

Run deterministic checks first. Use an AI judge only when the expected result is language, and only against a golden set the repo already has.

## Defects

A failed test becomes a Bug linked to the story and epic. Include steps, expected, actual, severity, and evidence. File it with `C:\Users\admin\office-agents\scripts\jira_draft.py --type Bug`. When that script reports JIRA is not connected, append the same block to `reports/defects.md`. Do not close bugs.

## Report

Write `reports/<epic>-<date>.md` with these sections, in order:

1. Epic
2. Counts by layer (unit, API, end-to-end) and pass/fail
3. Defects opened
4. Blocked scenarios
5. Untested criteria
6. Residual risk

The story stays unaccepted while a failed test has no explanation or a high-severity bug is still open.
