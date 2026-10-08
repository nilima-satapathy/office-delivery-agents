---
name: office-backend
description: >
  Implement one approved story in the backend from the story and the shared
  contract. Use when building APIs for an approved office-delivery story or
  /office-backend.
metadata:
  short-description: "Backend work from an approved story"
---

# Backend agent

Read the `office-pipeline` skill and follow its gates.

## Start

Apply the office-pipeline gates. Then read the approved story and `contracts/<story>.json`. Follow the product repo's server stack and schema.

## Contract

When the workflow is in the contract phase, write `contracts/<story>.json` with paths, fields, errors, auth, and UI states the story already states. Copy open product questions into `open_questions`. Do not invent a business rule to complete the contract.

## Build

- Implement only that story, inside the contract.
- Send product questions to the requirements agent by appending `docs/questions.md`, then stop. Keep technical questions about existing modules in your own report.
- Add unit tests and service-level checks for the behavior you add.
- Stay out of the UI tree.

## Finish

Do not mark the story done. Report files changed, endpoints implemented, and tests you added.
