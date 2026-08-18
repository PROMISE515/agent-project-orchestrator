---
name: project-company
description: "Launch and operate substantial projects through capacity-limited Terra-Luna pods directed by a Sol CEO, with one durable primary memory per project and a configurable archive countdown. Use only when the user explicitly invokes $project-company or asks to activate this project-company workflow; do not use for small, isolated changes."
---

# Project Company

Run projects as a portfolio of three generic Terra-Luna pods, not fixed functional departments. The active project memory stored under `~/.codex/project-memory` is the durable source of truth; never rely on an agent thread as the only memory.

## Start a project

1. Ask for a project id and retention period. Default to 30 days when the user does not specify one.
2. Have `sol_ceo` run `scripts/project_memory.py capacity` and choose one free permanent pod:
   - `terra_lead_1` with `luna_executor_1`
   - `terra_lead_2` with `luna_executor_2`
   - `terra_lead_3` with `luna_executor_3`
3. If no pod is free, have Sol tell the user that capacity is exhausted and request approval to provision the next Terra-Luna pair. Do not silently assign a busy pod as another project's primary owner.
4. Initialize the project with `scripts/project_memory.py init`, using the selected pair, the current project root, and the approved retention period.
5. Have the Terra lead create the charter and keep `WORKING_MEMORY.md` current. Its paired Luna executor performs bounded research, implementation, and verification. The pair remains accountable until the project is archived or Sol records an approved handover.

## Collaboration rules

- Other pods may assist only through a narrow, explicit task. Record the assistance in `WORKING_MEMORY.md`; assistants never take primary memory or decision ownership.
- Do not run concurrent writes against the same files or mutable resource.
- Ask Sol to resolve priority conflicts, handovers, scope changes, and work that exceeds a Luna executor's bounded task.
- At each meaningful decision, phase change, risk discovery, or verified delivery, update `WORKING_MEMORY.md` with the decision, rationale, evidence, current state, and a resume brief.

## Archive countdown and memory pool

At initialization, record `archive_due_at` in the manifest using the configured retention period. Create one project-specific heartbeat automation when the automation tool is available:

- Run daily against that project's memory root.
- Call `scripts/project_memory.py due --mark-notified`.
- If the project is due, tell the user that its active-memory window has ended, give the project id and archive path, and ask whether to archive or extend the retention period. For an extension, run `scripts/project_memory.py extend --project-id <id> --days <n>`.
- Never archive solely because the timer expired. Archive only after user confirmation, then run `scripts/project_memory.py archive --project-id <id> --confirm`.

The archive command preserves the active files and writes the detailed `PROJECT_MEMORY.md` into `~/.codex/project-memory/archive/<project-id>/`. For future continuation, read that archive first, then initialize a new active project record or an explicitly approved handover.

If automations are unavailable, state the exact due date in the project charter and ask the user to create a reminder; do not claim that the countdown is being monitored.
