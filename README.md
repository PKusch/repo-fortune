# repo-fortune

[![ci](https://github.com/PKusch/repo-fortune/actions/workflows/ci.yml/badge.svg)](https://github.com/PKusch/repo-fortune/actions/workflows/ci.yml)

A horoscope for your git repo. Run it in any repo and it reads the commit history and tells you what kind of repo it is.

```
$ python3 -m repo_fortune
+--------------------------------------------------+
| THE NOVELIST                                     |
|                                                  |
| Your commit messages have plot, character and a  |
| third act. Reviewers send thanks.                |
|                                                  |
| commits          32                              |
| lived between    2026-09-02 and 2026-09-29       |
| favourite hour   10pm                            |
| favourite day    Wednesday                       |
| night commits    16%                             |
| weekend commits  16%                             |
| 'fix' commits    3%                              |
| longest streak   5 days                          |
| lucky number     77                              |
+--------------------------------------------------+
```

## Try it

Nothing to install. It needs Python 3.9+ and git.

```bash
git clone https://github.com/PKusch/repo-fortune
cd repo-fortune
python3 -m repo_fortune /path/to/any/repo
```

Add `--json` to get the fortune and its numbers as data instead of the box, `--author "Ann"` to read only one person's commits, or `--since 2026-01-01` (or `--since "3 months ago"`) to read only newer history.

## What it does and why

It counts a few plain things in your history (when you commit, how long your messages are, how often they say "fix") and picks the fortune that fits best. Eleven fortunes: Night Owl, Weekend Warrior, Firefighter, Mysterious One, Confetti Cannon, Early Bird, Novelist, Streaker, Lone Wolf, The Choir, and Steady Hand. A repo with no commits yet gets a twelfth, the Blank Page.

It is for fun and for screenshots. It never leaves your machine and never uses a model: the same history always gives the same fortune, so it is safe to argue about with your team.

## Tests

```bash
python3 -m unittest discover -s tests
```
