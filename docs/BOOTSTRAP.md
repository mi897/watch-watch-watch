# Bootstrap (Phase 2)

`bootstrap` turns `config.yml` into a configured Jellyfin through its public API. It is safe to re-run: the second run changes nothing.

## Use
```
cp .env.example .env            # set MEDIA_DIR, PUID, PGID (and admin passwords, optionally)
cp config.example.yml config.yml
mkdir -p data/jellyfin/config data/jellyfin/cache data/companion
docker compose up -d jellyfin
docker compose run --rm bootstrap
```
Jellyfin is then at <http://127.0.0.1:8096> (loopback only by default).

## What it does
1. Checks `media_root` and each library folder exist and are readable *inside the container*. A wrong path stops with a clear message before anything is changed.
2. Fresh Jellyfin: completes the startup wizard and creates the first admin.
3. Creates one library per entry under `libraries` (Movies, Shows, Anime, Cartoons) with every option that writes into the media folders switched off: `SaveLocalMetadata` (NFO and artwork), `MetadataSavers`, `SaveSubtitlesWithMedia`, `SaveLyricsWithMedia`, `SaveTrickplayWithMedia`. Sets metadata language and country.
4. Creates users from `config.yml`; sets admin flag, optional `max_rating`, optional `libraries` restriction.
5. Creates an API key named `watch-companion` and saves it to `data/companion/jellyfin_api_key` (mode 0600).

Existing users and libraries not in the config are left alone. Libraries whose path differs from the config are reported as `drift` and not changed.

## Passwords
A user's password comes from the env var named by `password_env`. If it is empty, bootstrap generates one, prints it **once**, and does not store it. Existing users' passwords are never changed.

## Re-runs and credentials
After the first run, bootstrap authenticates with `JELLYFIN_API_KEY` (env) or the saved key file, falling back to an admin's `password_env`.

## Verified against
Jellyfin **12.4.0** (image `12.4.20261026-211555`, digest pinned in `compose.yaml`), checked against its published OpenAPI spec and a live container. Jellyfin 12.x migrates its database on first start and later versions cannot read it back, so back up `data/jellyfin` before changing the pinned version.

## Not in this phase
Plugins (Phase 3), `doctor` (Phase 3).
