# Anime

Honest scope: Jellyfin's anime handling is weaker than dedicated tools. Expect some manual fixing; the review queue (Phase 4) exists for that.

## What helps
- Keep anime in its own library (`anime:` in `config.yml`).
- Use `Season 01` folders and `SxxExx` names. Absolute numbering (episode 143 of a long series) often needs renaming by you or manual identification.
- Optional metadata plugins (for example AniList) can improve matches. Install them with `plugins:` in `config.yml`.

## Plugins are code you choose to trust
- Plugins from Jellyfin's default repository are the lower-risk choice. Name one with `name:` only.
- A plugin from any other repository needs an explicit `repository_url:`. That adds the repository to your Jellyfin and installs code from its owner; review it first.
- Installing a plugin restarts Jellyfin once. Bootstrap handles that and is safe to re-run.
- Plugins can break when Jellyfin is upgraded. Check each plugin supports your Jellyfin version before upgrading.
- We have not tested any specific anime plugin set yet; this phase tested only the install mechanism.
