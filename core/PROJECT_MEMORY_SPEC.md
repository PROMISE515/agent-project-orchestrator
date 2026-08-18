# Project-memory contract

## Ownership

Give each active project exactly one `lead_id` and one `executor_id`. The pair is the primary owner of planning, decisions, delivery coordination, and working-memory updates.

Assistants may contribute evidence or bounded work, but record them as assistance only. Do not transfer primary ownership without a written handover and an orchestrator decision.

## Required records

- `manifest.json`: project identity, project root, primary owners, lifecycle timestamps, and status.
- `WORKING_MEMORY.md`: mission, current state, decisions, evidence, handoffs, risks, and resume brief.
- `PROJECT_MEMORY.md`: archived, detailed snapshot generated from the active record after confirmation.

## Lifecycle

`active` → due notification → user confirms archive or extends retention → `archived`.

Schedulers may mark a due notification as sent, but must not call the confirmation-gated archive command by themselves. A later continuation reads `PROJECT_MEMORY.md` first and starts a new active record or an explicit handover.
