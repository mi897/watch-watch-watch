# PROJECT.md: what's where

A map of the repository. Update this file whenever files or directories are added, moved or removed.

## Current state
Phase 0 (planning). Docs only; no code yet. Phase status is tracked in `docs/PLAN.md` §3.

## Top level
| Path | Purpose |
|------|---------|
| `README.md` | Short project summary and status |
| `CLAUDE.md` | Rules and workflow for AI assistants (branching, PRs, hard rules) |
| `PROJECT.md` | This map |
| `LICENSE` | Apache-2.0 |
| `.gitignore` | Keeps secrets, real configs, data dirs and media out of git |

## docs/
| File | Purpose |
|------|---------|
| `docs/REQUIREMENTS.md` | Refined requirements, hard rules as testable checks, gaps and risks |
| `docs/PLAN.md` | Architecture, repo layout, phases with acceptance criteria, testing approach, resolved decisions |
| `docs/LICENSING.md` | Why Apache-2.0 is compatible with Jellyfin and the other components |

## Planned layout (not created yet)
Defined in `docs/PLAN.md` §2: `companion/` (Python service), `compose*.yaml`, more `docs/` guides, `scripts/`, `.github/workflows/`.

## Phases
| Phase | Branch | Summary |
|-------|--------|---------|
| 0 | `phase-0-planning` | Requirements, plan, licensing, project docs |
| 1 | `phase-1-scaffolding` | Repo scaffolding, example configs, CI |
| 2+ | see `docs/PLAN.md` | Compose + bootstrap, doctor, review queue, missing episodes, recommendations, hardening |
