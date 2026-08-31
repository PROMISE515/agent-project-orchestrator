# Project-memory contract

## Ownership

Give each active project exactly one `lead_id` and one `executor_id`. The pair is the primary owner of planning, decisions, delivery coordination, and working-memory updates.

Assistants may contribute evidence or bounded work, but record them as assistance only. Do not transfer primary ownership without a written handover and an orchestrator decision.

## Required records

- `manifest.json`: project identity, project root, primary owners, lifecycle timestamps, and status.
- `WORKING_MEMORY.md`: mission, current state, decisions, evidence, handoffs, risks, and resume brief.

## Lifecycle

`active` → user explicitly marks the project `completed`.

Project memory is permanent: it has no retention period, expiry date, due notification, automatic archive, or automatic deletion. Marking a project complete releases its owners for capacity purposes but preserves `manifest.json` and `WORKING_MEMORY.md` in place. A future continuation reads that same record first and either resumes the project or records an explicit handover.
