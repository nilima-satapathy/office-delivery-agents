---
name: office-frontend
description: >
  Implement one approved story in the frontend from the story and the shared
  contract. Use when building UI for an approved office-delivery story or
  /office-frontend.
metadata:
  short-description: "Frontend work from an approved story"
---

# Frontend agent

Read the `office-pipeline` skill and follow its gates.

## Start

Apply the office-pipeline gates. Then read the approved story and `contracts/<story>.json`. Follow the product repo's UI stack and existing components.

## Build

- Implement only that story.
- Use the contract's paths, fields, errors, and UI states.
- When a label, empty state, error state, or permission is absent from the story and the contract, add a question for the requirements agent and stop. Do not take the missing rule from backend notes.
- Leave the contract unchanged. A contract change goes back through the requirements agent and a new approval.
- Add unit or component tests for the behavior you add.
- Tell the automation agent the routes, the page object, and the states to cover. Put selectors in the page object.

## Finish

Do not mark the story done. Report files changed and tests you added.
