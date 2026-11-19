"""Unit tests for the bounded, deterministic parts of Engineering Guardian."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/engineering-guardian/scripts"))
sys.path.insert(0, str(ROOT / "tools"))
from check_repo import audit, screen_line
from review_diff import rank_files, changed_paths
from validate_skill import validate
from refresh_sources import digest, normalize_text, source_is_safe, update_snapshots, validate_registry


class ManifestTests(unittest.TestCase):
    def test_current_skill_is_valid(self):
        self.assertEqual(validate(ROOT / "skills/engineering-guardian"), [])

    def test_missing_manifest_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(any("Missing required" in x for x in validate(Path(temp))))


class AuditTests(unittest.TestCase):
    def test_detects_secret_assignment(self):
        line = 'api_' + 'key = "RandomSecretValueAbcdefGhijk"'
        self.assertTrue(any(x["rule"] == "hardcoded-credential" for x in screen_line(line, "src/config.py", 1)))

    def test_detects_unsafe_dynamic_execution(self):
        line = 'result = ev' + 'al(user_expression)'
        self.assertTrue(any(x["rule"] == "dynamic-execution" for x in screen_line(line, "src/run.py", 7)))

    def test_environment_variable_is_not_secret_literal(self):
        self.assertFalse(screen_line('api_key = os.environ["API_KEY"]', "src/config.py", 1))

    def test_detects_shell_true(self):
        line = "subprocess.run(cmd, shell" + "=True)"
        self.assertTrue(any(x["rule"] == "shell-execution" for x in screen_line(line, "src/a.py", 2)))

    def test_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "node_modules").mkdir()
            (project / "node_modules" / "x.py").write_text('pass' + 'word = "abcde1234567"')
            (project / "main.py").write_text("print('ok')")
            result = audit(project)
            self.assertEqual(result["stats"]["scanned_files"], 1)
            self.assertEqual(result["issues"], [])


class DiffTests(unittest.TestCase):
    def test_deleted_policy_is_reviewed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            def git(*args):
                return subprocess.run(["git", "-C", temp, *args], check=True, capture_output=True)
            git("init")
            git("config", "user.name", "Guardian Test")
            git("config", "user.email", "test@example.invalid")
            (repo / "AGENTS.md").write_text("policy")
            git("add", ".")
            git("commit", "-m", "baseline")
            (repo / "AGENTS.md").unlink()
            git("add", "-u")
            git("commit", "-m", "remove policy")
            self.assertEqual(changed_paths(repo, "HEAD~1", "HEAD"), ["AGENTS.md"])
            self.assertEqual(rank_files(["AGENTS.md"])[0]["risk"], "HIGH")

    def test_sensitive_changes_are_high_risk(self):
        files = rank_files(["src/auth/session.py", "docs/README.md", ".github/workflows/ci.yml"])
        self.assertEqual([f["risk"] for f in files], ["HIGH", "LOW", "HIGH"])


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.registry = {"schema": 1, "sources": [{"id": "official-docs", "url": "https://developers.openai.com/api/docs/guides/tools-skills", "topic": "skills"}]}
        self.empty = {"schema": 1, "sources": {}}

    def test_only_approved_https_hosts(self):
        self.assertTrue(source_is_safe("https://docs.github.com/en/actions"))
        self.assertFalse(source_is_safe("https://docs.github.com.evil.invalid/x"))
        self.assertFalse(source_is_safe("http://docs.github.com/en/actions"))

    def test_digest_stable_after_html_normalization(self):
        a = normalize_text(b"<html><script>bad()</script><body>Hello  world</body></html>")
        b = normalize_text(b"<html><body>Hello world</body></html>")
        self.assertEqual(digest(a), digest(b))

    def test_updater_marks_baseline_then_no_change(self):
        getter = lambda url: "Stable official content"
        next_lock, change = update_snapshots(self.registry, self.empty, getter=getter, today="2026-11-18")
        self.assertEqual(change[0]["status"], "baseline")
        self.assertEqual(validate_registry(self.registry, next_lock), [])
        later, change2 = update_snapshots(self.registry, next_lock, getter=getter, today="2026-11-19")
        self.assertEqual(change2, [])
        self.assertEqual(later, next_lock)

    def test_fetch_failure_retains_prior_snapshot(self):
        lock, _ = update_snapshots(self.registry, self.empty, getter=lambda u: "Stable content", today="2026-11-18")
        def fail(url):
            raise TimeoutError("unavailable")
        new_lock, events = update_snapshots(self.registry, lock, getter=fail, today="2026-11-19")
        self.assertEqual(new_lock, lock)
        self.assertEqual(events[0]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
