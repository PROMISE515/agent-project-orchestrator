# Codex adapter

This adapter provides one `sol_ceo` coordinator and three generic Terra-Luna pods.

The bundled `project-company` Skill is explicitly invoked. It assigns one free pod to a new project, creates durable memory, and directs Codex to create a project-specific due-date heartbeat when automations are available.

Install the individual TOML files from `.codex/agents` into `~/.codex/agents`, and the `project-company` directory into `~/.agents/skills`. Keep the adapter directory inside this repository so its lifecycle script remains available. Do not overwrite existing custom roles without reviewing the difference first.
