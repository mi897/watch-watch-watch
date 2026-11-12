# Plan

Status: **APPROVED.** Recommendations accepted; v1 is kept deliberately simple. Phases 1+ are in progress or pending. When the plan changes, update this file first.

## 1. Architecture

```
                 LAN / Tailscale / WireGuard (user-managed)
                               │
        ┌──────────────────────┼───────────────────────┐
        │                      │                       │
   Jellyfin clients      Companion web UI         (optional) webhooks out
 (web, mobile, TV)       review / missing / recs   ntfy, Discord, ...
        │                      │
        ▼                      ▼
 ┌─────────────┐  REST   ┌───────────────────────────┐   HTTPS   ┌─────────┐
 │  Jellyfin   │◄────────│ companion (FastAPI)       │──────────►│ TMDB    │
 │  (pinned)   │         │  - api + UI               │           │ AniList │
 └─────┬───────┘         │  - worker (scan, hash,    │           └─────────┘
       │                 │    sync, notify)          │
       │ :ro             │  - SQLite (decisions,     │
       ▼                 │    fingerprints, cache)   │
 ┌─────────────┐   :ro   └───────────┬───────────────┘
 │ media root  │◄────────────────────┘
 └─────────────┘
 bootstrap (one-shot container / CLI of the same image): config.yml → Jellyfin API
```

Key choices (each is a proposal, see §9 for the ones needing your answer):

- **One companion image, three entry points:** `serve` (API + UI), `worker` (background jobs), `bootstrap`/`doctor` (CLI). Same codebase, one Docker image. Worker and API can run in one process for v1.
- **Python 3.12, FastAPI, SQLAlchemy + SQLite (WAL), Alembic.** Reason: `guessit` is Python, the work is I/O-bound, and SQLite fits a single-household deployment and a backup is one file. Postgres is not needed. Keep the SQLAlchemy layer so a switch stays possible.
- **UI:** server-rendered Jinja + HTMX, no JS build chain. Keeps contributions easy and the image small. Revisit if the UI outgrows it.
- **Jellyfin client:** thin typed wrapper around `httpx`, generated models from Jellyfin's published OpenAPI spec for the pinned version **[VERIFY]**.
- **Filename parsing:** `guessit` as the primary parser, used only as a second opinion against Jellyfin's own match. Evaluate `PTN`/`anitopy` for anime in Phase 4 on a fixture corpus.
- **Fingerprint:** `sha256(size || first 1 MiB || last 1 MiB)` plus duration from Jellyfin. Cached by (path, size, mtime).
- **Providers:** TMDB (movies, TV, air dates, recommendations), AniList GraphQL for anime. Jikan only if AniList is insufficient. Each behind a small interface with a recorded-response test double.
- **Security:** companion binds to `127.0.0.1` by default; sessions validated against Jellyfin; CSRF protection on forms; secrets only from env; log redaction filter.

## 2. Repo layout

```
.
├── README.md  LICENSE  CONTRIBUTING.md  SECURITY.md  CHANGELOG.md
├── .gitignore  .env.example  config.example.yml
├── compose.yaml                  # core stack: jellyfin + companion
├── compose.lan.yaml              # opt-in LAN binding
├── compose.hwaccel-vaapi.yaml    # opt-in
├── compose.hwaccel-nvidia.yaml   # opt-in
├── docs/
│   ├── REQUIREMENTS.md  PLAN.md
│   ├── QUICKSTART.md  CONFIGURATION.md  NAMING.md  ANIME.md
│   ├── REMOTE-ACCESS.md  DEVICES.md  HARDWARE-TRANSCODING.md
│   ├── PLATFORMS.md (macOS/Windows)  UPGRADING.md  TROUBLESHOOTING.md
├── companion/
│   ├── pyproject.toml  Dockerfile
│   ├── src/companion/
│   │   ├── config/        # pydantic settings, schema, validation
│   │   ├── jellyfin/      # API client, models
│   │   ├── bootstrap/     # reconcile config → Jellyfin
│   │   ├── doctor/        # checks
│   │   ├── matching/      # guessit, confidence, review queue, fingerprints
│   │   ├── episodes/      # missing/new computation, notifications
│   │   ├── recs/          # taste profile, ranking
│   │   ├── providers/     # tmdb, anilist, cache
│   │   ├── web/           # routes, templates
│   │   └── db/            # models, migrations
│   └── tests/{unit,integration,e2e,fixtures}
├── scripts/                      # small shell helpers (dev only)
└── .github/workflows/            # ci.yml, nightly-jellyfin-next.yml, release.yml
```

## 3. Phases and acceptance criteria

"No-media" means testable without real video. Tests use empty/stub files with realistic names (Jellyfin can scan names without decoding), plus tiny generated clips (ffmpeg `testsrc`, a few seconds) where probing matters.

### Phase 0, scaffolding (this step, now)
`docs/`, `.gitignore`, README stub. **Acceptance:** you approve requirements, plan and open-question answers.

### Phase 1, repo scaffolding and CI
LICENSE confirmed, CONTRIBUTING, SECURITY, `.env.example`, `config.example.yml`, Python project skeleton, lint (ruff), types (mypy), pytest, pre-commit, gitleaks, CI skeleton.
**Acceptance:** CI green on an empty-but-wired project; secret scan and `:latest` check both demonstrably fail on a deliberate bad commit (in a throwaway branch); no real config tracked. **No-media.**

### Phase 2, compose stack and idempotent bootstrap
Compose with pinned Jellyfin, media `:ro`, loopback binding. Config loader. Jellyfin client. `bootstrap`: wizard, admins, libraries (with write-to-media features disabled), metadata language, API key. Generated passwords shown once.
**Acceptance:** from a clean checkout, `docker compose up` + `bootstrap` gives a logged-in-able Jellyfin with the configured libraries; second run is a no-op (test asserts zero mutating calls); wrong media path gives a clear error; checksum of the media tree unchanged. Integration test in CI against the pinned Jellyfin image. **No-media** (stub files).

### Phase 3, doctor, docs, optional extras
`doctor` with the F4 checks and `--json`. QUICKSTART, CONFIGURATION, NAMING, REMOTE-ACCESS, DEVICES, PLATFORMS, HARDWARE-TRANSCODING docs. Optional plugin install (pinned list, restarts handled). Sonarr/Radarr are dropped from v1 (decision in §9).
**Acceptance:** each doctor check has a passing and failing test; a reviewer who has never seen the project completes QUICKSTART on Linux without help (your or a volunteer's dry run). **Mostly no-media.**

### Phase 4, matching review queue
Companion DB + migrations, scan job reading Jellyfin items, `guessit` second opinion, confidence scoring, fingerprinting, review UI with search/identify/apply, persisted decisions re-applied after rename.
**Acceptance:** on a fixture corpus of ~300 messy filenames (scene, fansub, multi-episode, year-in-title, absolute-numbered anime) the queue flags a pre-agreed set of known-bad cases with at most an agreed false-positive rate; a recorded fix survives a rename and a move in the integration test; no media write. **Needs a handful of real tiny clips** for fingerprint tests, generated by ffmpeg in CI.

### Phase 5, missing and new episodes
TMDB and AniList providers, caching and rate limiting, missing computation per library and per user, in-app list/badge, webhook notifier with retry and dedupe (notify once per episode).
**Acceptance:** with recorded provider fixtures, known gaps are reported exactly; an episode airing "tomorrow" fires exactly one webhook when its air date passes (clock injected); webhook payload documented; provider outage degrades gracefully. **No-media.**

### Phase 6, recommendations
Taste profile, content-based ranking, in-library and not-in-library lists, explanations, per-user isolation.
**Acceptance:** golden-file tests on a synthetic watch history produce the expected top-N; two users with different histories get different lists; works offline from cache; a user never sees another user's data (test). **No-media.**

### Phase 7, hardening and release
Security review (threat model for the companion UI, SSRF on webhook URLs, CSRF, session handling), dependency audit, SBOM, image signing optional, upgrade guide tested (N to N+1), release workflow, versioning policy, contribution guide, issue templates, nightly test against next Jellyfin release.
**Acceptance:** v1.0 success criteria in `REQUIREMENTS.md` §8 met; upgrade test passes; docs reviewed by someone other than the author.

## 4. Testing approach

- **Unit** (pure logic, fast): config validation, confidence scoring, missing-episode computation, taste profile, fingerprint, webhook payloads. Time and network injected.
- **Contract/recorded**: provider clients tested against recorded responses (VCR-style, secrets scrubbed) so CI needs no API keys.
- **Integration**: real pinned Jellyfin container in CI (GitHub service container or testcontainers) with a stub media tree. Covers bootstrap, idempotence, doctor, and identify/apply.
- **End to end**: compose up, bootstrap, scan, hit the companion UI with Playwright, assert media checksum unchanged.
- **Static**: ruff, mypy, hadolint, `docker compose config`, gitleaks, custom check for unpinned images and rw media mounts.
- **Nightly**: run integration against Jellyfin's newest release to catch API drift early.

## 5. Security notes

Companion and Jellyfin bind to loopback unless the LAN override file is used. Webhook URLs are user-configured and validated (scheme allowlist, block link-local/metadata addresses by default, with an opt-in for LAN targets because ntfy/Gotify often live there). API keys live in env or Docker secrets and are redacted from logs and `doctor` output. Containers run non-root with `no-new-privileges`. Dependabot/Renovate for pinned images and Python deps.

## 6. Upgrade and release process

SemVer for the companion. Jellyfin version is pinned in compose and recorded in `CHANGELOG.md`; bumping it requires green integration CI. `UPGRADING.md` covers: back up `data/`, pull, `bootstrap` (re-runnable), migrations run on start.

## 7. What I could not verify yet

I have not checked current Jellyfin, TMDB, AniList or Jikan docs in this session. Everything marked **[VERIFY]** in the requirements will be confirmed against upstream documentation (and against the pinned Jellyfin's OpenAPI spec) at the start of Phase 2, and I will report any deviation before building on it.

## 8. Principal risks (ranked)

1. Plugin/anime automation fragility.
2. Jellyfin writing near media despite `:ro` (breaks libraries or degrades silently).
3. Review-queue false positives making the feature noisy.
4. Windows/macOS bind-mount permission and performance problems.
5. API drift between Jellyfin releases.

## 9. Decisions (resolved)

All recommendations were approved by the project owner. "Keep v1 simple" is a standing constraint: when in doubt, cut scope.

1. **Name and license:** keep `watch-watch-watch` and Apache-2.0 (compatibility checked in `docs/LICENSING.md`).
2. **Stack:** Python 3.12, FastAPI, SQLite, Jinja/HTMX.
3. **Bootstrap:** CLI/container only. No setup web UI in v1.
4. **Sonarr/Radarr:** not in v1. Missing episodes use our own logic.
5. **Notifications:** in-app list plus generic webhook. Email later.
6. **Media mount:** read-only always in v1.
7. **Metadata:** TMDB and AniList, keys via `.env` only.
8. **Platforms:** Linux x86_64 tested first; arm64 built; macOS/Windows documented only.
9. **UI:** separate companion web UI, no Jellyfin plugin.
10. **Anime:** documented best effort plus review queue.
11. **Plugins:** third-party plugin repos are an opt-in, documented step.
12. **Branch:** work on `claude/new-session-uoe31j`.
