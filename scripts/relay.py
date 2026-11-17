#!/usr/bin/env python3
"""animus-relay: hand work over to a fresh Claude Code session without losing the thread.

A handoff is a short Markdown file kept next to the project's journal
(<project>/.journal/relay/, or ~/journal/relay/ for sessions with no project), so it
is never committed. The next session in that project sees one line at start-up
while a handoff is waiting, and takes it with `take`.

Commands:
  context                  SessionStart hook: one line per waiting handoff, nothing otherwise
  gather                   facts for writing a handoff: git state, STATE.md, recent journal entries
  save --title T           stdin -> a new handoff file (<= RELAY_MAX_LINES lines)
  take [FILE]              print the newest waiting handoff (or FILE) and mark it taken
  list                     waiting and taken handoffs
  where                    print the relay dir
  check [PATH]             is it safe to close/delete this session? exit 1 if work would be lost

Standard library only, Python 3.9+. No network.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

JOURNAL_GLOBAL = Path(os.environ.get("JOURNAL_GLOBAL_DIR") or Path.home() / "journal").expanduser()
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
ECO_FILE = Path(os.environ.get("CLAUDE_ECOSYSTEM_FILE") or CLAUDE_DIR / "ecosystem.json").expanduser()
MAX_LINES = int(os.environ.get("RELAY_MAX_LINES") or 120)
SCRIPT = Path(__file__).resolve()
SELF = "animus-relay"
ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s")

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run(args, cwd):
    try:
        return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=10).stdout.strip()
    except Exception:
        return ""


def journal_dir(cwd):
    """Same rule as animus-journal: git root/.journal, or the global dir for projectless sessions."""
    p = Path(cwd)
    s = str(p).replace("\\", "/").lower()
    if "scratch-workspaces" in s or not p.exists():
        return JOURNAL_GLOBAL
    for base in (Path.home(), Path(tempfile.gettempdir())):
        try:
            if p.resolve() == base.resolve():
                return JOURNAL_GLOBAL
        except OSError:
            pass
    top = run(["git", "rev-parse", "--show-toplevel"], p)
    return Path(top or p) / ".journal"


def relay_dir(cwd=None):
    j = journal_dir(cwd or os.getcwd())
    d = j / "relay"
    return d


def ensure(d):
    (d / "taken").mkdir(parents=True, exist_ok=True)
    gi = d.parent / ".gitignore"
    if d.parent != JOURNAL_GLOBAL and not gi.exists():
        gi.write_text("*\n", encoding="utf-8")  # same convention as animus-journal
    return d


def waiting(d):
    return sorted(d.glob("*.md")) if d.is_dir() else []


def title_of(f):
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return f.stem


def age(f):
    mins = int((dt.datetime.now().timestamp() - f.stat().st_mtime) // 60)
    return f"{mins} min ago" if mins < 90 else (f"{mins // 60} h ago" if mins < 48 * 60 else f"{mins // 1440} d ago")


def register():
    try:
        e = json.loads(ECO_FILE.read_text(encoding="utf-8"))
        if not isinstance(e, dict):
            e = {}
    except (OSError, ValueError):
        e = {}
    e.setdefault("plugins", {})
    me = {"cmd": f'"{sys.executable}" "{SCRIPT}"'}
    if e["plugins"].get(SELF) != me:
        e["plugins"][SELF] = me
        try:
            ECO_FILE.parent.mkdir(parents=True, exist_ok=True)
            ECO_FILE.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass


# ---------- commands ----------

def cmd_context(_):
    cwd = os.getcwd()
    try:
        cwd = json.loads(sys.stdin.read() or "{}").get("cwd") or cwd
    except Exception:
        pass
    try:
        register()
        d = relay_dir(cwd)
        files = waiting(d)
    except Exception:
        return  # never break session start
    cmd = f'"{sys.executable}" "{SCRIPT}"'
    for f in files[-3:]:
        print(f"[relay] handoff waiting: \"{title_of(f)}\" ({age(f)}). To continue it: {cmd} take")


def cmd_gather(_):
    cwd = Path.cwd()
    j = journal_dir(cwd)
    out = [f"cwd: {cwd}", f"journal: {j}" + ("" if (j / "log").is_dir() else " (no entries yet)")]
    if run(["git", "rev-parse", "--is-inside-work-tree"], cwd) == "true":
        out.append(f"git branch: {run(['git', 'branch', '--show-current'], cwd) or '(detached)'}")
        stash = run(["git", "stash", "list"], cwd).splitlines()
        ahead = run(["git", "rev-list", "--count", "@{u}..HEAD"], cwd)
        if stash:
            out.append(f"stash: {len(stash)} entr{'y' if len(stash) == 1 else 'ies'}")
        if ahead.isdigit() and int(ahead):
            out.append(f"unpushed commits: {ahead}")
        status = run(["git", "status", "--short"], cwd).splitlines()
        out.append(f"uncommitted: {len(status)} file(s)")
        out += [f"  {l}" for l in status[:20]]
        if len(status) > 20:
            out.append(f"  (+{len(status) - 20} more)")
        log = run(["git", "log", "--oneline", "-5"], cwd)
        if log:
            out.append("recent commits:")
            out += [f"  {l}" for l in log.splitlines()]
    state = j / "STATE.md"
    if state.is_file() and j != JOURNAL_GLOBAL:
        out.append("STATE.md:")
        out += [f"  {l}" for l in state.read_text(encoding="utf-8", errors="replace").splitlines()[:40]]
    logs = sorted((j / "log").glob("*.md")) if (j / "log").is_dir() else []
    if logs:
        secs = re.split(r"(?m)^(?=## \d{4})", logs[-1].read_text(encoding="utf-8", errors="replace"))
        secs = [s.strip() for s in secs if ENTRY_RE.match(s)]
        if secs:
            out.append("recent journal entries:")
            for s in secs[-3:]:
                out += [f"  {l}" for l in s.splitlines()[:8]]
    files = waiting(relay_dir(cwd))
    if files:
        out.append("handoffs already waiting: " + ", ".join(f.name for f in files))
    print("\n".join(out))


def slug(s):
    s = re.sub(r"[^\w\s-]", "", s.lower(), flags=re.U).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    if len(s) > 40:  # cut at a word boundary, not mid-word
        s = s[:41].rsplit("-", 1)[0] if "-" in s[:41] else s[:40]
    return s.strip("-") or "handoff"


def cmd_save(a):
    text = sys.stdin.read().strip()
    n = len(text.splitlines())
    if not text:
        sys.exit("refused: empty handoff")
    if n > MAX_LINES:
        sys.exit(f"refused: {n} lines > {MAX_LINES}. A handoff is a map, not a transcript: compress and retry.")
    if not text.startswith("# "):
        text = f"# {a.title}\n\n{text}"
    d = ensure(relay_dir())
    f = d / f"{dt.datetime.now():%Y-%m-%d-%H%M}-{slug(a.title)}.md"
    f.write_text(text + "\n", encoding="utf-8")
    print(f"[relay] saved {n} lines -> {f}")
    print(f'[relay] in the new session, open this project and say: continue from the handoff "{a.title}"')


def cmd_take(a):
    d = relay_dir()
    if a.file:
        f = Path(a.file)
        if not f.is_file():
            f = d / a.file
    else:
        files = waiting(d)
        if not files:
            sys.exit("[relay] no handoff waiting here")
        f = files[-1]
    if not f.is_file():
        sys.exit(f"[relay] not found: {a.file}")
    print(f.read_text(encoding="utf-8", errors="replace"))
    if f.parent == d:
        ensure(d)
        f.replace(d / "taken" / f.name)
        print(f"[relay] marked as taken -> {d / 'taken' / f.name}")


def cmd_list(_):
    d = relay_dir()
    w = waiting(d)
    t = sorted((d / "taken").glob("*.md")) if (d / "taken").is_dir() else []
    for f in w:
        print(f"waiting  {f.name}  — {title_of(f)} ({age(f)})")
    for f in t[-10:]:
        print(f"taken    {f.name}  — {title_of(f)}")
    if not w and not t:
        print("[relay] no handoffs here")


def cmd_where(_):
    print(relay_dir())


# ---------- safe to close? ----------

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".journal"}


def git_repos(root, depth=2):
    """The repo containing root (if any) plus repos nested up to `depth` levels below it."""
    out = []
    top = run(["git", "rev-parse", "--show-toplevel"], root)
    if top:
        out.append(Path(top))

    def walk(d, level):
        if level > depth:
            return
        try:
            kids = [k for k in d.iterdir() if k.is_dir() and k.name not in SKIP_DIRS]
        except OSError:
            return
        for k in kids:
            if (k / ".git").exists():
                out.append(k)
            else:
                walk(k, level + 1)
    walk(root, 1)
    seen, uniq = set(), []
    for r in out:
        key = str(r.resolve()).lower()
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


def repo_problems(repo, scratch=False):
    """(blockers, notes). A repo with no remote is only a note outside a temporary folder:
    closing or deleting the session does not delete the folder, so local commits survive."""
    probs, notes = [], []
    status = run(["git", "status", "--porcelain"], repo).splitlines()
    # `run` strips the output, so the first line may have lost its leading space: path = l[2:].lstrip()
    changed = [l[2:].lstrip() for l in status if not l.startswith("??")]
    untracked = [l[2:].lstrip() for l in status if l.startswith("??")]
    if changed:
        probs.append(f"{len(changed)} uncommitted change(s): " + ", ".join(changed[:5]))
    if untracked:
        probs.append(f"{len(untracked)} untracked file(s): " + ", ".join(untracked[:5]))
    if not run(["git", "remote"], repo):
        if run(["git", "rev-parse", "--verify", "HEAD"], repo):
            (probs if scratch else notes).append("no remote: commits exist only on this machine"
                                                 + (" and this folder is deleted with the session" if scratch else ""))
    else:
        branches = run(["git", "for-each-ref", "--format=%(refname:short)|%(upstream:short)|%(upstream:track)",
                        "refs/heads"], repo).splitlines()
        for b in branches:
            name, up, track = (b.split("|") + ["", ""])[:3]
            if not up:
                probs.append(f"branch {name} has no upstream (never pushed?)")
            elif "ahead" in track:
                probs.append(f"branch {name} is {track.strip('[]')} of {up}: not pushed")
    stash = run(["git", "stash", "list"], repo).splitlines()
    if stash:
        probs.append(f"{len(stash)} stash entr{'y' if len(stash) == 1 else 'ies'}")
    return probs, notes


def outside_repos(root, repos, limit=10):
    """Top-level items in root that are not inside any git repo."""
    inside = [str(r.resolve()).lower() for r in repos]
    items = []
    try:
        for k in sorted(root.iterdir()):
            if k.name in SKIP_DIRS:
                continue
            path = str(k.resolve()).lower()
            if any(path == r or path.startswith(r + os.sep) for r in inside):
                continue
            if k.is_dir() and any(r.startswith(path + os.sep) for r in inside):
                continue  # a folder that only holds repos
            items.append(k.name + ("/" if k.is_dir() else ""))
    except OSError:
        pass
    return items[:limit], len(items)


def cmd_check(a):
    root = Path(a.path or os.getcwd()).resolve()
    scratch = "scratch-workspaces" in str(root).replace("\\", "/").lower()
    blockers, unsaved, notes = [], [], []
    repos = git_repos(root)
    for r in repos:
        probs, rnotes = repo_problems(r, scratch)
        # a temporary folder is deleted with the session: its problems lose work. A kept folder stays on disk,
        # so the same problems only mean "no copy elsewhere yet".
        (blockers if scratch else unsaved).extend(f"{r.name}: {p}" for p in probs)
        notes += [f"{r.name}: {n}" for n in rnotes]
    if scratch:
        loose, n = outside_repos(root, repos)
        if n:
            blockers.append(f"{n} item(s) in this session's temporary folder are in no git repo and will be "
                            f"deleted with the session: " + ", ".join(loose) + (" …" if n > len(loose) else ""))
    j = journal_dir(root)
    logs = sorted((j / "log").glob("*.md")) if (j / "log").is_dir() else []
    last = max((f.stat().st_mtime for f in logs), default=0)
    hours = (dt.datetime.now().timestamp() - last) / 3600
    if not logs:
        notes.append("no journal here: if the work matters, record it (animus-journal) before closing")
    elif hours > a.fresh:
        notes.append(f"last journal entry is {hours:.0f} h old: record this session if it did real work")
    if not waiting(relay_dir(root)):
        notes.append("no handoff waiting: save one (`save`) if the work continues in another session")
    print(f"[relay] check {root}")
    print(f"[relay] {len(repos)} git repo(s) checked" + (" · temporary session folder" if scratch else ""))
    for b in blockers:
        print(f"  ✗ {b}")
    for u in unsaved:
        print(f"  ! {u}")
    for n in notes:
        print(f"  · {n}")
    if blockers:
        print("[relay] NOT SAFE to close: fix the ✗ lines first")
    elif unsaved:
        print("[relay] SAFE to close: this folder stays on disk, nothing is deleted with the session. "
              "Not backed up yet (! lines): commit/push them only if the user wants a copy elsewhere")
    else:
        print("[relay] SAFE to close")
    if blockers:
        sys.exit(1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="relay.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("context").set_defaults(fn=cmd_context)
    sub.add_parser("gather").set_defaults(fn=cmd_gather)
    p = sub.add_parser("save")
    p.add_argument("--title", required=True)
    p.set_defaults(fn=cmd_save)
    p = sub.add_parser("take")
    p.add_argument("file", nargs="?")
    p.set_defaults(fn=cmd_take)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    sub.add_parser("where").set_defaults(fn=cmd_where)
    p = sub.add_parser("check", help="is it safe to close or delete this session?")
    p.add_argument("path", nargs="?")
    p.add_argument("--fresh", type=float, default=6, help="hours after which the journal counts as stale")
    p.set_defaults(fn=cmd_check)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
