# Contributing

- Read `docs/REQUIREMENTS.md` and `docs/PLAN.md` first. Keep v1 simple.
- Never commit secrets, real configs, databases or media. Only `*.example` files.
- Dependencies must be licence-compatible (`docs/LICENSING.md`).
- Dev setup: `cd companion && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`
- Before pushing: `ruff check . && ruff format . && mypy && pytest`, and `scripts/check-repo-hygiene.sh` from the repo root.
- Small commits with clear messages.
