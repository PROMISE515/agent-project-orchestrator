"""End-to-end coverage for the framework-neutral lifecycle CLI."""

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
TOOL = REPOSITORY / "core" / "project_memory.py"


class ProjectMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.memory_root = self.base / "memory"
        self.project_root = self.base / "workspace"
        self.project_root.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_tool(self, *arguments, expected_returncode=0):
        result = subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected_returncode, result.stderr)
        return result

    def initialize(self, identifier="billing-redesign", lead="terra-1", executor="luna-1", expected_returncode=0):
        return self.run_tool(
            "init",
            "--memory-root",
            str(self.memory_root),
            "--project-id",
            identifier,
            "--project-root",
            str(self.project_root),
            "--lead-id",
            lead,
            "--executor-id",
            executor,
            "--retention-days",
            "30",
            expected_returncode=expected_returncode,
        )

    def test_init_capacity_extend_and_archive(self):
        manifest = json.loads(self.initialize().stdout)
        self.assertEqual(manifest["state"], "active")

        capacity = json.loads(self.run_tool("capacity", "--memory-root", str(self.memory_root)).stdout)
        self.assertEqual(capacity["active_projects"][0]["lead_id"], "terra-1")

        self.initialize("another-project", expected_returncode=2)

        extended = json.loads(
            self.run_tool(
                "extend",
                "--memory-root",
                str(self.memory_root),
                "--project-id",
                "billing-redesign",
                "--days",
                "14",
            ).stdout
        )
        self.assertEqual(extended["retention_extensions"][0]["days"], 14)

        self.run_tool(
            "archive",
            "--memory-root",
            str(self.memory_root),
            "--project-id",
            "billing-redesign",
            expected_returncode=2,
        )
        archive = json.loads(
            self.run_tool(
                "archive",
                "--memory-root",
                str(self.memory_root),
                "--project-id",
                "billing-redesign",
                "--confirm",
            ).stdout
        )
        self.assertTrue(Path(archive["archive_path"]).joinpath("PROJECT_MEMORY.md").is_file())

    def test_due_marks_notice_once(self):
        self.initialize()
        manifest_file = self.memory_root / "active" / "billing-redesign" / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest["archive_due_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        first_due = json.loads(
            self.run_tool("due", "--memory-root", str(self.memory_root), "--mark-notified").stdout
        )
        self.assertEqual([item["project_id"] for item in first_due["due_projects"]], ["billing-redesign"])
        second_due = json.loads(self.run_tool("due", "--memory-root", str(self.memory_root)).stdout)
        self.assertEqual(second_due["due_projects"], [])


if __name__ == "__main__":
    unittest.main()
