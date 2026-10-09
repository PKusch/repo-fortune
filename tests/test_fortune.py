import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime

from repo_fortune.core import (Commit, fortune, longest_streak, lucky_number,
                               read_commits, render, stats)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def c(when, subject="add thing", author="a"):
    return Commit(author, datetime.fromisoformat(when.replace("Z", "+00:00")), subject)


class Rules(unittest.TestCase):
    def test_empty_repo(self):
        self.assertEqual(fortune([])["name"], "The Blank Page")
        self.assertIn("BLANK PAGE", render([]))

    def test_night_owl(self):
        cs = [c(f"2026-01-{d:02d}T02:00:00") for d in range(1, 8)]
        self.assertEqual(fortune(cs)["name"], "The Night Owl")

    def test_weekend_warrior(self):
        # 2026-01-03 and 04 are Saturday and Sunday
        cs = [c("2026-01-03T14:00:00"), c("2026-01-04T14:00:00"), c("2026-01-05T14:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Weekend Warrior")

    def test_firefighter(self):
        cs = [c("2026-01-05T10:00:00", "fix bug")] * 4 + [c("2026-01-06T10:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Firefighter")

    def test_mysterious(self):
        cs = [c("2026-01-05T10:00:00", "wip")] * 2 + [c("2026-01-06T10:00:00")] * 8
        self.assertEqual(fortune(cs)["name"], "The Mysterious One")

    def test_default_is_steady(self):
        cs = [c("2026-01-05T10:00:00"), c("2026-01-06T11:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Steady Hand")

    def test_streak(self):
        days = [date(2026, 1, d) for d in (1, 2, 3, 5, 6)]
        self.assertEqual(longest_streak(days), 3)
        self.assertEqual(longest_streak([]), 0)

    def test_deterministic(self):
        cs = [c("2026-01-05T10:00:00", "one"), c("2026-01-06T11:00:00", "two")]
        self.assertEqual(render(cs), render(cs))
        self.assertEqual(lucky_number(cs), lucky_number(cs))
        self.assertTrue(1 <= lucky_number(cs) <= 99)

    def test_stats_shares(self):
        s = stats([c("2026-01-05T02:00:00"), c("2026-01-05T12:00:00")])
        self.assertEqual(s["night"], 0.5)
        self.assertEqual(s["n"], 2)


class RealRepo(unittest.TestCase):
    def test_reads_a_real_git_repo_and_cli_runs(self):
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                   "GIT_AUTHOR_DATE": "2026-01-03T02:00:00+00:00",
                   "GIT_COMMITTER_DATE": "2026-01-03T02:00:00+00:00"}
            run = lambda *a: subprocess.run(["git", "-C", d, *a], check=True,
                                            capture_output=True, env=env)
            run("init", "-q")
            for i in range(3):
                run("commit", "-q", "--allow-empty", "-m", f"commit {i}")
            self.assertEqual(len(read_commits(d)), 3)
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("NIGHT OWL", r.stdout)

    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
