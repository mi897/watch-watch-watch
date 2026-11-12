# Requirements

Status: **DRAFT, awaiting user approval.** No code exists yet. Items marked **[VERIFY]** are from memory and must be checked against current upstream docs before relying on them. Items marked **[DECISION]** need a user answer (see `PLAN.md` §9).

## 1. Vision

A public, open-source, self-hosted "personal Netflix". Someone with a folder of mp4/mkv files (movies, TV, anime, cartoons) of messy provenance should be able to point the system at it, create admin accounts, and watch from any device on their local or trusted network.

**Target experience:** clone, copy `.env.example` and `config.example.yml`, set a few values, `docker compose up -d`, done.

## 2. Principles

- Build on Jellyfin. Do not write a streaming server.
- Our code is a thin companion layer. It talks to Jellyfin only through the public API and never reads or writes Jellyfin's database.
- Media is read-only everywhere by default. Nothing we ship renames, moves, deletes or writes into the media tree.
- Nothing is exposed to the internet. Nothing phones home.
- Everything is idempotent and documented for a stranger.

## 3. Hard rules (from the brief, restated as testable requirements)

| ID | Rule | How we check it |
|----|------|-----------------|
| H1 | No secrets or real configs in git. Only `*.example` files. | `.gitignore` from first commit; CI runs a secret scanner (gitleaks) and fails if a tracked file matches `.env`, `config.yml`, or a known data dir. |
| H2 | Media files are never modified. | Compose mounts media `:ro` for every container. A test asserts no compose service mounts the media root read-write. Any future write feature is opt-in, documented and reversible. |
| H3 | No telemetry from our code. | Code review rule; companion makes outbound calls only to Jellyfin and user-configured providers (TMDB etc.). Documented list of every outbound host. Jellyfin's own update checks are documented and can be disabled. |
| H4 | Safe defaults. | Ports bind to `127.0.0.1` by default; LAN binding is an explicit one-line change. No default passwords: admin passwords are user-supplied or generated and shown once. |
| H5 | Idempotent bootstrap. | Integration test runs bootstrap twice against a real Jellyfin container and asserts the second run makes no changes. |
| H6 | Documented well enough for a stranger. | Docs are an acceptance criterion in every phase. |
| H7 | Pinned third-party images, documented upgrades. | Compose uses explicit tags (digest-pinned at release). CI fails on `:latest`. `docs/UPGRADING.md`. |

## 4. Functional requirements

### 4.1 Setup and provisioning (MVP)

- **F1** Config: a single `config.yml` (from `config.example.yml`) with `media_root`, optional per-type subfolders (`movies`, `shows`, `anime`, `cartoons`), a list of admin accounts, and optional user accounts. Secrets (API keys, passwords) come from `.env`/environment, not the YAML. Config is validated with clear error messages.
- **F2** A `bootstrap` command provisions Jellyfin via its API: complete the startup wizard, create admin users, create libraries per media type, set metadata language and country, install/enable chosen plugins, create an API key for the companion. **[VERIFY]** exact endpoints (`/Startup/*`, `/Library/VirtualFolders`, `/Auth/Keys`, `/Packages/Installed/{name}`, `/Plugins`) and per-version differences for the pinned Jellyfin version. Some plugin installs require a Jellyfin restart; bootstrap must handle that.
- **F3** Library creation must disable features that write into the media folders: NFO savers, "save artwork into media folders", subtitle download to media folder, and any similar options. **[VERIFY]** the full list for the pinned version. Without this, a `:ro` mount breaks Jellyfin or silently degrades it.
- **F4** `doctor` command: checks media path exists and is readable, the container user can read it, mount is read-only, Jellyfin reachable and version supported, API key valid, libraries exist and have scanned, provider keys valid, ports bound as intended, disk space for Jellyfin cache/transcode dirs. Machine-readable (`--json`) and human output, nonzero exit on failure.
- **F5** Bootstrap generates admin passwords when none are supplied, prints them once, never writes them to logs or disk. **[DECISION]** whether to also offer "write to a 0600 file in the data dir".
- **F6** Bootstrap converges state: it reconciles config to Jellyfin (add missing, report drift) and does not delete users/libraries that are absent from config unless `--prune` is passed.

### 4.2 Users and profiles

- **F7** Multiple admins and regular users, created from config or later. Each has separate watch history, progress and recommendations (provided by Jellyfin natively).
- **F8** Optional restrictions per user: max content rating, hide libraries (e.g. kids see only cartoons). Configurable per user in `config.yml`.
- **F9** Jellyfin's auth is the only auth. The companion authenticates users by validating their Jellyfin session token, and has its own service API key for server-to-server calls. **[VERIFY]** best token validation approach.

### 4.3 Library organization and matching

- **F10** Docs: recommended folder/naming convention (Jellyfin's own, plus anime notes). Not required.
- **F11** Review queue: the companion lists items that are unmatched or low-confidence. Signals: no provider ID, Jellyfin guessed from filename only, `guessit` result disagrees with Jellyfin's match (title/year/season/episode), duplicate episode numbers, absolute-vs-season numbering mismatch.
- **F12** Fixing a match applies it through Jellyfin's identify/update API and stores the decision in the companion DB keyed by a **file fingerprint** (size + hash of first/last 1 MiB + duration), not by path. If the file is renamed or moved the fix is re-applied after the next scan. Full-file hashing is rejected as too slow on NAS-class hardware.
- **F13** Anime: documented plugin set (AniList/AniDB/AniSearch, plus Jellyfin plugin repos the user must trust) and guidance for absolute numbering. Honest scope: Jellyfin's anime handling is weaker than Sonarr's. We document the limits and use the review queue to patch, rather than promise perfect results. **[VERIFY]** which anime plugins are currently maintained and compatible with the pinned Jellyfin.

### 4.4 Missing and new episodes

- **F14** For each series in the library, compute episodes that have aired but are not present, using TMDB (and AniList for anime) air dates compared to Jellyfin's item list. Per library and per user (users who have watched or favorited a series).
- **F15** Notifications v1: in-app badge/list plus a generic outgoing webhook (works with ntfy, Discord, Gotify, Home Assistant, etc.). Email is a later phase. **[DECISION]**
- **F16** Sonarr/Radarr: **recommendation is to not bundle them in v1** and use our own logic (F14). Reasons: Sonarr/Radarr want a writable root folder (they health-warn on read-only) and try to manage files, which conflicts with H2; they add two more services and API-key wiring for a use that is only "compare aired vs present"; Jellyfin plus TMDB already has what is needed. Revisit as an optional compose profile if users ask. **[DECISION: this deviates from the brief's default, so it needs explicit user sign-off.]**

### 4.5 Recommendations

- **F17** Per-user, content-based: build a taste profile from the user's watched/rated/favorited items (genres, keywords, cast/crew, studio, language, decade) and rank unwatched library items, plus an optional "not in library yet" list from TMDB `recommendations`/`similar`. Explanations shown ("because you watched X").
- **F18** No collaborative filtering at this scale. Embeddings are a stretch goal, behind a flag, local-only (no external embedding API by default).
- **F19** Provider keys (TMDB etc.) are supplied by the user via `.env`; the doctor validates them. Attribution requirements shown in UI and README. **[VERIFY]** TMDB's current terms (non-commercial use, attribution wording, rate limits), AniList and Jikan rate limits.
- **F20** Cache provider responses locally (SQLite) to respect rate limits and run offline.

### 4.6 Devices and access

- **F21** Docs listing supported Jellyfin clients (web, Android/iOS, Android TV/Fire TV, Roku, Apple TV via Swiftfin/Infuse, LG/Samsung where available, Kodi) and how to connect.
- **F22** Docs for remote access via Tailscale and WireGuard. We ship no tunneling and no reverse proxy by default. Port-forwarding and public exposure are documented as discouraged.
- **F23** Local discovery (UDP 7359, DLNA) requires host networking; **off by default**, documented.

### 4.7 Companion UI

- **F24** Review queue, missing episodes and recommendations are in a small companion web UI (login via Jellyfin credentials). Links open items in Jellyfin. **[DECISION]** whether to also attempt a Jellyfin plugin (C#, separate toolchain, version-coupled) — recommendation is no.
- **F25** A setup web UI is **not** in MVP. Bootstrap is CLI/container only. **[DECISION]**

## 5. Non-functional requirements

- **N1** Linux primary (x86_64 and arm64). macOS and Windows through Docker Desktop, with a documented caveats page: path syntax, file-sharing permissions, slow bind mounts, no hardware transcoding passthrough, no host networking.
- **N2** Optional hardware transcoding (Intel QSV/VAAPI via `/dev/dri`, NVIDIA via container toolkit) as separate compose override files, off by default, documented.
- **N3** Runs on 2 cores / 2 GB RAM for the companion plus Jellyfin with direct play. Companion idle memory target under 150 MB. Scans are throttled and resumable.
- **N4** Open-source license: Apache-2.0 is already in the repo's `LICENSE`. **[DECISION]** confirm.
- **N5** Tests and CI on GitHub: lint, type check, unit, integration (Jellyfin container), compose validation, secret scan, image-tag pin check. Details in `PLAN.md`.
- **N6** Observability: structured logs (never including secrets), `/healthz` endpoint, `doctor` output usable in bug reports with secrets redacted.
- **N7** Compose files run containers as a non-root PUID/PGID, with `no-new-privileges` and dropped capabilities where the image allows.

## 6. Out of scope

Downloading or acquiring media, indexers/torrent/usenet clients, a custom player, our own transcoding, our own user database, public hosting, DRM handling, rename/move features (possible future opt-in).

## 7. Gaps and risks found while refining the brief

1. **Read-only media vs Jellyfin behavior.** Jellyfin can write NFOs, artwork, and trickplay next to media depending on settings. Need to confirm library defaults on the pinned version and disable them (F3). Trickplay/chapter images go to Jellyfin's data dir by default **[VERIFY]**.
2. **Sonarr/Radarr conflict with H2** (F16).
3. **Plugin installation is the weakest-automation area.** Plugins come from third-party repositories, need trust decisions, may need restarts, and break across Jellyfin releases. Plan: ship a pinned, tested plugin list and treat plugin installation as optional with clear failure messages.
4. **Anime numbering** (F13). Expect a manual review workload.
5. **Provider terms.** TMDB requires attribution and restricts commercial use. A public repo that ships no keys is fine; each user supplies their own.
6. **Jellyfin API drift.** Pin the Jellyfin version, run integration tests against it in CI, and add a scheduled CI job that tests the next release.
7. **Fingerprint cost on network mounts** (F12): need throttling and a cache keyed on (path, size, mtime).
8. **Auth in the companion UI.** We must not become a second auth system (F9). Validating Jellyfin tokens on each request has latency and failure modes; needs a short-lived cache.
9. **First-run timing.** Jellyfin takes time to start; the initial library scan can take hours on big libraries. Bootstrap must be re-entrant and `doctor` should report scan progress.

## 8. Success criteria for v1.0

A new user on a fresh Linux box with Docker and a media folder gets to a working, logged-in Jellyfin with correctly typed libraries in under 10 minutes of hands-on time, `doctor` passes, the review queue shows unmatched items, missing episodes are listed with a working webhook notification, recommendations render for at least one user, and no file under the media root has been modified (verified by checksum comparison in an end-to-end test).
