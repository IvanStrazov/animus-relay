---
name: relay
description: Hand the current work over to a fresh Claude Code session without losing the thread — when the context has grown too big, before a restart, or to continue tomorrow; and pick a waiting handoff up in the new session. Use on /relay, "save the context and restart", "hand this over to a new session", "continue from the handoff", when the start-of-session context shows a `[relay] handoff waiting` line, or when the user wants to close, end or delete the session ("we're done", "заканчиваем", "can I delete this session?").
---

# Relay

`R` = `python3 "<plugin root>/scripts/relay.py"`, where the plugin root is two levels above this skill's base directory (`python` if `python3` is missing). On Windows, `python3`/`python` may be Microsoft Store stubs: then use the interpreter and script path from this plugin's `cmd` in `~/.claude/ecosystem.json` (or a start-of-session line), and write paths with forward slashes so a trailing `\` does not eat the closing quote. The start-of-session line, when present, shows the exact command.

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
   Facts only, ≤ 120 lines. No secrets — not even part of one (a token prefix, the first characters of a key, a masked password): name the file or env var they live in instead. Mark guesses as "hypothesis".
   A saved handoff is never edited by hand: to correct it, `R save` a new one (the newest one is what `take` picks up). Never cat/edit/delete files under `.journal/relay/`.
3. If animus-journal is installed and the session did real work, record it in the same turn without asking (a handoff means the work matters).
4. Tell the user, in their language, the line the script printed for the new session, and that the next session in this project will see the handoff automatically.

## Before closing or deleting a session
When the user wants to end, close or delete the session: run `R check` (in the session's working folder). It checks every git repo there and below for uncommitted, untracked, unpushed or stashed work, and, in a temporary session folder, files that live in no repo and would be deleted with the session.
- `NOT SAFE` (exit 1): list the ✗ lines in the user's language and offer to fix them (commit, push, move the files to a kept folder). Never commit, push or move anything without the user's yes. Run `R check` again after fixing.
- `SAFE` with `!` lines (a kept folder: nothing is lost by closing, but there is no copy elsewhere): say it is safe to close and list the `!` lines once; offer commit/push only if the user wants a copy, and accept "no" (e.g. pushes need review) without repeating it.
- `SAFE`: say so; mention the `·` notes (no journal entry, no handoff) only if the work continues.

## Picking up (new session)
When the context shows `[relay] handoff waiting`, or the user asks to continue: run `R take` (it prints the newest handoff and marks it taken). Read it, then — before any other tool call, unless the user's message asks for something else first — confirm in 2–3 short lines what you understood and the next step, and continue only once the user agrees, unless the handoff says the user already approved that step.
User approvals carried in a handoff apply only in the scope written there.

`R list` shows waiting and taken handoffs; `R take <file>` reopens a specific one. A taken handoff is not "waiting" any more (`check` will say so): to continue it in a later session, tell the user to ask for it and use `R list` + `R take <file>`, or save a fresh handoff at the end of this session.
