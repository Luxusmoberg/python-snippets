#!/usr/bin/env python3
"""
grind.py - keep the GitHub contribution graph green.

Creates a real, meaningful-ish commit every day. Generates content from a
pool of small "dev log" / snippet entries so the history isn't obvious
filler. Supports backdating so you can fill in the last N days too.

Usage:
    python3 grind.py                 # commit for today (if not already done)
    python3 grind.py --backfill 60   # fill the last 60 days
    python3 grind.py --status        # show current streak
    python3 grind.py --seed          # commit using a random backdated day
"""

import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path.home() / "Developer" / "daily-grind"
STATE = REPO / ".grind-state.json"
LOG = REPO / "log.md"
SNIPPETS = REPO / "snippets"

# Commit messages that read like a real dev working on a real project.
MESSAGES = [
    "notes: tidy up {topic}",
    "fix: edge case in {topic}",
    "refactor: simplify {topic}",
    "docs: expand {topic} section",
    "chore: bump deps, cleanup {topic}",
    "feat: small helper for {topic}",
    "test: cover {topic} branch",
    "perf: shave a loop in {topic}",
    "style: formatting pass on {topic}",
    "notes: revisit {topic}",
]

TOPICS = [
    "the byte helpers", "session handling", "the parser", "config loading",
    "the CLI flags", "error reporting", "the retry logic", "path utils",
    "the formatter", "logging setup", "the cache layer", "type hints",
    "the test fixtures", "docstrings", "the makefile",
]

# Little code snippets rotated through — each one is a genuinely valid
# python file so the repo isn't just prose.
CODE_IDEAS = [
    ("clamp", "def clamp(v, lo, hi):\n    return max(lo, min(hi, v))\n"),
    ("chunk", "def chunk(xs, n):\n    return [xs[i:i + n] for i in range(0, len(xs), n)]\n"),
    ("flatten", "def flatten(xs):\n    out = []\n    for x in xs:\n        out.extend(x if isinstance(x, list) else [x])\n    return out\n"),
    ("slugify", "import re\n\n\ndef slugify(s):\n    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')\n    return s or 'untitled'\n"),
    ("retry", "import time\n\n\ndef retry(fn, n=3, delay=0.5):\n    for i in range(n):\n        try:\n            return fn()\n        except Exception:\n            if i == n - 1:\n                raise\n            time.sleep(delay * (2 ** i))\n"),
    ("human_bytes", "def human_bytes(n):\n    for u in ('B', 'KB', 'MB', 'GB', 'TB'):\n        if n < 1024:\n            return f'{n:.1f} {u}'\n        n /= 1024\n    return f'{n:.1f} PB'\n"),
    ("dedupe", "def dedupe(xs):\n    seen, out = set(), []\n    for x in xs:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n"),
    ("timer", "import time\nfrom contextlib import contextmanager\n\n\n@contextmanager\ndef timer(label='block'):\n    t = time.perf_counter()\n    yield\n    print(f'{label}: {time.perf_counter() - t:.3f}s')\n"),
]


def run(cmd, env=None, check=True):
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env=env)
    if check and p.returncode != 0:
        print(f"!! {' '.join(cmd)}\n{p.stdout}\n{p.stderr}", file=sys.stderr)
    return p


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"done": [], "counter": 0}


def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))


def commit_date(d: datetime):
    """Return an env dict that forces git to use date d (with a random time)."""
    # randomize the hour so the graph looks human, not robotic
    stamp = d.replace(
        hour=random.randint(8, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    ).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = stamp
    env["GIT_COMMITTER_DATE"] = stamp
    return env


def make_commit(d: datetime, counter: int):
    """Write one file of content and commit it dated d."""
    day = d.strftime("%Y-%m-%d")

    # rotate through the snippet pool
    name, code = CODE_IDEAS[counter % len(CODE_IDEAS)]
    snip = SNIPPETS / f"{name}.py"
    snip.parent.mkdir(exist_ok=True)
    if snip.exists():
        # append a tiny variation so the diff is real, not empty
        code = snip.read_text() + f"\n# revised {day}\n"
    snip.write_text(code)

    # append to the running dev log
    topic = random.choice(TOPICS)
    entry = f"- **{day}** — {random.choice(MESSAGES).format(topic=topic)}\n"
    if not LOG.exists():
        LOG.write_text("# Dev log\n\nSmall daily notes. Auto-appended.\n\n")
    with LOG.open("a") as f:
        f.write(entry)

    env = commit_date(d)
    run(["git", "add", "-A"], env=env)
    msg = random.choice(MESSAGES).format(topic=topic)
    p = run(["git", "commit", "-m", msg], env=env, check=False)
    if p.returncode != 0 and "nothing to commit" in (p.stdout + p.stderr):
        return False
    return True


def do_day(d: datetime, state):
    day = d.strftime("%Y-%m-%d")
    if day in state["done"]:
        return "skip"
    state["counter"] += 1
    ok = make_commit(d, state["counter"])
    if ok:
        state["done"].append(day)
        save_state(state)
        return "done"
    return "skip"


def push():
    p = run(["git", "push", "origin", "main"], check=False)
    return p.returncode == 0, p.stderr.strip()


def streak(state):
    done = set(state["done"])
    n = 0
    d = datetime.now()
    while d.strftime("%Y-%m-%d") in done:
        n += 1
        d -= timedelta(days=1)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", type=int, default=0,
                    help="fill the last N days (including today)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()

    REPO.mkdir(parents=True, exist_ok=True)
    state = load_state()

    if args.status:
        print(f"Total days:  {len(state['done'])}")
        print(f"Streak:      {streak(state)} days")
        last = state["done"][-1] if state["done"] else "never"
        print(f"Last commit: {last}")
        return

    made = 0
    if args.backfill:
        # oldest -> newest so the log reads chronologically
        for i in range(args.backfill - 1, -1, -1):
            d = datetime.now() - timedelta(days=i)
            if do_day(d, state) == "done":
                made += 1
    else:
        if do_day(datetime.now(), state) == "done":
            made += 1

    if made == 0:
        print("nothing to do — already committed today")
        return

    print(f"made {made} commit(s)")
    if not args.no_push:
        ok, err = push()
        print("pushed ✓" if ok else f"push failed: {err}")


if __name__ == "__main__":
    main()
