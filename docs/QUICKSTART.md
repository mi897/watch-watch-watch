# Quickstart

Goal: a working Jellyfin with your libraries in about 10 minutes. Linux with Docker (Compose v2) is the tested path; see [PLATFORMS.md](PLATFORMS.md) for macOS and Windows.

## 1. Get the files
```
git clone https://github.com/mi897/watch-watch-watch.git
cd watch-watch-watch
cp .env.example .env
cp config.example.yml config.yml
```

## 2. Edit `.env`
- `MEDIA_DIR`: absolute host path of your media folder (for example `/srv/media`).
- `PUID` / `PGID`: output of `id -u` and `id -g`. The user must be able to read your media.
- Optional: `ADMIN_PASSWORD_ALICE` (rename to match your user). Leave blank to have one generated.

## 3. Edit `config.yml`
- Inside the container your media is at `/media`. Keep `media_root: /media`.
- Under `libraries`, list only the subfolders you have (`movies`, `shows`, `anime`, `cartoons`). Names are relative to `MEDIA_DIR`.
- Under `users`, keep at least one `admin: true` user. See [CONFIGURATION.md](CONFIGURATION.md).

## 4. Start and provision
```
mkdir -p data/jellyfin/config data/jellyfin/cache data/companion
docker compose up -d jellyfin
docker compose run --rm bootstrap
```
Bootstrap prints any generated password **once**. Copy it now; it is not stored.

## 5. Check and watch
```
docker compose run --rm doctor
```
Fix anything marked `FAIL` (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)); `WARN` is informational. Then open <http://127.0.0.1:8096>, sign in, and give the first library scan time to finish (hours on big collections).

Jellyfin listens on loopback only. To reach it from other devices on your network, see [REMOTE-ACCESS.md](REMOTE-ACCESS.md). To connect phones and TVs, see [DEVICES.md](DEVICES.md).

## Re-running
`bootstrap` is safe to run again after editing `config.yml`; it only adds or fixes what differs.
