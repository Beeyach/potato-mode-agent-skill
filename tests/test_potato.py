from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "potato-mode" / "scripts" / "potato.py"
SPEC = importlib.util.spec_from_file_location("potato", SCRIPT)
assert SPEC and SPEC.loader
potato = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(potato)


class ClassificationTests(unittest.TestCase):
    def test_low_memory_is_critical(self):
        tier, workers, reasons = potato.classify(1024 * potato.MIB, 50_000 * potato.MIB, 8, 0.1)
        self.assertEqual((tier, workers), ("critical", 1))
        self.assertTrue(any("memory" in reason for reason in reasons))

    def test_low_disk_is_critical(self):
        tier, workers, _ = potato.classify(16_000 * potato.MIB, 1024 * potato.MIB, 8, 0.1)
        self.assertEqual((tier, workers), ("critical", 1))

    def test_two_cpus_are_constrained(self):
        tier, workers, _ = potato.classify(16_000 * potato.MIB, 50_000 * potato.MIB, 2, None)
        self.assertEqual((tier, workers), ("constrained", 1))

    def test_moderate_memory_is_balanced(self):
        tier, workers, _ = potato.classify(6000 * potato.MIB, 50_000 * potato.MIB, 8, 0.1)
        self.assertEqual((tier, workers), ("balanced", 2))

    def test_roomy_caps_workers(self):
        tier, workers, _ = potato.classify(16_000 * potato.MIB, 50_000 * potato.MIB, 32, 0.1)
        self.assertEqual((tier, workers), ("roomy", 4))

    def test_high_load_is_critical(self):
        tier, workers, _ = potato.classify(16_000 * potato.MIB, 50_000 * potato.MIB, 4, 4.0)
        self.assertEqual((tier, workers), ("critical", 1))


class CliTests(unittest.TestCase):
    def test_json_probe_has_stable_fields(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "probe", "--path", str(ROOT), "--json"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn('"schema_version": 1', completed.stdout)
        self.assertIn('"worker_limit"', completed.stdout)
        self.assertIn('"tier"', completed.stdout)

    def test_run_limits_environment(self):
        code = "import os; print(os.environ['GOMAXPROCS']); print(os.environ['CARGO_BUILD_JOBS'])"
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "run", "--path", str(ROOT), "--", sys.executable, "-c", code],
            text=True,
            capture_output=True,
            check=True,
            env={**os.environ, "GOMAXPROCS": "999"},
        )
        lines = completed.stdout.strip().splitlines()
        self.assertEqual(lines[0], lines[1])
        self.assertNotEqual(lines[0], "999")

    def test_run_returns_child_status(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "run", "--path", str(ROOT), "--", sys.executable, "-c", "raise SystemExit(7)"],
            check=False,
        )
        self.assertEqual(completed.returncode, 7)


class InstallerTests(unittest.TestCase):
    def test_project_install_for_both_clients(self):
        with tempfile.TemporaryDirectory() as temp:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "install.py"), "--target", "both", "--scope", "project", "--project", temp],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue((Path(temp) / ".claude/skills/potato-mode/SKILL.md").is_file())
            self.assertTrue((Path(temp) / ".agents/skills/potato-mode/SKILL.md").is_file())
            self.assertIn("Installed for claude", completed.stdout)
            self.assertIn("Installed for codex", completed.stdout)

    def test_installer_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, str(ROOT / "install.py"), "--target", "codex", "--scope", "project", "--project", temp]
            subprocess.run(command, check=True, capture_output=True)
            completed = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("already exists", completed.stderr)

    def test_skill_metadata_is_packaged(self):
        skill = ROOT / "skill" / "potato-mode"
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("name: potato-mode", text)
        self.assertIn('$potato-mode', metadata)


if __name__ == "__main__":
    unittest.main()
