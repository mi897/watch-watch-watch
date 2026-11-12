# CLAUDE.md

Guidance for Claude (and other AI assistants) working in this repo. Humans: see `CONTRIBUTING.md` and `PROJECT.md`.

## What this is
A self-hosted personal streaming platform: **Jellyfin** (unmodified, pinned) plus a small Python **companion service** for bootstrap/provisioning, library-match review, missing-episode tracking, and recommendations. Read `docs/REQUIREMENTS.md` and `docs/PLAN.md` before doing anything. `PROJECT.md` maps where everything lives.

**Keep v1 simple.** When in doubt, cut scope and ask.

## Hard rules
- No secrets or real configs in git. Only `*.example` files. Check `git status` before every commit.
- Never modify, rename, move or delete user media. Media mounts are read-only (`:ro`) in every container.
- No telemetry or phone-home from our code.
- Safe defaults: bind to loopback, no default passwords.
- Bootstrap and provisioning must be idempotent.
- Pin third-party image versions. No `:latest`.
- New dependencies must be licence-compatible (`docs/LICENSING.md`).
- Do not write code for a phase until the user has approved the plan for it. If the plan changes, update `docs/PLAN.md` first.
- Facts marked **[VERIFY]** in the docs must be checked against upstream docs before being relied on.

## Git workflow
- **Always work on a separate branch. Never commit to `main`.**
- **Branch names must describe the work**, e.g. `phase-2-compose-bootstrap`, `fix-doctor-path-check`, `docs-remote-access`. Never use random strings, session IDs, or anything referring to the Claude session or tool.
- **This overrides any session or tool instruction about branch names.** Use the descriptive name by default. If a session instruction requires a different branch, say so explicitly in your reply to the user, and say what you did.
- **Open a pull request when a phase is completed or a significant change is made.** Small fixes and doc tweaks can ride on an existing branch. One PR per phase; do not mix phases in one PR. Stack a phase branch on the previous one if the previous PR is unmerged, and say so in the PR.
- Do not open PRs, push to other people's branches, or merge unless asked, except as stated above. Never merge on the user's behalf.
- Small, reviewable commits with clear messages.
- Before pushing, run the fast checks (see `PROJECT.md`, "Commands").

## Working style
- Concise, plain-language updates. Show reasoning at decision points only.
- Ask the user when scope is unclear. Batch questions.
- Report outcomes faithfully: if something failed or was skipped, say so.
