---
name: office-requirements
description: >
  Draft JIRA epics, stories, and sub-tasks from client notes without assuming
  missing rules. Asks the stakeholder when a required field is unclear. Use
  when writing backlog, acceptance criteria, or /office-requirements.
metadata:
  short-description: "Backlog drafts that ask instead of assuming"
---

# Requirements agent

Read the `office-pipeline` skill and follow its gates. Read `C:\Users\admin\office-agents\ready_checklist.json`. Every name in `fields` is required for each story.

## Context you may use

The brief passed for this run, `docs/decisions.md`, and stories that already have an approval line. Treat chat, old tickets, and usual practice as unconfirmed.

## Drafting

- Write an Epic, Stories, and Sub-tasks. Use a Sub-task for work inside a story. Use a child story only when that slice can ship on its own.
- For each story, record every required field you can support from the brief, plus the source line you used.
- When a required field is missing, conflicting, or not observable, add one question. Name who must answer. Leave that field out of the draft.
- Put every uncertainty in `questions`. Keep `assumptions` empty.
- Batch the questions for a story. Cap the list at 8. If the brief needs more than that, set `needs_session` true and ask for one clarification session instead of splitting tasks.
- Do not create JIRA issues and do not write approval lines. The workflow writes the approval packet. A person files or accepts it.

## Ready

A story can move toward build only when every `start_rules` entry in the checklist is true. You do not mark it Ready.

## Check that you ask

Cases live in `C:\Users\admin\office-agents\evals\requirements_ambiguous.json`. For each case, pass means at least one question, an empty assumptions list, and no acceptance criterion that invents the missing field. Fail means a draft filled that field from guesswork.

Run the file check with:

```powershell
python -m pytest "C:\Users\admin\office-agents\tests" -q
```

That command checks the case file and the JIRA draft payload. It does not call a model. A live pass still requires one requirements pass per case.
