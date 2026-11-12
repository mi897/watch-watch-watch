# Troubleshooting

Start with `docker compose run --rm doctor`. For bug reports use `--json`; secrets are redacted, but still read it before posting.

| Symptom | Likely cause and fix |
|---------|----------------------|
| `doctor`: `media_path` FAIL | `MEDIA_DIR` wrong, or subfolders in `libraries` do not exist. Names are relative to `MEDIA_DIR` |
| `media_path`: not readable | `PUID`/`PGID` cannot read the media. Match the owner of the files |
| `media_readonly` FAIL | The media volume lost its `:ro`. Restore it in `compose.yaml` |
| `api_key` FAIL | Run `bootstrap` again. If Jellyfin was reset, delete `data/companion/jellyfin_api_key` first |
| `library_*` writes-into-media | Library options drifted; run `bootstrap` |
| `library_*` is scanning | Normal after first start; wait |
| bootstrap: "no working credentials" | Jellyfin is already set up. Set that admin's password env var, or `JELLYFIN_API_KEY` |
| bootstrap: plugin install failed | Wrong plugin name, or it lives in a third-party repo: add `repository_url` |
| `jellyfin_reachable` WARN | Jellyfin major version differs from the tested one |
| Forgot a generated password | Reset it in Jellyfin as an admin, or recreate the user |
