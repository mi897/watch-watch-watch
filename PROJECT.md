# PROJECT.md: what's where

A map of the repository. Update this file whenever files or directories are added, moved or removed.

## Current state
Phase 2 (compose + bootstrap). Pinned Jellyfin stack and idempotent `bootstrap` command. Phase status is tracked in `docs/PLAN.md` §3.

## Top level
| Path | Purpose |
|------|---------|
| `README.md` | Short project summary and status |
| `CLAUDE.md` | Rules and workflow for AI assistants (branching, PRs, hard rules) |
| `PROJECT.md` | This map |
| `LICENSE` | Apache-2.0 |
| `CONTRIBUTING.md` | Human contributor guide |
| `SECURITY.md` | Vulnerability reporting and security stance |
| `compose.yaml` | Jellyfin (pinned, media `:ro`, loopback) and the one-shot `bootstrap` service |
| `.env.example` | Example secrets/env file (copy to `.env`, git-ignored) |
| `config.example.yml` | Example config (copy to `config.yml`, git-ignored) |
| `.pre-commit-config.yaml` | ruff and gitleaks hooks |
| `.gitignore` | Keeps secrets, real configs, data dirs and media out of git |

## docs/
| File | Purpose |
|------|---------|
| `docs/REQUIREMENTS.md` | Refined requirements, hard rules as testable checks, gaps and risks |
| `docs/PLAN.md` | Architecture, repo layout, phases with acceptance criteria, testing approach, resolved decisions |
| `docs/BOOTSTRAP.md` | What bootstrap does, how to run it, passwords, verified Jellyfin version |
| `docs/LICENSING.md` | Why Apache-2.0 is compatible with Jellyfin and the other components |

## companion/
| Path | Purpose |
|------|---------|
| `companion/pyproject.toml` | Package metadata, ruff/mypy/pytest config |
| `companion/Dockerfile` | Companion image |
| `companion/src/companion/config/` | Config schema and loader |
| `companion/src/companion/jellyfin/` | Jellyfin REST client |
| `companion/src/companion/bootstrap/` | Reconcile config to Jellyfin |
| `companion/src/companion/cli.py` | `watch-companion bootstrap` |
| `companion/tests/unit/` | Unit tests |
| `companion/tests/integration/` | Live-Jellyfin tests (`pytest -m integration`, needs `JELLYFIN_TEST_URL`, `JELLYFIN_TEST_MEDIA`) |

## scripts/ and .github/
| Path | Purpose |
|------|---------|
| `scripts/check-repo-hygiene.sh` | Fails if real configs/keys are tracked or compose images are unpinned |
| `.github/workflows/ci.yml` | CI: ruff, mypy, pytest, hygiene script, gitleaks |

## Commands
- Dev setup: `cd companion && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`
- Fast checks (in `companion/`): `ruff check . && ruff format --check . && mypy && pytest`
- Integration (needs a fresh Jellyfin): `JELLYFIN_TEST_URL=http://127.0.0.1:8096 JELLYFIN_TEST_MEDIA=/abs/path pytest -m integration`
- From repo root: `scripts/check-repo-hygiene.sh`

## Still planned
Defined in `docs/PLAN.md` §2: more `docs/` guides, and the companion modules.

## Phases
| Phase | Branch | Summary |
|-------|--------|---------|
| 0 | `phase-0-planning` | Requirements, plan, licensing, project docs |
| 1 | `phase-1-scaffolding` | Repo scaffolding, example configs, CI |
| 2 | `phase-2-compose-bootstrap` | Compose stack, config loader, Jellyfin client, bootstrap |
| 3+ | see `docs/PLAN.md` | Doctor, review queue, missing episodes, recommendations, hardening |
