---
name: relay
description: Hand the current work over to a fresh Claude Code session without losing the thread — when the context has grown too big, before a restart, or to continue tomorrow; and pick a waiting handoff up in the new session. Use on /relay, "save the context and restart", "hand this over to a new session", "continue from the handoff", or when the start-of-session context shows a `[relay] handoff waiting` line.
---

# Relay

`R` = `python3 "<plugin root>/scripts/relay.py"`, where the plugin root is two levels above this skill's base directory (`python` on Windows if `python3` is missing). The start-of-session line, when present, shows the exact command.

## Handing over (old session)
1. `R gather` — git state, STATE.md, recent journal entries. Do not re-read files you already know.
2. Write the handoff from this conversation and those facts, then save it in one call:
```bash
R save --title "Short title of the work" <<'EOF'
# Short title of the work
Goal: what we are trying to achieve, in one or two lines
Where we are: the current state, honestly (what works, what does not)
Done this session: files, commits, results
Decisions: X because Y (only ones the next session must not reopen)
User approvals: what the user allowed and its scope (e.g. "may restart the server", "no purchases")
Open questions: what is undecided, who decides
Next step: the exact first action, with file/command
Key files: path — why it matters
Gotchas: traps already hit, things that look right but are not
Do not redo: checks or searches already done, with their result
EOF
```
   Facts only, ≤ 120 lines, no secrets (keys, passwords, tokens): name the file they live in instead.
3. If animus-journal is installed, record the session as usual.
4. Tell the user, in their language, the line the script printed for the new session, and that the next session in this project will see the handoff automatically.

## Picking up (new session)
When the context shows `[relay] handoff waiting`, or the user asks to continue: run `R take` (it prints the newest handoff and marks it taken). Read it, then confirm in 2–3 lines what you understood and the next step, and continue only once the user agrees, unless the handoff says the user already approved that step.
User approvals carried in a handoff apply only in the scope written there.

`R list` shows waiting and taken handoffs; `R take <file>` reopens a specific one.
