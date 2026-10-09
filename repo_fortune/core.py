"""Read a repo's commit history and turn it into a fortune.

Everything here is plain rules on plain numbers: no network, no model.
The same history always gives the same fortune.
"""
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta

SEP = "\x1f"


@dataclass(frozen=True)
class Commit:
    author: str
    when: datetime  # author-local time, as recorded
    subject: str


def read_commits(path="."):
    """Return commits oldest-first. Raises RuntimeError if not a git repo."""
    fmt = SEP.join(["%an", "%aI", "%s"])
    try:
        out = subprocess.run(
            ["git", "-C", path, "log", "--no-merges", f"--format={fmt}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(f"could not read git history in {path!r}") from e
    commits = []
    for line in out.splitlines():
        parts = line.split(SEP, 2)
        if len(parts) != 3:
            continue
        name, iso, subject = parts
        commits.append(Commit(name, datetime.fromisoformat(iso.replace("Z", "+00:00")), subject))
    commits.reverse()
    return commits


FIX_WORDS = re.compile(r"\b(fix|fixes|fixed|bug|hotfix|oops|revert|typo)\b", re.I)
WIP_WORDS = re.compile(r"^(wip|tmp|temp|asdf|stuff|update|changes|misc|\.+)$", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def longest_streak(days):
    """Longest run of consecutive calendar days that have a commit."""
    days = sorted(set(days))
    best = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best


def stats(commits):
    n = len(commits)
    if n == 0:
        return {"n": 0}
    hours = [c.when.hour for c in commits]
    days = [c.when.date() for c in commits]
    subjects = [c.subject.strip() for c in commits]
    words = [len(s.split()) for s in subjects]
    authors = Counter(c.author for c in commits)
    weekday_counts = Counter(c.when.weekday() for c in commits)
    return {
        "n": n,
        "first": commits[0].when.date(),
        "last": commits[-1].when.date(),
        "authors": len(authors),
        "top_author_share": authors.most_common(1)[0][1] / n,
        "night": sum(1 for h in hours if h >= 23 or h < 5) / n,
        "early": sum(1 for h in hours if 5 <= h < 8) / n,
        "weekend": sum(1 for c in commits if c.when.weekday() >= 5) / n,
        "fix": sum(1 for s in subjects if FIX_WORDS.search(s)) / n,
        "wip": sum(1 for s in subjects if WIP_WORDS.match(s)) / n,
        "emoji": sum(1 for s in subjects if EMOJI.search(s)) / n,
        "avg_words": sum(words) / n,
        "one_word": sum(1 for w in words if w <= 1) / n,
        "streak": longest_streak(days),
        "active_days": len(set(days)),
        "busiest_day": Counter(days).most_common(1)[0],
        "busiest_weekday": weekday_counts.most_common(1)[0][0],
        "peak_hour": Counter(hours).most_common(1)[0][0],
    }


# Each archetype: (score function over stats, name, reading). Highest score wins;
# ties go to the earlier entry, so the result is deterministic.
ARCHETYPES = [
    (lambda s: s["night"] * 2.0 if s["night"] > 0.25 else 0,
     "The Night Owl",
     "The moon is your standup. Your best ideas arrive after everyone else has logged off."),
    (lambda s: s["weekend"] * 2.0 if s["weekend"] > 0.4 else 0,
     "The Weekend Warrior",
     "Weekdays are for meetings. Saturdays are for actually building the thing."),
    (lambda s: s["fix"] * 2.5 if s["fix"] > 0.3 else 0,
     "The Firefighter",
     "Every third commit is an apology to the previous one. Yet the repo stands."),
    (lambda s: s["wip"] * 3.0 if s["wip"] > 0.1 else 0,
     "The Mysterious One",
     "Your commit messages are haiku with the words removed. The future you will wonder."),
    (lambda s: s["emoji"] * 3.0 if s["emoji"] > 0.2 else 0,
     "The Confetti Cannon",
     "Every commit is a small parade. The changelog is the happiest place in the office."),
    (lambda s: s["early"] * 2.5 if s["early"] > 0.2 else 0,
     "The Early Bird",
     "You ship before the coffee has cooled. Nobody has ever seen you at your worst hour."),
    (lambda s: 1.0 if s["avg_words"] > 9 else 0,
     "The Novelist",
     "Your commit messages have plot, character and a third act. Reviewers send thanks."),
    (lambda s: 1.0 if s["streak"] >= 14 else 0,
     "The Streaker",
     "Two weeks without a day off. The repo is grateful. Your friends have questions."),
    (lambda s: 0.5,
     "The Steady Hand",
     "No drama, no midnight panic. Just commits, arriving on schedule like a good train."),
]


def fortune(commits):
    """Return a dict with the stats, the chosen archetype, and its reading."""
    s = stats(commits)
    if s["n"] == 0:
        return {"stats": s, "name": "The Blank Page",
                "reading": "Nothing has happened yet. Everything still can."}
    best = max(range(len(ARCHETYPES)), key=lambda i: (ARCHETYPES[i][0](s), -i))
    _, name, reading = ARCHETYPES[best]
    return {"stats": s, "name": name, "reading": reading}


def lucky_number(commits):
    """A stable 'lucky number' from the history: same repo state, same number."""
    return sum(len(c.subject) for c in commits) % 99 + 1


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _pct(x):
    return f"{round(x * 100)}%"


def _hour(h):
    return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"


def render(commits, width=52):
    f = fortune(commits)
    s = f["stats"]
    lines = [f["name"].upper(), ""]
    lines += wrap(f["reading"], width - 4)
    if s["n"]:
        lines += [
            "",
            f"commits          {s['n']}",
            f"lived between    {s['first']} and {s['last']}",
            f"favourite hour   {_hour(s['peak_hour'])}",
            f"favourite day    {DAYS[s['busiest_weekday']]}",
            f"night commits    {_pct(s['night'])}",
            f"weekend commits  {_pct(s['weekend'])}",
            f"'fix' commits    {_pct(s['fix'])}",
            f"longest streak   {s['streak']} day{'s' * (s['streak'] != 1)}",
            f"lucky number     {lucky_number(commits)}",
        ]
    top = "+" + "-" * (width - 2) + "+"
    body = [top] + [f"| {l:<{width - 4}} |" for l in lines] + [top]
    return "\n".join(body)


def wrap(text, width):
    out, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out
