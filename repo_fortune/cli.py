import argparse
import json
import sys

from . import __version__
from .core import fortune, read_commits, render


def main(argv=None):
    p = argparse.ArgumentParser(prog="repo-fortune",
                                description="Read your git history's fortune.")
    p.add_argument("path", nargs="?", default=".", help="repo to read (default: here)")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--json", action="store_true",
                   help="print the fortune and its numbers as JSON")
    args = p.parse_args(argv)
    try:
        commits = read_commits(args.path)
    except RuntimeError as e:
        print(f"repo-fortune: {e}", file=sys.stderr)
        return 1
    if args.json:
        f = fortune(commits)
        stats = {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                 for k, v in f["stats"].items() if k != "busiest_day"}
        if "busiest_day" in f["stats"]:
            day, count = f["stats"]["busiest_day"]
            stats["busiest_day"] = {"date": day.isoformat(), "commits": count}
        print(json.dumps({"fortune": f["name"], "reading": f["reading"], "stats": stats}, indent=2))
        return 0
    print(render(commits))
    return 0
