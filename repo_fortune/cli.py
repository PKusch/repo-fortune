import argparse
import json
import sys

from . import __version__
from .core import ARCHETYPES, fortune, read_commits, render, render_markdown


def main(argv=None):
    p = argparse.ArgumentParser(prog="repo-fortune",
                                description="Read your git history's fortune.")
    p.add_argument("path", nargs="?", default=".", help="repo to read (default: here)")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--author", help="only read commits whose author matches this name or email")
    p.add_argument("--since", help="only read commits after this date, e.g. 2026-01-01 or '3 months ago'")
    p.add_argument("--until", help="only read commits up to this date, e.g. 2026-06-30; with --since this reads one window of history")
    p.add_argument("--markdown", action="store_true",
                   help="print the fortune as a Markdown block to paste into a README or issue")
    p.add_argument("--json", action="store_true",
                   help="print the fortune and its numbers as JSON")
    p.add_argument("--list", action="store_true", dest="list_fortunes",
                   help="print every fortune there is and exit")
    args = p.parse_args(argv)
    # A favourite word like "größe" must not crash a console that cannot show it.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if args.list_fortunes:
        for _, name, reading in ARCHETYPES:
            print(f"{name}: {reading}")
        return 0
    try:
        commits = read_commits(args.path, author=args.author, since=args.since, until=args.until)
    except RuntimeError as e:
        print(f"repo-fortune: {e}", file=sys.stderr)
        return 1
    filters = [f"--{k} {v!r}" for k, v in (("author", args.author), ("since", args.since), ("until", args.until)) if v]
    if not commits and filters:
        # The Blank Page means a repo with no history yet. Saying it about a
        # repo whose commits a filter left out would be a fortune about a typo.
        print(f"repo-fortune: no commits match {' '.join(filters)}", file=sys.stderr)
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
    print(render_markdown(commits) if args.markdown else render(commits))
    return 0
