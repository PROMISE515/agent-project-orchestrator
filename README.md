# Agent Project Orchestrator

A platform-neutral pattern for running multiple long-lived AI projects through capacity-limited owner/executor pods.

It separates durable project state from ephemeral agent context:

- A coordinator assigns each active project to one primary lead/executor pair.
- The pair owns decisions and a durable working-memory record.
- Other pairs may help on bounded tasks without taking ownership.
- A configurable retention window triggers an archive review.
- After confirmation, the working memory becomes an immutable project archive that a later run can load.

This repository is not affiliated with OpenAI. The `adapters/codex` directory is one implementation; the core lifecycle is usable from any agent framework.

## Repository layout

```text
core/                 Framework-independent project-memory lifecycle tool and contract
adapters/codex/       Custom agents and a Skill for Codex
examples/             Minimal invocation examples
```

## Core lifecycle

Each project has an active record:

```text
<memory-root>/
├── active/<project-id>/
│   ├── manifest.json
│   └── WORKING_MEMORY.md
└── archive/<project-id>/
    ├── manifest.json
    └── PROJECT_MEMORY.md
```

The `manifest.json` records ownership, start time, retention duration, archive due date, status, and extensions. `WORKING_MEMORY.md` records decisions, evidence, handoffs, and a resume brief. Do not treat an agent conversation as the only project memory.

## Use the core tool

```bash
python3 core/project_memory.py init \
  --memory-root /path/to/project-memory \
  --project-id billing-redesign \
  --project-root /path/to/billing-repo \
  --lead-id lead-1 \
  --executor-id executor-1 \
  --retention-days 30

python3 core/project_memory.py capacity --memory-root /path/to/project-memory
python3 core/project_memory.py due --memory-root /path/to/project-memory --mark-notified
python3 core/project_memory.py extend --memory-root /path/to/project-memory --project-id billing-redesign --days 14
python3 core/project_memory.py archive --memory-root /path/to/project-memory --project-id billing-redesign --confirm
```

Archive is intentionally confirmation-gated. A scheduler may notify when a project is due, but it should not archive a project without an explicit approval policy.

## Codex adapter

Clone this repository and link each agent file plus the Skill into your Codex discovery locations. The commands below refuse to overwrite an existing file; rename or remove a prior custom role first if you intend to replace it.

```bash
mkdir -p "$HOME/.codex/agents" "$HOME/.agents/skills"
for agent in "$PWD"/adapters/codex/.codex/agents/*.toml; do
  ln -s "$agent" "$HOME/.codex/agents/"
done
ln -s "$PWD/adapters/codex/.agents/skills/project-company" "$HOME/.agents/skills/project-company"
ln -s "$PWD/adapters/codex/.agents/skills/collaborative-problem-solve" "$HOME/.agents/skills/collaborative-problem-solve"
```

Restart Codex if the agent or Skill list does not refresh. Then invoke:

```text
Use $project-company to start a project with a 30-day memory window.
```

The Codex adapter exposes one Sol coordinator and three generic Terra-Luna pods. Sol assigns one free pod to each project; a fourth active project must request capacity expansion instead of silently reusing an occupied pod. It also includes `$collaborative-problem-solve`: a separate Sol-led, user-checkpointed diagnostic loop that can call a Luna investigator without taking ownership away from the project's primary pod.

## Add another framework

Keep the core ownership and memory contract unchanged. Implement an adapter that:

1. Lists active owners and chooses a free pair.
2. Initializes project memory with `core/project_memory.py`.
3. Ensures only the primary pair updates the working memory.
4. Creates a scheduled due-date notification.
5. Requires the configured approval before calling `archive`.

## License

MIT. See [LICENSE](LICENSE).
