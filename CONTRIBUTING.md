# Contributing

The most useful thing you can send is a repo where the fortune feels wrong. Open a "fortune feels wrong" issue and say what the repo is like and what you expected.

## Where things live

- `repo_fortune/core.py` reads the git history and counts the plain things.
- The fortunes and the rules that pick between them sit beside it in `repo_fortune/`.
- `tests/test_fortune.py` covers all of it.

## Running it

```bash
python3 -m unittest discover -s tests
python3 -m repo_fortune /path/to/any/repo
```

Nothing to install. It needs Python 3.9+ and git, and it stays free of outside packages and models, so the same history always gives the same fortune.
