# Changelog

## 0.2.1 — 2026-11-17
- `check`: a repo with no remote is only a note when the folder is kept (closing a session does not delete it); still a blocker in a temporary session folder.
- Skill: on pick-up, confirm the handoff in 2–3 short lines before any other tool call.

## 0.2.0 — 2026-11-17
- `check`: is it safe to close or delete this session? Checks every git repo in the folder and below (uncommitted, untracked, unpushed, no upstream, no remote, stash) and, in a temporary session folder, files in no repo. Exit 1 when work would be lost.
- The skill runs it when you say you are done with a session.

## 0.1.0 — 2026-11-17
- First release, part of the Animus ecosystem.
