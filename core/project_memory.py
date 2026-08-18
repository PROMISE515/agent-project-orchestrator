#!/usr/bin/env python3
"""Framework-neutral durable ownership and memory lifecycle for agent projects."""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def now_utc():
    return datetime.now(timezone.utc)


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def project_id(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
        raise argparse.ArgumentTypeError("use lowercase letters, digits, and hyphens")
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
    return f"""# Working Memory: {identifier}

## Mission

Record the user goal, measurable success criteria, and explicit non-goals here.

## Primary ownership

- Lead: {manifest['lead_id']}
- Executor: {manifest['executor_id']}
- Project root: {manifest['project_root']}
- Started: {manifest['started_at']}
- Archive due: {manifest['archive_due_at']}

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
    archive_root(root).mkdir(parents=True, exist_ok=True)
    active_dir = active_root(root) / args.project_id
    if active_dir.exists() or (archive_root(root) / args.project_id).exists():
        fail(f"project id already exists: {args.project_id}")
    for _, manifest in active_manifests(root):
        if manifest["lead_id"] == args.lead_id or manifest["executor_id"] == args.executor_id:
            fail(f"owner is already assigned to active project {manifest['project_id']}")

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.is_dir():
        fail(f"project root is not a directory: {project_root}")
    started = now_utc()
    manifest = {
        "schema_version": 1,
        "project_id": args.project_id,
        "project_root": str(project_root),
        "lead_id": args.lead_id,
        "executor_id": args.executor_id,
        "started_at": timestamp(started),
        "retention_days": args.retention_days,
        "archive_due_at": timestamp(started + timedelta(days=args.retention_days)),
        "state": "active",
        "archive_notice_sent_at": None,
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
            "archive_due_at": manifest["archive_due_at"],
        }
        for _, manifest in active_manifests(args.memory_root)
    ]
    print(json.dumps({"active_projects": active}, indent=2))


def command_due(args):
    current = now_utc()
    due_projects = []
    for path, manifest in active_manifests(args.memory_root):
        notified = manifest.get("archive_notice_sent_at") is not None
        if parse_timestamp(manifest["archive_due_at"]) <= current and (args.include_notified or not notified):
            due_projects.append({
                "project_id": manifest["project_id"],
                "lead_id": manifest["lead_id"],
                "executor_id": manifest["executor_id"],
                "archive_due_at": manifest["archive_due_at"],
                "working_memory": str(path.parent / "WORKING_MEMORY.md"),
            })
            if args.mark_notified and not notified:
                manifest["archive_notice_sent_at"] = timestamp(current)
                write_json(path, manifest)
    print(json.dumps({"due_projects": due_projects}, indent=2))


def command_extend(args):
    path = manifest_path(args.memory_root, args.project_id)
    manifest = read_manifest(path)
    if manifest.get("state") != "active":
        fail(f"project is not active: {args.project_id}")
    current = now_utc()
    previous_due = parse_timestamp(manifest["archive_due_at"])
    new_due = max(current, previous_due) + timedelta(days=args.days)
    manifest.setdefault("retention_extensions", []).append({
        "extended_at": timestamp(current),
        "days": args.days,
        "previous_due_at": manifest["archive_due_at"],
        "new_due_at": timestamp(new_due),
    })
    manifest["archive_due_at"] = timestamp(new_due)
    manifest["archive_notice_sent_at"] = None
    write_json(path, manifest)
    print(json.dumps(manifest, indent=2))


def command_archive(args):
    if not args.confirm:
        fail("archiving requires --confirm after the owner has been notified")
    active_dir = active_root(args.memory_root) / args.project_id
    active_manifest = active_dir / "manifest.json"
    manifest = read_manifest(active_manifest)
    if manifest.get("state") != "active":
        fail(f"project is not active: {args.project_id}")
    archive_dir = archive_root(args.memory_root) / args.project_id
    if archive_dir.exists():
        fail(f"archive already exists: {archive_dir}")

    working_file = active_dir / "WORKING_MEMORY.md"
    working_text = working_file.read_text(encoding="utf-8") if working_file.exists() else "No working memory file was found."
    archived_at = timestamp(now_utc())
    archive_dir.mkdir(parents=True)
    archive_text = f"""# Project Memory: {args.project_id}

## Archive record

- Lead: {manifest['lead_id']}
- Executor: {manifest['executor_id']}
- Original project root: {manifest['project_root']}
- Started: {manifest['started_at']}
- Retention window: {manifest['retention_days']} days
- Archive due: {manifest['archive_due_at']}
- Archived: {archived_at}

## Detailed active memory

{working_text}
"""
    (archive_dir / "PROJECT_MEMORY.md").write_text(archive_text, encoding="utf-8")
    if working_file.exists():
        shutil.copy2(working_file, archive_dir / "WORKING_MEMORY.md")
    manifest["state"] = "archived"
    manifest["archived_at"] = archived_at
    manifest["archive_path"] = str(archive_dir)
    write_json(active_manifest, manifest)
    write_json(archive_dir / "manifest.json", manifest)
    print(json.dumps({"project_id": args.project_id, "archive_path": str(archive_dir)}, indent=2))


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
    return parser


def main():
    args = build_parser().parse_args()
    if getattr(args, "retention_days", 30) < 1 or getattr(args, "days", 1) < 1:
        fail("retention and extension days must be at least 1")
    args.handler(args)


if __name__ == "__main__":
    main()
