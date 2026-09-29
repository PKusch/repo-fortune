import argparse
import sys

from . import __version__
from .core import read_commits, render


def main(argv=None):
    p = argparse.ArgumentParser(prog="repo-fortune",
                                description="Read your git history's fortune.")
    p.add_argument("path", nargs="?", default=".", help="repo to read (default: here)")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)
    try:
        commits = read_commits(args.path)
    except RuntimeError as e:
        print(f"repo-fortune: {e}", file=sys.stderr)
        return 1
    print(render(commits))
    return 0
