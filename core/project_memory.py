#!/usr/bin/env python3
"""Create persistent project memory and track active owner capacity."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def now_utc():
    return datetime.now(timezone.utc)


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def project_id(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
        raise argparse.ArgumentTypeError("use lowercase letters, digits, and hyphens")
    return value


def memory_root(value):
    return Path(value).expanduser().resolve()


def active_root(root):
    return root / "active"


def manifest_path(root, identifier):
    return active_root(root) / identifier / "manifest.json"


def read_manifest(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"unknown project: {path.parent.name}")
    except json.JSONDecodeError as error:
        fail(f"invalid manifest at {path}: {error}")


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def active_manifests(root):
    manifests = []
    for path in sorted(active_root(root).glob("*/manifest.json")):
        manifest = read_manifest(path)
        if manifest.get("state") == "active":
            manifests.append((path, manifest))
    return manifests


def working_memory(identifier, manifest):
    return f"""# Project Memory: {identifier}

This is a persistent project record. It has no expiry date and is never moved, archived, or deleted automatically.

## Mission

Record the user goal, measurable success criteria, and explicit non-goals here.

## Primary ownership

- Lead: {manifest['lead_id']}
- Executor: {manifest['executor_id']}
- Project root: {manifest['project_root']}
- Started: {manifest['started_at']}

## Current state

Record the current phase, active work package, and blockers.

## Decisions and rationale

Append material decisions with date, owner, alternatives considered, and rationale.

## Handoffs and assistance

Record bounded help. Do not transfer primary ownership without an explicit handover.

## Evidence and validation

Record changed files, commands run, test results, sources, and known limitations.

## Resume brief

Keep a concise current instruction for the next session: what to read first, what is complete, and the next safe action.
"""


def command_init(args):
    root = args.memory_root
    active_root(root).mkdir(parents=True, exist_ok=True)
    active_dir = active_root(root) / args.project_id
    if active_dir.exists():
        fail(f"project id already exists: {args.project_id}")
    for _, manifest in active_manifests(root):
        if manifest["lead_id"] == args.lead_id or manifest["executor_id"] == args.executor_id:
            fail(f"owner is already assigned to active project {manifest['project_id']}")

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.is_dir():
        fail(f"project root is not a directory: {project_root}")
    manifest = {
        "schema_version": 2,
        "project_id": args.project_id,
        "project_root": str(project_root),
        "lead_id": args.lead_id,
        "executor_id": args.executor_id,
        "started_at": timestamp(now_utc()),
        "state": "active",
        "assisting_owners": [],
    }
    active_dir.mkdir(parents=True)
    write_json(active_dir / "manifest.json", manifest)
    (active_dir / "WORKING_MEMORY.md").write_text(working_memory(args.project_id, manifest), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def command_capacity(args):
    active = [
        {
            "project_id": manifest["project_id"],
            "lead_id": manifest["lead_id"],
            "executor_id": manifest["executor_id"],
            "working_memory": str(path.parent / "WORKING_MEMORY.md"),
        }
        for path, manifest in active_manifests(args.memory_root)
    ]
    print(json.dumps({"active_projects": active}, indent=2))


def command_complete(args):
    path = manifest_path(args.memory_root, args.project_id)
    manifest = read_manifest(path)
    if manifest.get("state") != "active":
        fail(f"project is not active: {args.project_id}")
    manifest["state"] = "completed"
    manifest["completed_at"] = timestamp(now_utc())
    write_json(path, manifest)
    print(json.dumps({
        "project_id": args.project_id,
        "state": "completed",
        "working_memory": str(path.parent / "WORKING_MEMORY.md"),
        "memory_retained": True,
    }, indent=2))


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--memory-root", type=memory_root, required=True)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", parents=[common])
    init.add_argument("--project-id", type=project_id, required=True)
    init.add_argument("--project-root", required=True)
    init.add_argument("--lead-id", required=True)
    init.add_argument("--executor-id", required=True)
    init.set_defaults(handler=command_init)

    capacity = commands.add_parser("capacity", parents=[common])
    capacity.set_defaults(handler=command_capacity)

    complete = commands.add_parser("complete", parents=[common])
    complete.add_argument("--project-id", type=project_id, required=True)
    complete.set_defaults(handler=command_complete)
    return parser


def main():
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
