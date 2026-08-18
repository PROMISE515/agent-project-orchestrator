# Codex adapter

This adapter provides one `sol_ceo` coordinator, three generic Terra-Luna pods, and a separate `sol_collaborator` with an on-demand `luna_diagnostician` for human-in-the-loop problem solving.

The bundled `project-company` Skill is explicitly invoked. It assigns one free pod to a new project, creates durable memory, and directs Codex to create a project-specific due-date heartbeat when automations are available.

Install the individual TOML files from `.codex/agents` into `~/.codex/agents`, and both Skill directories from `.agents/skills` into `~/.agents/skills`. Keep the adapter directory inside this repository so its lifecycle script remains available. Do not overwrite existing custom roles without reviewing the difference first.

Use `$collaborative-problem-solve` for an escalated project issue where the user should review assumptions, choose a direction, and assess the result between evidence-gathering cycles. It preserves the primary Terra-Luna pod's project ownership.
