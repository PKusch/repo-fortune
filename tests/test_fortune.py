import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime

from repo_fortune.core import (ARCHETYPES, Commit, favourite_word, fortune, longest_streak, lucky_number,
                               read_commits, render, render_markdown, stats)

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
        # git can print a UTC time with a trailing Z, which Python before 3.11 rejects
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-03T02:00:00+0000",
                       GIT_COMMITTER_DATE="2026-01-03T02:00:00+0000", TZ="UTC")
            subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                            "commit", "-q", "--allow-empty", "-m", "x"], check=True, env=env)
            self.assertEqual(read_commits(d)[0].when.hour, 2)

    def test_since_keeps_only_newer_commits(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            for when, msg in (("2020-01-03T10:00:00+0000", "old"), ("2026-01-03T10:00:00+0000", "new")):
                env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when, TZ="UTC")
                subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                                "commit", "-q", "--allow-empty", "-m", msg], check=True, env=env)
            self.assertEqual(len(read_commits(d)), 2)
            self.assertEqual([x.subject for x in read_commits(d, since="2025-01-01")], ["new"])

    def test_until_keeps_only_older_commits(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            for when, msg in (("2020-01-03T10:00:00+0000", "old"), ("2026-01-03T10:00:00+0000", "new")):
                env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when, TZ="UTC")
                subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                                "commit", "-q", "--allow-empty", "-m", msg], check=True, env=env)
            self.assertEqual([x.subject for x in read_commits(d, until="2025-01-01")], ["old"])
            self.assertEqual(read_commits(d, since="2021-01-01", until="2025-01-01"), [])

    def test_minimalist(self):
        cs = [c(f"2026-02-{i + 1:02d}T10:00:00", subject="more") for i in range(12)]
        self.assertEqual(fortune(cs)["name"], "The Minimalist")

    def test_hibernator(self):
        cs = [c(f"2026-01-{i + 5:02d}T10:00:00") for i in range(4)] + [c(f"2026-05-{i + 4:02d}T10:00:00") for i in range(4)]
        self.assertEqual(fortune(cs)["name"], "The Hibernator")

    def test_sprinter(self):
        cs = [c(f"2026-02-03T{9 + i % 8:02d}:00:00") for i in range(12)] + [c("2026-02-10T10:00:00"), c("2026-02-17T10:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Sprinter")

    def test_lone_wolf(self):
        cs = [c(f"2026-02-{(i % 8) * 3 + 1:02d}T10:00:00") for i in range(20)]  # 20 commits, one author
        self.assertEqual(fortune(cs)["name"], "The Lone Wolf")

    def test_a_short_solo_history_is_not_a_lone_wolf(self):
        cs = [c("2026-01-05T10:00:00"), c("2026-01-06T11:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Steady Hand")

    def test_choir(self):
        names = ["a", "b", "c", "d", "e"]
        cs = [c(f"2026-02-{(i % 8) * 3 + 1:02d}T10:00:00", author=names[i % 5]) for i in range(10)]
        self.assertEqual(fortune(cs)["name"], "The Choir")

    def test_lunch_break_coder(self):
        cs = [c(f"2026-01-{d:02d}T12:30:00") for d in range(5, 10)]
        self.assertEqual(fortune(cs)["name"], "The Lunch-Break Coder")

    def test_gardener(self):
        cs = [c(f"2026-01-{d:02d}T10:00:00", "refactor the parser") for d in range(5, 9)]
        self.assertEqual(fortune(cs)["name"], "The Gardener")

    def test_librarian(self):
        cs = [c(f"2026-01-{d:02d}T10:00:00", "update the README") for d in range(5, 9)]
        self.assertEqual(fortune(cs)["name"], "The Librarian")

    def test_every_archetype_has_a_unique_name_and_a_reading(self):
        names = [a[1] for a in ARCHETYPES]
        self.assertEqual(len(names), len(set(names)))
        for _, name, reading in ARCHETYPES:
            self.assertTrue(name.startswith("The "), name)
            self.assertGreater(len(reading.split()), 5, name)

    def test_the_readme_lists_every_fortune(self):
        readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
        for _, name, _ in ARCHETYPES:
            short = name[4:] if name != "The Choir" and name != "The Duet" else name
            self.assertIn(short, readme, name)

    def test_duet(self):
        cs = [c(f"2026-02-{(i % 8) * 3 + 1:02d}T10:00:00", author="ab"[i % 2]) for i in range(10)]
        self.assertEqual(fortune(cs)["name"], "The Duet")

    def test_two_authors_with_one_dominant_are_not_a_duet(self):
        cs = [c(f"2026-02-{(i % 8) * 3 + 1:02d}T10:00:00", author="a" if i < 9 else "b") for i in range(10)]
        self.assertNotEqual(fortune(cs)["name"], "The Duet")

    def test_markdown_has_the_name_the_reading_and_a_table(self):
        cs = [c("2026-01-05T10:00:00"), c("2026-01-06T11:00:00")]
        md = render_markdown(cs)
        self.assertTrue(md.startswith("### The Steady Hand"))
        self.assertIn("| commits | 2 |", md)
        self.assertEqual(md, render_markdown(cs))

    def test_markdown_for_an_empty_repo_is_just_the_page(self):
        md = render_markdown([])
        self.assertIn("The Blank Page", md)
        self.assertNotIn("|", md)

    def test_default_is_steady(self):
        cs = [c("2026-01-05T10:00:00"), c("2026-01-06T11:00:00")]
        self.assertEqual(fortune(cs)["name"], "The Steady Hand")

    def test_longest_gap_counts_days_between_commit_days(self):
        cs = [c("2026-01-01T10:00:00"), c("2026-01-02T10:00:00"), c("2026-03-03T10:00:00"), c("2026-03-04T10:00:00")]
        self.assertEqual(fortune(cs)["stats"]["longest_gap"], 60)
        self.assertEqual(fortune([c("2026-01-01T10:00:00")])["stats"]["longest_gap"], 0)

    def test_the_box_and_the_table_show_the_longest_gap(self):
        from repo_fortune.core import render
        cs = [c("2026-01-05T10:00:00"), c("2026-03-09T10:00:00")]
        self.assertIn("longest gap      63 days", render(cs))

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

    def test_author_is_matched_as_written_not_as_a_pattern(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            for email in ("a.b@x.com", "axb@x.com", "c+d@x.com"):
                subprocess.run(["git", "-C", d, "-c", "user.name=n", "-c", f"user.email={email}",
                                "commit", "-q", "--allow-empty", "-m", "x"], check=True)
            self.assertEqual(len(read_commits(d, author="a.b@x.com")), 1)
            self.assertEqual(len(read_commits(d, author="A.B@X.COM")), 1)
            self.assertEqual(len(read_commits(d, author="c+d@x.com")), 1)
            self.assertEqual(read_commits(d, author="C["), [])

    def _commit(self, d, when, subject="x", name="a"):
        env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
        subprocess.run(["git", "-C", d, "-c", f"user.name={name}", "-c", "user.email=a@a",
                        "commit", "-q", "--allow-empty", "-m", subject], check=True, env=env)

    def test_names_and_subjects_are_read_as_utf8_on_a_machine_not_set_to_utf8(self):
        # A machine whose language setting is not UTF-8 (common on Windows) used to
        # decode git's output with that setting and crash on the first "é".
        import json
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            self._commit(d, "2026-01-05T10:00:00+0000", "café crème", name="José Müller")
            env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0",
                       PYTHONCOERCECLOCALE="0", PYTHONIOENCODING="ascii")
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d, "--json"],
                               cwd=ROOT, capture_output=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
            self.assertEqual(json.loads(r.stdout)["stats"]["n"], 1)
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d],
                               cwd=ROOT, capture_output=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))

    def test_a_line_separator_inside_a_name_or_subject_does_not_split_the_commit(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            self._commit(d, "2026-01-05T10:00:00+0000", "line sep", name="A\u0085B")
            (only,) = read_commits(d)
            self.assertEqual((only.author, only.subject), ("A\u0085B", "line sep"))

    def test_a_bare_date_means_the_whole_day_whatever_the_time_now(self):
        # git reads --since 2026-01-01 as 1 January at the current clock time, so a
        # commit early on the 1st was in or out depending on when you ran it.
        import json
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            for when in ("2025-12-31T23:59:30+0000", "2026-01-01T00:00:30+0000",
                         "2026-06-30T23:59:30+0000", "2026-07-01T00:00:30+0000"):
                self._commit(d, when)
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d, "--json",
                                "--since", "2026-01-01", "--until", "2026-06-30"],
                               cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, TZ="UTC"))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["stats"]["n"], 2)

    def test_a_filter_that_matches_nothing_says_so_rather_than_a_blank_page(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            self._commit(d, "2026-01-05T10:00:00+0000")
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d, "--author", "nobody"],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertNotIn("BLANK PAGE", r.stdout)
            self.assertEqual(r.stderr.strip(), "repo-fortune: no commits match --author 'nobody'")

    def test_an_impossible_date_is_refused_in_one_line(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            self._commit(d, "2026-01-05T10:00:00+0000")
            for flag, value in (("--since", "2026-02-30"), ("--until", "2026-13-01")):
                r = subprocess.run([sys.executable, "-m", "repo_fortune", d, flag, value],
                                   cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertEqual(r.stderr.strip(), f"repo-fortune: '{value}' is not a real date")

    def test_an_empty_repo_is_the_blank_page_when_git_speaks_another_language(self):
        # git translates its "no commits yet" message; this stands in a git that
        # answers in German and passes every other call to the real one.
        import shutil
        real = shutil.which("git")
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as bindir:
            fake = os.path.join(bindir, "git")
            with open(fake, "w", encoding="utf-8") as f:
                f.write(f"#!{sys.executable}\n"
                        "import subprocess, sys\n"
                        f"r = subprocess.run([{real!r}, *sys.argv[1:]], capture_output=True)\n"
                        "if r.returncode and 'log' in sys.argv:\n"
                        "    sys.stderr.write(\"fatal: Ihr aktueller Branch 'main' hat noch keine Commits.\\n\")\n"
                        "    sys.exit(r.returncode)\n"
                        "sys.stdout.buffer.write(r.stdout); sys.stderr.buffer.write(r.stderr)\n"
                        "sys.exit(r.returncode)\n")
            os.chmod(fake, 0o755)
            subprocess.run(["git", "init", "-q", d], check=True)
            env = dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"])
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d], cwd=ROOT,
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("BLANK PAGE", r.stdout)

    def test_the_command_line_reads_a_window_with_since_and_until(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            for when in ("2020-01-03T10:00:00+0000", "2023-01-03T10:00:00+0000", "2026-01-03T10:00:00+0000"):
                env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
                subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                                "commit", "-q", "--allow-empty", "-m", "x"], check=True, env=env)
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d, "--json",
                                "--since", "2021-01-01", "--until", "2025-01-01"],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["stats"]["n"], 1)

    def test_markdown_flag_prints_a_table_not_a_box(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            subprocess.run(["git", "-C", d, "-c", "user.name=a", "-c", "user.email=a@a",
                            "commit", "-q", "--allow-empty", "-m", "x"], check=True)
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d, "--markdown"],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("|", r.stdout)
            self.assertNotIn("+----", r.stdout)

    def test_the_box_and_the_table_show_refactor_and_docs_shares(self):
        cs = [c("2026-01-05T10:00:00", "refactor parser"), c("2026-01-06T10:00:00", "update README"),
              c("2026-01-07T10:00:00", "add thing"), c("2026-01-08T10:00:00", "add other")]
        self.assertIn("refactor commits 25%", render(cs))
        self.assertIn("docs commits     25%", render(cs))
        self.assertIn("| docs commits | 25% |", render_markdown(cs))

    def test_favourite_word_skips_filler_and_ties_go_to_the_first_seen(self):
        self.assertEqual(favourite_word(["add the parser", "parser tests", "the tests"]), "parser")
        self.assertEqual(favourite_word(["add the", "fix a"]), None)
        self.assertEqual(favourite_word(["Parser", "PARSER again"]), "parser")

    def test_favourite_word_reads_letters_in_any_alphabet(self):
        self.assertEqual(favourite_word(["Größe ändern", "Größe prüfen"]), "größe")

    def test_a_long_favourite_word_does_not_push_out_the_edge_of_the_box(self):
        cs = [c(f"2026-01-0{d}T10:00:00", "internationalisation-and-localisation-overhaul") for d in (1, 2, 3)]
        widths = {len(line) for line in render(cs).splitlines()}
        self.assertEqual(widths, {52})
        self.assertIn("...", render(cs))

    def test_a_wide_favourite_word_keeps_the_box_edge_straight(self):
        # Chinese, Japanese and Korean characters take two columns on screen.
        from repo_fortune.core import columns
        for word in ("修正しました", "国際化対応国際化対応国際化対応国際化対応国際化対応"):
            cs = [c(f"2026-01-0{d}T10:00:00", word) for d in (1, 2, 3)]
            self.assertEqual({columns(line) for line in render(cs).splitlines()}, {52}, word)

    def test_the_box_and_the_table_show_the_favourite_word(self):
        cs = [c("2026-01-05T10:00:00", "tune parser"), c("2026-01-06T10:00:00", "parser tests")]
        self.assertIn("favourite word   parser", render(cs))
        self.assertIn("| favourite word | parser |", render_markdown(cs))

    def test_the_readme_counts_the_fortunes_correctly(self):
        words = {18: "Eighteen"}
        readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
        self.assertIn(f"{words.get(len(ARCHETYPES), '?')} fortunes", readme)

    def test_the_changelog_has_an_entry_for_the_current_version(self):
        from repo_fortune import __version__
        log = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
        self.assertIn(f"## {__version__}", log)

    def test_json_and_markdown_together_is_a_usage_error(self):
        r = subprocess.run([sys.executable, "-m", "repo_fortune", ".", "--json", "--markdown"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("not allowed with argument", r.stderr)

    def test_list_with_json_prints_every_fortune_as_json(self):
        import json
        r = subprocess.run([sys.executable, "-m", "repo_fortune", "--list", "--json"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([f["fortune"] for f in out], [name for _, name, _ in ARCHETYPES])

    def test_list_prints_every_fortune_without_reading_a_repo(self):
        from repo_fortune.cli import main
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["--list", "/no/such/place"])
        self.assertEqual(code, 0)
        lines = buf.getvalue().strip().splitlines()
        self.assertEqual(len(lines), len(ARCHETYPES))
        self.assertTrue(all(l.startswith("The ") for l in lines))

    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, "-m", "repo_fortune", d], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
