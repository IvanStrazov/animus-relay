# animus-relay

[![tests](https://github.com/IvanStrazov/animus-relay/actions/workflows/test.yml/badge.svg)](https://github.com/IvanStrazov/animus-relay/actions/workflows/test.yml)
[![version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)
![python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)

**Context too big? Restarting tomorrow? Pass the baton to a fresh session — and it picks it up by itself.**

> **Part of Animus** — small, local, token-frugal plugins that let Claude Code remember you and your work. Each works alone; together they share context through `~/.claude/ecosystem.json`.
>
> | Plugin | What it does |
> |---|---|
> | [animus-journal](https://github.com/IvanStrazov/animus-journal) | Project journal on a hard token budget: what was done, decided, next |
> | [animus-portrait](https://github.com/IvanStrazov/animus-portrait) | A compact portrait of you, built from your own sessions |
> | [animus-brief](https://github.com/IvanStrazov/animus-brief) | One status brief across all your projects |
> | [animus-limits](https://github.com/IvanStrazov/animus-limits) | Token spend per task, per-task limits, cost estimates |
> | [animus-relay](https://github.com/IvanStrazov/animus-relay) | Hand work over to a fresh session without losing the thread |
> | [animus-review](https://github.com/IvanStrazov/animus-review) | Send work to another model for review, triage the answer |
>
> The name nods to the memory machine from Assassin's Creed and to the Latin *animus*, "mind". Not affiliated with Ubisoft.

## Install

```
/plugin marketplace add IvanStrazov/animus-relay
/plugin install animus-relay@animus-relay
```

Then say `/relay`. Requires Python 3.9+ on `PATH` (`python3` or `python`); works on macOS, Linux and Windows (Git Bash).

## What you get

**Old session** — say "hand this over to a new session" or `/relay`. Claude gathers git state, `STATE.md` and recent journal entries, then writes a short handoff (≤ 120 lines): goal, where we are, decisions, **the approvals you gave and their scope**, open questions, the exact next step, key files, gotchas, what not to redo.

**New session** — opens in the same project and sees one line: `[relay] handoff waiting: "…"`. Claude takes it, tells you in 2–3 lines what it understood, and continues once you agree.

Handoffs live in `<project>/.journal/relay/` (or `~/journal/relay/` without a project), next to [animus-journal](https://github.com/IvanStrazov/animus-journal) and git-ignored. Taken ones move to `relay/taken/`.

**Safe to close?** Say "we're done" or "can I delete this session?" and Claude runs `relay.py check`: every git repo in the session folder and below is checked for uncommitted, untracked, unpushed or stashed work, and, in a temporary session folder, files that live in no repo and would vanish with it. You get `SAFE to close` or a list of what to fix first. Nothing is committed or pushed without your yes.

Unlike handoff tools that summarise automatically before compaction, a relay is written on purpose and carries what a summary loses: decisions with reasons, approvals with scope, dead ends.

## Token budget

| Moment | Cost |
|---|---|
| Session start, nothing waiting | 0 — the hook prints nothing |
| Session start, a handoff waiting | one line per handoff (≈ 30 tokens) |
| Taking a handoff | the handoff itself (≤ 120 lines) |

## Commands

```
relay.py gather              # facts for writing a handoff
relay.py save --title T      # stdin -> handoff
relay.py take [FILE]         # print the newest waiting handoff, mark it taken
relay.py list
relay.py check [PATH]       # safe to close/delete? exit 1 if work would be lost
```

## Privacy

Everything stays on your machine: plain Markdown and JSON files, no network, no database, one stdlib Python script.

## License

MIT
