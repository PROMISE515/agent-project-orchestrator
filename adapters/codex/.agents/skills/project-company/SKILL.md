---
name: project-company
description: "Launch and operate substantial projects through capacity-limited Terra-Luna pods directed by a Sol CEO, with one permanent primary memory per project. Use only when the user explicitly invokes $project-company or asks to activate this project-company workflow; do not use for small, isolated changes."
---

# Project Company

Run projects as a portfolio of three generic Terra-Luna pods, not fixed functional departments. The project memory stored under `~/.codex/project-memory` is the durable source of truth; never rely on an agent thread as the only memory.

## Start a project

1. Ask for a project id.
2. Have `sol_ceo` run `scripts/project_memory.py capacity` and choose one free permanent pod:
   - `terra_lead_1` with `luna_executor_1`
   - `terra_lead_2` with `luna_executor_2`
   - `terra_lead_3` with `luna_executor_3`
3. If no pod is free, have Sol tell the user that capacity is exhausted and request approval to provision the next Terra-Luna pair. Do not silently assign a busy pod as another project's primary owner.
4. Initialize the project with `scripts/project_memory.py init`, using the selected pair and the current project root.
5. Have the Terra lead create the charter and keep `WORKING_MEMORY.md` current. Its paired Luna executor performs bounded research, implementation, and verification. The pair remains accountable until Sol records an approved handover or the user explicitly marks the project complete.

## Collaboration rules

- Other pods may assist only through a narrow, explicit task. Record the assistance in `WORKING_MEMORY.md`; assistants never take primary memory or decision ownership.
- Do not run concurrent writes against the same files or mutable resource.
- Ask Sol to resolve priority conflicts, handovers, scope changes, and work that exceeds a Luna executor's bounded task.
- At each meaningful decision, phase change, risk discovery, or verified delivery, update `WORKING_MEMORY.md` with the decision, rationale, evidence, current state, and a resume brief.

## Permanent project memory

Project memory has no countdown, retention period, expiry date, scheduled check, automatic archive, or automatic deletion. Do not create an automation for project memory management.

When the user explicitly says a project is complete, run `scripts/project_memory.py complete --project-id <id>`. This only changes the project state so its pod can accept another project; `manifest.json` and `WORKING_MEMORY.md` remain in their existing directory for future continuation.
