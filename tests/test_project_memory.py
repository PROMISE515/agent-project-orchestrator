"""End-to-end coverage for the persistent project-memory CLI."""

import json
import subprocess
import sys
import tempfile
import unittest
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

    def initialize(self, identifier="billing-redesign", lead="terra-1", executor="luna-1"):
        return json.loads(self.run_tool(
            "init", "--memory-root", str(self.memory_root), "--project-id", identifier,
            "--project-root", str(self.project_root), "--lead-id", lead, "--executor-id", executor,
        ).stdout)

    def test_memory_is_persistent_and_completion_releases_capacity(self):
        created = self.initialize()
        self.assertEqual(created["state"], "active")
        self.assertNotIn("archive_due_at", created)
        memory_file = self.memory_root / "active" / "billing-redesign" / "WORKING_MEMORY.md"
        self.assertIn("no expiry date", memory_file.read_text(encoding="utf-8"))

        capacity = json.loads(self.run_tool("capacity", "--memory-root", str(self.memory_root)).stdout)
        self.assertEqual([item["project_id"] for item in capacity["active_projects"]], ["billing-redesign"])

        completed = json.loads(self.run_tool(
            "complete", "--memory-root", str(self.memory_root), "--project-id", "billing-redesign"
        ).stdout)
        self.assertTrue(completed["memory_retained"])
        self.assertTrue(memory_file.is_file())
        self.assertEqual(
            json.loads(self.run_tool("capacity", "--memory-root", str(self.memory_root)).stdout)["active_projects"], []
        )

        replacement = self.initialize("next-project", "terra-1", "luna-1")
        self.assertEqual(replacement["project_id"], "next-project")

    def test_cannot_reuse_active_owner_or_project_id(self):
        self.initialize()
        self.initialize("second-project", "terra-2", "luna-2")
        self.run_tool(
            "init", "--memory-root", str(self.memory_root), "--project-id", "third-project",
            "--project-root", str(self.project_root), "--lead-id", "terra-1", "--executor-id", "luna-3",
            expected_returncode=2,
        )
        self.run_tool(
            "init", "--memory-root", str(self.memory_root), "--project-id", "billing-redesign",
            "--project-root", str(self.project_root), "--lead-id", "terra-3", "--executor-id", "luna-3",
            expected_returncode=2,
        )


if __name__ == "__main__":
    unittest.main()
