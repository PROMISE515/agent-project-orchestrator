#!/usr/bin/env python3
"""Maintain durable ownership and memory for Project Company pods."""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_MEMORY_ROOT = Path.home() / ".codex" / "project-memory"
PODS = {
    "terra_lead_1": "luna_executor_1",
    "terra_lead_2": "luna_executor_2",
    "terra_lead_3": "luna_executor_3",
}


def now_utc():
    return datetime.now(timezone.utc)


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def project_id(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
        raise argparse.ArgumentTypeError(
            "project id must use lowercase letters, digits, and hyphens"
        )
    return value


def memory_root(value):
    return Path(value).expanduser().resolve()


def active_root(root):
    return root / "active"


def archive_root(root):
    return root / "archive"


def manifest_path(root, identifier):
    return active_root(root) / identifier / "manifest.json"


def read_manifest(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"unknown active project: {path.parent.name}")
    except json.JSONDecodeError as error:
        fail(f"invalid manifest at {path}: {error}")


def write_json(path, payload):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def active_manifests(root):
    result = []
    for path in sorted(active_root(root).glob("*/manifest.json")):
        manifest = read_manifest(path)
        if manifest.get("state") == "active":
            result.append((path, manifest))
    return result


def working_memory(identifier, manifest):
    return f"""# Working Memory: {identifier}

## Mission

Record the user goal, measurable success criteria, and explicit non-goals here.

## Primary ownership

- Terra lead: {manifest['primary_lead']}
- Luna executor: {manifest['primary_executor']}
- Project root: {manifest['project_root']}
- Started: {manifest['started_at']}
- Archive due: {manifest['archive_due_at']}

## Current state

Record the current phase, active work package, and blockers.

## Decisions and rationale

Append material decisions with date, owner, alternatives considered, and rationale.

## Handoffs and assistance

Record any help from another pod as bounded assistance. Do not transfer primary ownership without an explicit Sol-approved handover.

## Evidence and validation

Record changed files, commands run, test results, sources, and known limitations.

## Resume brief

Keep a concise, current instruction for the next session: what to read first, what is complete, and the next safe action.
"""


def command_init(args):
    root = args.memory_root
    root.mkdir(parents=True, exist_ok=True)
    active_root(root).mkdir(exist_ok=True)
    archive_root(root).mkdir(exist_ok=True)

    if PODS.get(args.lead) != args.executor:
        fail("lead and executor must be one of the defined Terra-Luna pods")

    project_dir = active_root(root) / args.project_id
    if project_dir.exists() or (archive_root(root) / args.project_id).exists():
        fail(f"project id already exists: {args.project_id}")

    for _, manifest in active_manifests(root):
        if manifest.get("primary_lead") == args.lead:
            fail(
                f"{args.lead} already owns active project "
                f"{manifest.get('project_id')}"
            )

    root_path = Path(args.project_root).expanduser().resolve()
    if not root_path.is_dir():
        fail(f"project root does not exist or is not a directory: {root_path}")

    started = now_utc()
    manifest = {
        "schema_version": 1,
        "project_id": args.project_id,
        "project_root": str(root_path),
        "primary_lead": args.lead,
        "primary_executor": args.executor,
        "started_at": timestamp(started),
        "retention_days": args.retention_days,
        "archive_due_at": timestamp(started + timedelta(days=args.retention_days)),
        "state": "active",
        "archive_notice_sent_at": None,
        "assisting_pods": [],
    }

    project_dir.mkdir(parents=True)
    write_json(project_dir / "manifest.json", manifest)
    (project_dir / "WORKING_MEMORY.md").write_text(
        working_memory(args.project_id, manifest), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


def command_capacity(args):
    owners = {}
    for _, manifest in active_manifests(args.memory_root):
        owners[manifest["primary_lead"]] = {
            "project_id": manifest["project_id"],
            "executor": manifest["primary_executor"],
            "archive_due_at": manifest["archive_due_at"],
        }
    payload = {
        "available": [lead for lead in PODS if lead not in owners],
        "active": owners,
    }
    print(json.dumps(payload, indent=2))


def command_due(args):
    current_time = now_utc()
    due_projects = []
    for path, manifest in active_manifests(args.memory_root):
        is_due = parse_timestamp(manifest["archive_due_at"]) <= current_time
        notified = manifest.get("archive_notice_sent_at") is not None
        if is_due and (args.include_notified or not notified):
            due_projects.append(
                {
                    "project_id": manifest["project_id"],
                    "primary_lead": manifest["primary_lead"],
                    "primary_executor": manifest["primary_executor"],
                    "archive_due_at": manifest["archive_due_at"],
                    "working_memory": str(path.parent / "WORKING_MEMORY.md"),
                }
            )
            if args.mark_notified and not notified:
                manifest["archive_notice_sent_at"] = timestamp(current_time)
                write_json(path, manifest)
    print(json.dumps({"due_projects": due_projects}, indent=2))


def command_extend(args):
    manifest_file = manifest_path(args.memory_root, args.project_id)
    manifest = read_manifest(manifest_file)
    if manifest.get("state") != "active":
        fail(f"project is not active: {args.project_id}")

    current_time = now_utc()
    previous_due = parse_timestamp(manifest["archive_due_at"])
    next_due = max(current_time, previous_due) + timedelta(days=args.days)
    manifest.setdefault("retention_extensions", []).append(
        {
            "extended_at": timestamp(current_time),
            "days": args.days,
            "previous_due_at": manifest["archive_due_at"],
            "new_due_at": timestamp(next_due),
        }
    )
    manifest["archive_due_at"] = timestamp(next_due)
    manifest["archive_notice_sent_at"] = None
    write_json(manifest_file, manifest)
    print(json.dumps(manifest, indent=2))


def command_archive(args):
    if not args.confirm:
        fail("archiving requires --confirm after the user has been notified")

    active_dir = active_root(args.memory_root) / args.project_id
    manifest_file = active_dir / "manifest.json"
    manifest = read_manifest(manifest_file)
    if manifest.get("state") != "active":
        fail(f"project is not active: {args.project_id}")

    archive_dir = archive_root(args.memory_root) / args.project_id
    if archive_dir.exists():
        fail(f"archive already exists: {archive_dir}")

    source_memory = active_dir / "WORKING_MEMORY.md"
    working_text = source_memory.read_text(encoding="utf-8") if source_memory.exists() else "No working memory file was found."
    archived_at = timestamp(now_utc())
    archive_dir.mkdir(parents=True)
    archive_memory = f"""# Project Memory: {args.project_id}

## Archive record

- Primary Terra lead: {manifest['primary_lead']}
- Primary Luna executor: {manifest['primary_executor']}
- Original project root: {manifest['project_root']}
- Started: {manifest['started_at']}
- Retention window: {manifest['retention_days']} days
- Archive due: {manifest['archive_due_at']}
- Archived: {archived_at}

## Detailed active memory

{working_text}
"""
    (archive_dir / "PROJECT_MEMORY.md").write_text(archive_memory, encoding="utf-8")
    shutil.copy2(manifest_file, archive_dir / "manifest.json")
    if source_memory.exists():
        shutil.copy2(source_memory, archive_dir / "WORKING_MEMORY.md")

    manifest["state"] = "archived"
    manifest["archived_at"] = archived_at
    manifest["archive_path"] = str(archive_dir)
    write_json(manifest_file, manifest)
    write_json(archive_dir / "manifest.json", manifest)
    print(json.dumps({"project_id": args.project_id, "archive_path": str(archive_dir)}, indent=2))


def parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--memory-root", type=memory_root, default=DEFAULT_MEMORY_ROOT,
        help="global root for active project memory and archived project memory",
    )

    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", parents=[common])
    init.add_argument("--project-id", type=project_id, required=True)
    init.add_argument("--project-root", required=True)
    init.add_argument("--lead", choices=sorted(PODS), required=True)
    init.add_argument("--executor", choices=sorted(PODS.values()), required=True)
    init.add_argument("--retention-days", type=int, default=30)
    init.set_defaults(handler=command_init)

    capacity = commands.add_parser("capacity", parents=[common])
    capacity.set_defaults(handler=command_capacity)

    due = commands.add_parser("due", parents=[common])
    due.add_argument("--mark-notified", action="store_true")
    due.add_argument("--include-notified", action="store_true")
    due.set_defaults(handler=command_due)

    extend = commands.add_parser("extend", parents=[common])
    extend.add_argument("--project-id", type=project_id, required=True)
    extend.add_argument("--days", type=int, required=True)
    extend.set_defaults(handler=command_extend)

    archive = commands.add_parser("archive", parents=[common])
    archive.add_argument("--project-id", type=project_id, required=True)
    archive.add_argument("--confirm", action="store_true")
    archive.set_defaults(handler=command_archive)
    return root


def main():
    args = parser().parse_args()
    if getattr(args, "retention_days", 30) < 1:
        fail("retention days must be at least 1")
    if getattr(args, "days", 1) < 1:
        fail("extension days must be at least 1")
    args.handler(args)


if __name__ == "__main__":
    main()
