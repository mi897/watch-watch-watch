# Configuration

Two files, both git-ignored: `.env` (secrets and host settings) and `config.yml` (everything else). Copy from the `*.example` files.

## `.env`
| Variable | Meaning |
|----------|---------|
| `MEDIA_DIR` | Host path of your media; mounted read-only at `/media` |
| `PUID`, `PGID` | Numeric user and group the containers run as |
| `JELLYFIN_PORT` | Host port, bound to 127.0.0.1 (default 8096) |
| `ADMIN_PASSWORD_<NAME>` | Password for a configured user, named by that user's `password_env`. Blank means generate |
| `JELLYFIN_API_KEY` | Optional override; bootstrap normally saves its own key in `data/companion/` |
| `TMDB_API_KEY` | Your own TMDB key. Used from a later phase; `doctor` validates it |

## `config.yml`
| Key | Meaning |
|-----|---------|
| `media_root` | Media path inside the container (keep `/media`) |
| `server_name` | Jellyfin server name |
| `libraries` | Map of `movies`, `shows`, `anime`, `cartoons` to subfolder names. Omit what you lack |
| `metadata.language`, `metadata.country` | For example `en` and `US` |
| `users[]` | `name`, `admin`, `password_env`, optional `max_rating` (for example `PG`) and `libraries` (list of keys) |
| `plugins[]` | Optional: `name`, optional `version`, optional `repository_url` |

Unknown keys are rejected with the file and key named. `shows`, `anime` and `cartoons` are all Jellyfin "TV shows" libraries; `movies` is "Movies".

## Commands
- `docker compose run --rm bootstrap`: reconcile config into Jellyfin.
- `docker compose run --rm doctor [--json]`: health check; exits 1 on any `FAIL`. `--json` output has secrets redacted and is safe to paste into a bug report.

## Outbound connections
Our code contacts only Jellyfin and, if you set a key, TMDB (`api.themoviedb.org`, for the `doctor` key check now and for metadata later). No telemetry. Jellyfin itself can check for updates and fetch metadata; configure that in its admin dashboard.
