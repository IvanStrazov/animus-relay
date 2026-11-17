# Changelog

## 0.2.0 — 2026-11-17
- `check`: is it safe to close or delete this session? Checks every git repo in the folder and below (uncommitted, untracked, unpushed, no upstream, no remote, stash) and, in a temporary session folder, files in no repo. Exit 1 when work would be lost.
- The skill runs it when you say you are done with a session.

## 0.1.0 — 2026-11-17
- First release, part of the Animus ecosystem.
