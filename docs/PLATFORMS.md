# Platforms

Tested path: **Linux x86_64** with Docker Engine and Compose v2. The pinned Jellyfin image publishes arm64 as well; arm64 is not yet tested by us.

## macOS and Windows (Docker Desktop): documented, untested
- Use forward-slash host paths in `.env` (for example `MEDIA_DIR=/Users/me/Media`, or a WSL2 path on Windows). Run commands from WSL2 on Windows.
- Share the media folder with Docker Desktop (Settings, Resources, File sharing).
- `PUID`/`PGID` are mostly ignored by Docker Desktop's file sharing; permission errors usually mean the folder is not shared.
- Bind mounts are slower than on Linux, so library scans take longer. Keep `data/` on a fast local disk.
- No hardware transcoding passthrough and no host networking (no automatic discovery).
- `:ro` mounts are honoured; run `doctor` to confirm.
