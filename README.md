# Agent Project Orchestrator

A platform-neutral pattern for running multiple long-lived AI projects through capacity-limited owner/executor pods.

It separates durable project state from ephemeral agent context:

- A coordinator assigns each active project to one primary lead/executor pair.
- The pair owns decisions and a durable working-memory record.
- Other pairs may help on bounded tasks without taking ownership.
- Every project memory is permanent and remains readable for future continuation.

This repository is not affiliated with OpenAI. The `adapters/codex` directory is one implementation; the core lifecycle is usable from any agent framework.

## Repository layout

```text
core/                 Framework-independent persistent memory tool and contract
adapters/codex/       Custom agents and a Skill for Codex
examples/             Minimal invocation examples
```

## Project memory

Each project retains one record in place:

```text
<memory-root>/
└── active/<project-id>/
    ├── manifest.json
    └── WORKING_MEMORY.md
```

`manifest.json` records ownership, start time, completion state, and any handover. `WORKING_MEMORY.md` records decisions, evidence, handoffs, and a resume brief. Project memory has no expiry, scheduler, automatic archive, or automatic deletion.

When the user explicitly completes a project, its state changes to `completed`, which frees its owner/executor pair for capacity planning. The files remain where they are.

## Use the core tool

```bash
python3 core/project_memory.py init \
  --memory-root /path/to/project-memory \
  --project-id billing-redesign \
  --project-root /path/to/billing-repo \
  --lead-id lead-1 \
  --executor-id executor-1

python3 core/project_memory.py capacity --memory-root /path/to/project-memory
python3 core/project_memory.py complete --memory-root /path/to/project-memory --project-id billing-redesign
```

## Codex adapter

Clone this repository and link each agent file plus the Skill into your Codex discovery locations. The commands below refuse to overwrite an existing file; rename or remove a prior custom role first if you intend to replace it.

```bash
mkdir -p "$HOME/.codex/agents" "$HOME/.agents/skills"
for agent in "$PWD"/adapters/codex/.codex/agents/*.toml; do
  ln -s "$agent" "$HOME/.codex/agents/"
done
ln -s "$PWD/adapters/codex/.agents/skills/project-company" "$HOME/.agents/skills/project-company"
```

Restart Codex if the agent or Skill list does not refresh. Then invoke:

```text
Use $project-company to start a project with permanent project memory.
```

The Codex adapter exposes one Sol coordinator and three generic Terra-Luna pods. Sol assigns one free pod to each project; a fourth active project must request capacity expansion instead of silently reusing an occupied pod.

## Add another framework

Keep the core ownership and memory contract unchanged. Implement an adapter that:

1. Lists active owners and chooses a free pair.
2. Initializes project memory with `core/project_memory.py`.
3. Ensures only the primary pair updates the working memory.
4. Marks a project complete only on explicit user direction, while retaining its memory in place.

## License

MIT. See [LICENSE](LICENSE).
