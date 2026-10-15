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

    def test_early_bird(self):
        cs = [c(f"2026-01-{d:02d}T06:00:00") for d in range(5, 9)]
        self.assertEqual(fortune(cs)["name"], "The Early Bird")

    def test_confetti_cannon(self):
        cs = [c("2026-01-05T10:00:00", "ship it \U0001F389")] * 3 + [c("2026-01-06T10:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Confetti Cannon")

    def test_novelist(self):
        long = "rework the importer so that it reads each file once and reports every problem together"
        cs = [c("2026-01-05T10:00:00", long), c("2026-01-06T11:00:00", long)]
        self.assertEqual(fortune(cs)["name"], "The Novelist")

    def test_streaker(self):
        cs = [c(f"2026-01-{d:02d}T10:00:00") for d in range(5, 20)]  # 15 days in a row
        self.assertEqual(fortune(cs)["name"], "The Streaker")

    def test_a_commit_made_in_utc_is_read(self):
        # git can print a UTC time with a trailing Z, which Python 3.9 rejects
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-03T02:00:00+0000",
                       GIT_COMMITTER_DATE="2026-01-03T02:00:00+0000", TZ="UTC")
            subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                            "commit", "-q", "--allow-empty", "-m", "x"], check=True, env=env)
            self.assertEqual(read_commits(d)[0].when.hour, 2)

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

    def test_repo_with_no_commits_is_the_blank_page(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            self.assertEqual(read_commits(d), [])
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("BLANK PAGE", r.stdout)

    def test_json_output_is_valid_and_has_the_fortune(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-03T02:00:00+0000",
                       GIT_COMMITTER_DATE="2026-01-03T02:00:00+0000")
            subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                            "commit", "-q", "--allow-empty", "-m", "x"], check=True, env=env)
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d, "--json"], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            self.assertIn("fortune", out)
            self.assertEqual(out["stats"]["n"], 1)
            self.assertEqual(out["stats"]["busiest_day"]["commits"], 1)

    def test_author_filter_reads_only_that_authors_commits(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            for who in ("ann", "ann", "bob"):
                subprocess.run(["git", "-C", d, "-c", f"user.name={who}", "-c", f"user.email={who}@x",
                                "commit", "-q", "--allow-empty", "-m", "x"], check=True)
            self.assertEqual(len(read_commits(d)), 3)
            self.assertEqual(len(read_commits(d, author="ann")), 2)
            self.assertEqual(len(read_commits(d, author="bob")), 1)
            self.assertEqual(read_commits(d, author="nobody"), [])

    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
