---
name: collaborative-problem-solve
description: "Run a human-in-the-loop, evidence-driven loop for a difficult project problem, with Sol as the collaboration lead and on-demand Luna diagnostic subagents. Use only when the user explicitly invokes $collaborative-problem-solve or asks to start a collaborative Sol-Luna problem-solving loop; do not use for simple questions or routine implementation."
---

# Collaborative Problem Solve

Use `sol_collaborator` as the primary agent. It owns the problem-solving process but does not replace the existing project's primary Terra owner. Use `luna_diagnostician` only for bounded evidence work that changes the decision.

## Run one decision cycle

1. Read the relevant project memory when it exists. State the problem, desired outcome, constraints, known facts, assumptions, and highest-value unknowns. Ask only essential clarifying questions.
2. Gather safe direct evidence. Delegate at most two independent, narrow questions to `luna_diagnostician` when reproduction, source checking, or an adversarial view materially reduces uncertainty.
3. Present a decision checkpoint with two or three options: recommendation, evidence, confidence, risk, reversibility, expected signal, and the smallest next test.
4. Await the user's direction before a destructive, externally visible, costly, or scope-expanding step. Do not stop for routine read-only investigation or a clearly reversible test within the agreed scope.
5. Run or guide the approved test. Compare the actual outcome with the expected signal. If they differ, revise the assumptions and begin the next decision cycle.
6. At resolution, summarize the conclusion, evidence, remaining uncertainty, and follow-up monitoring. Have the primary Terra record material decisions, rejected hypotheses, evidence, and a resume brief in `WORKING_MEMORY.md`. Without an active project, create a separate issue record only after the user approves tracking it.

## Preserve ownership and token budget

- The project Terra-Luna pod remains primary owner. Sol is the escalation and collaboration lead for this issue; Luna agents are temporary assistants.
- Do not delegate a simple lookup, summary, or mechanical task. Keep every Luna request to one question and require a compact evidence report.
- Do not ask the user to reconfirm settled constraints. Avoid status-only messages and autonomous background loops.
- Never turn a hypothesis into a conclusion without evidence or a stated uncertainty level.
