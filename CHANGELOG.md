# Changelog

## Unreleased
- An impossible date such as `--since 2026-02-30` is refused in one line instead of being read as some other day.
- `--author` matches the text as written and in any case: `a.b@x.com` no longer also matches `axb@x.com`.
- A bare date in `--since` or `--until` now means the whole day. git read `--since 2026-01-01` as 1 January at the current clock time, so the same command gave a different fortune depending on when it ran.
- Reads author names and commit messages correctly on a machine that is not set to UTF-8, where a name like "José" used to crash it.
- The favourite word counts letters in any alphabet: "Größe ändern" gave "ndern", now "größe".
- A repo with no commits is The Blank Page even when git speaks another language.
- A very long favourite word no longer breaks the edge of the box.
- Needs Python 3.10 or newer. Python 3.9 no longer gets fixes, and GitHub's test machines no longer offer it.

## 0.2.0
- Seven new fortunes: The Duet, The Lunch-Break Coder, The Gardener, The Librarian, The Hibernator, The Sprinter and The Minimalist. Eighteen in all.
- The box and the table show the longest gap between commit days, the share of refactor and docs commits, and the favourite word.
- `--until` reads history up to a date, and with `--since` reads one window.
- `--list` prints every fortune and its reading without reading a repo.

## 0.1.0
- First release: a fortune for your git history, as a box, Markdown or JSON, with `--author` and `--since`.
