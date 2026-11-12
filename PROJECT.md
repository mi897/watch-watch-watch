# PROJECT.md: what's where

A map of the repository. Update this file whenever files or directories are added, moved or removed.

## Current state
Phase 1 (scaffolding). Skeleton, example configs and CI only; no features yet. Phase status is tracked in `docs/PLAN.md` §3.

## Top level
| Path | Purpose |
|------|---------|
| `README.md` | Short project summary and status |
| `CLAUDE.md` | Rules and workflow for AI assistants (branching, PRs, hard rules) |
| `PROJECT.md` | This map |
| `LICENSE` | Apache-2.0 |
| `CONTRIBUTING.md` | Human contributor guide |
| `SECURITY.md` | Vulnerability reporting and security stance |
| `.env.example` | Example secrets/env file (copy to `.env`, git-ignored) |
| `config.example.yml` | Example config (copy to `config.yml`, git-ignored) |
| `.pre-commit-config.yaml` | ruff and gitleaks hooks |
| `.gitignore` | Keeps secrets, real configs, data dirs and media out of git |

## docs/
| File | Purpose |
|------|---------|
| `docs/REQUIREMENTS.md` | Refined requirements, hard rules as testable checks, gaps and risks |
| `docs/PLAN.md` | Architecture, repo layout, phases with acceptance criteria, testing approach, resolved decisions |
| `docs/LICENSING.md` | Why Apache-2.0 is compatible with Jellyfin and the other components |

## companion/
| Path | Purpose |
|------|---------|
| `companion/pyproject.toml` | Package metadata, ruff/mypy/pytest config |
| `companion/src/companion/` | Python package (currently only `__init__.py`) |
| `companion/tests/unit/` | Unit tests |

## scripts/ and .github/
| Path | Purpose |
|------|---------|
| `scripts/check-repo-hygiene.sh` | Fails if real configs/keys are tracked or compose images are unpinned |
| `.github/workflows/ci.yml` | CI: ruff, mypy, pytest, hygiene script, gitleaks |

## Commands
- Dev setup: `cd companion && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`
- Fast checks (in `companion/`): `ruff check . && ruff format --check . && mypy && pytest`
- From repo root: `scripts/check-repo-hygiene.sh`

## Still planned
Defined in `docs/PLAN.md` §2: `compose*.yaml`, more `docs/` guides, and the companion modules.

## Phases
| Phase | Branch | Summary |
|-------|--------|---------|
| 0 | `phase-0-planning` | Requirements, plan, licensing, project docs |
| 1 | `phase-1-scaffolding` | Repo scaffolding, example configs, CI |
| 2+ | see `docs/PLAN.md` | Compose + bootstrap, doctor, review queue, missing episodes, recommendations, hardening |
