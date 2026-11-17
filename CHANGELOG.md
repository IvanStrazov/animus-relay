# Changelog

## 0.4.0 — 2026-11-17
- Fix: `take` picked the alphabetically last handoff when two were saved in the same minute; now the newest by save time.
- New `show [file]` (print without taking) and `drop <file>` (delete a test or mistaken handoff); file names can be given by prefix.
- `save` refuses a body without a `Next step:` line (`--force` overrides). Skill: run `check` first when asked whether it is safe to close. Same inside-a-journal rule as animus-journal.

## 0.3.1 — 2026-11-17
- Skill: a taken handoff is no longer waiting; continue it later with `list` + `take <file>` or save a fresh one.

## 0.3.0 — 2026-11-17
- `check`: in a kept folder nothing is deleted with the session, so uncommitted/unpushed/stashed work is shown as `!` (not backed up yet) and the verdict is SAFE; ✗ blockers remain for temporary session folders.
- `gather` shows stash and unpushed commits, and says when the journal has no entries yet.
- Skill: record the journal entry with a handoff without asking; accept a user's "no push" without repeating it; Windows interpreter from ecosystem.json.

## 0.2.2 — 2026-11-17
- Skill: not even part of a secret (a token prefix) goes into a handoff; guesses are marked as hypotheses; a handoff is corrected by saving a new one, never edited by hand.
- Skill: on pick-up the user's own request comes before the confirmation.
- Handoff file names are cut at a word boundary.

## 0.2.1 — 2026-11-17
- `check`: a repo with no remote is only a note when the folder is kept (closing a session does not delete it); still a blocker in a temporary session folder.
- Skill: on pick-up, confirm the handoff in 2–3 short lines before any other tool call.

## 0.2.0 — 2026-11-17
- `check`: is it safe to close or delete this session? Checks every git repo in the folder and below (uncommitted, untracked, unpushed, no upstream, no remote, stash) and, in a temporary session folder, files in no repo. Exit 1 when work would be lost.
- The skill runs it when you say you are done with a session.

## 0.1.0 — 2026-11-17
- First release, part of the Animus ecosystem.
