"""End-to-end tests for scripts/relay.py (stdlib unittest, no dependencies)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "relay.py"


def find_bash():
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    cands = [Path(git).resolve().parent.parent / "bin" / "bash.exe"] if git else []
    cands.append(Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe")
    return next((str(c) for c in cands if c.is_file()), None)


BASH = find_bash()


class RelayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.proj = self.tmp / "proj"
        self.proj.mkdir()
        self.env = dict(os.environ, JOURNAL_GLOBAL_DIR=str(self.tmp / "journal"),
                        CLAUDE_ECOSYSTEM_FILE=str(self.tmp / "eco.json"), PYTHONIOENCODING="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_r(self, *args, stdin="", ok=True, cwd=None):
        r = subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, cwd=str(cwd or self.proj),
                           env=self.env, capture_output=True, text=True, encoding="utf-8")
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def ctx(self):
        return self.run_r("context", stdin=json.dumps({"cwd": str(self.proj)})).stdout

    def test_save_context_take_cycle(self):
        self.assertEqual(self.ctx(), "")  # nothing waiting: silent
        r = self.run_r("save", "--title", "Парсер: этап 2", stdin="Goal: g\nNext step: run tests")
        self.assertIn("saved 2 lines", r.stdout)
        d = self.proj / ".journal" / "relay"
        files = list(d.glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].read_text(encoding="utf-8").startswith("# Парсер: этап 2"))
        self.assertEqual((self.proj / ".journal" / ".gitignore").read_text(encoding="utf-8"), "*\n")
        out = self.ctx()
        self.assertIn('[relay] handoff waiting: "Парсер: этап 2"', out)
        self.assertIn("relay.py", out)
        taken = self.run_r("take").stdout
        self.assertIn("Next step: run tests", taken)
        self.assertIn("marked as taken", taken)
        self.assertEqual(self.ctx(), "")
        self.assertIn("taken", self.run_r("list").stdout)
        self.assertIn("no handoff waiting", self.run_r("take", ok=False).stderr)

    def test_limits_and_projectless(self):
        r = self.run_r("save", "--title", "x", stdin="\n".join(["l"] * 200), ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotEqual(self.run_r("save", "--title", "x", stdin="", ok=False).returncode, 0)
        r = self.run_r("where", cwd=tempfile.gettempdir())
        self.assertEqual(Path(r.stdout.strip()), self.tmp / "journal" / "relay")

    def test_gather_in_git_repo(self):
        if not shutil.which("git"):
            self.skipTest("git not available")
        g = lambda *a: subprocess.run(["git", *a], cwd=str(self.proj), capture_output=True)
        g("init", "-q")
        g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "first commit")
        (self.proj / "a.txt").write_text("x", encoding="utf-8")
        (self.proj / ".journal" / "log").mkdir(parents=True)
        (self.proj / ".journal" / "STATE.md").write_text("# s\nIn progress: thing\n", encoding="utf-8")
        (self.proj / ".journal" / "log" / "2026-11.md").write_text(
            "## 2026-11-17 10:00 #t — Did a thing\nDone: x\nNext: y\n", encoding="utf-8")
        out = self.run_r("gather").stdout
        self.assertIn("first commit", out)
        self.assertIn("a.txt", out)
        self.assertIn("In progress: thing", out)
        self.assertIn("Did a thing", out)

    @unittest.skipUnless(BASH, "bash not available")
    def test_hook_command_runs(self):
        self.run_r("save", "--title", "Hooked", stdin="Goal: g")
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        cmd = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        env = dict(self.env, CLAUDE_PLUGIN_ROOT=ROOT.as_posix())
        r = subprocess.run([BASH, "-c", cmd], input=json.dumps({"cwd": str(self.proj)}), cwd=str(self.proj),
                           env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"Hooked"', r.stdout)


if __name__ == "__main__":
    unittest.main()
