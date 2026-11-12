"""Idempotent reconcile of config.yml -> Jellyfin. Never touches media files."""

from __future__ import annotations

import copy
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from companion.config import LIBRARY_KINDS, Config, UserConfig
from companion.jellyfin import JellyfinClient, JellyfinError

KEY_FILE = "jellyfin_api_key"

# Library options that would make Jellyfin write into the (read-only) media folders.
NO_MEDIA_WRITES: dict[str, Any] = {
    "SaveLocalMetadata": False,  # NFO files and artwork next to media
    "MetadataSavers": [],
    "SaveSubtitlesWithMedia": False,
    "SaveLyricsWithMedia": False,
    "SaveTrickplayWithMedia": False,
}


class BootstrapError(Exception):
    """User-facing failure with a clear message."""


@dataclass
class Report:
    changes: list[str] = field(default_factory=list)
    drift: list[str] = field(default_factory=list)
    generated_passwords: dict[str, str] = field(default_factory=dict)
    api_key_created: bool = False


def _check_media(cfg: Config) -> None:
    root = Path(cfg.media_root)
    if not root.is_dir():
        raise BootstrapError(
            f"media_root '{cfg.media_root}' does not exist inside this container. "
            "Check the media mount in compose.yaml and media_root in config.yml."
        )
    for key in cfg.libraries:
        p = Path(cfg.library_path(key))
        if not p.is_dir():
            raise BootstrapError(
                f"library '{key}': folder '{p}' does not exist or is not a directory"
            )
        if not os.access(p, os.R_OK | os.X_OK):
            raise BootstrapError(f"library '{key}': folder '{p}' is not readable by this user")


def _read_key(data_dir: Path, env: Mapping[str, str]) -> str | None:
    if env.get("JELLYFIN_API_KEY"):
        return env["JELLYFIN_API_KEY"]
    f = data_dir / KEY_FILE
    return f.read_text().strip() if f.is_file() else None


def _write_key(data_dir: Path, key: str) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    f = data_dir / KEY_FILE
    fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(key + "\n")


def _password_for(u: UserConfig, env: Mapping[str, str], report: Report) -> str:
    if u.password_env and env.get(u.password_env):
        return env[u.password_env]
    pw = secrets.token_urlsafe(16)
    report.generated_passwords[u.name] = pw
    return pw


def _authenticate(jf: JellyfinClient, cfg: Config, env: Mapping[str, str], data_dir: Path) -> None:
    key = _read_key(data_dir, env)
    if key:
        jf.use_token(key)
        try:
            jf.get("/Auth/Keys")
            return
        except JellyfinError:
            pass  # stale key; fall back to admin login
    for u in cfg.users:
        if u.admin and u.password_env and env.get(u.password_env):
            try:
                jf.login(u.name, env[u.password_env])
                return
            except JellyfinError:
                continue
    raise BootstrapError(
        "Jellyfin is already set up but no working credentials were found. Provide "
        "JELLYFIN_API_KEY, or the password of an admin via its password_env variable."
    )


def _ensure_libraries(jf: JellyfinClient, cfg: Config, report: Report) -> dict[str, str]:
    """Returns library key -> Jellyfin item id."""
    existing = {f["Name"]: f for f in jf.virtual_folders()}
    ids: dict[str, str] = {}
    desired = {
        **NO_MEDIA_WRITES,
        "PreferredMetadataLanguage": cfg.metadata.language,
        "MetadataCountryCode": cfg.metadata.country,
    }
    for key in cfg.libraries:
        name, ctype = LIBRARY_KINDS[key]
        path = cfg.library_path(key)
        folder = existing.get(name)
        if folder is None:
            jf.add_library(name, ctype, path, desired)
            report.changes.append(f"created library {name} -> {path}")
            folder = next((f for f in jf.virtual_folders() if f["Name"] == name), None)
            if folder is None:
                raise BootstrapError(f"library {name} was created but is not listed")
        else:
            if path not in (folder.get("Locations") or []):
                report.drift.append(
                    f"library {name}: path {path} not among Jellyfin locations "
                    f"{folder.get('Locations')} (not changed)"
                )
            opts = copy.deepcopy(folder.get("LibraryOptions") or {})
            if any(opts.get(k) != v for k, v in desired.items()):
                opts.update(desired)
                jf.update_library_options(folder["ItemId"], opts)
                report.changes.append(f"updated options of library {name}")
        ids[key] = str(folder["ItemId"])
    return ids


def _ensure_users(
    jf: JellyfinClient,
    cfg: Config,
    env: Mapping[str, str],
    lib_ids: dict[str, str],
    report: Report,
) -> None:
    ratings: dict[str, int] | None = None
    by_name = {u["Name"].lower(): u for u in jf.users()}
    for uc in cfg.users:
        user = by_name.get(uc.name.lower())
        if user is None:
            user = jf.create_user(uc.name, _password_for(uc, env, report))
            report.changes.append(f"created user {uc.name}")
        policy = copy.deepcopy(user.get("Policy") or {})
        want: dict[str, Any] = {"IsAdministrator": uc.admin}
        if uc.max_rating:
            if ratings is None:
                ratings = jf.parental_ratings()
            if uc.max_rating.upper() not in ratings:
                raise BootstrapError(
                    f"user {uc.name}: unknown max_rating '{uc.max_rating}'. "
                    f"Known: {', '.join(sorted(ratings))}"
                )
            want["MaxParentalRating"] = ratings[uc.max_rating.upper()]
        if uc.libraries is not None:
            want["EnableAllFolders"] = False
            want["EnabledFolders"] = sorted(lib_ids[k] for k in uc.libraries)
        current = {k: policy.get(k) for k in want}
        if "EnabledFolders" in current and current["EnabledFolders"] is not None:
            current["EnabledFolders"] = sorted(current["EnabledFolders"])
        if current != want:
            policy.update(want)
            jf.set_policy(str(user["Id"]), policy)
            report.changes.append(f"updated policy of user {uc.name}")


def run_bootstrap(
    cfg: Config,
    jf: JellyfinClient,
    *,
    env: Mapping[str, str],
    data_dir: Path,
    wait: float = 120,
) -> Report:
    report = Report()
    _check_media(cfg)
    info = jf.wait_ready(wait)

    if not info.get("StartupWizardCompleted"):
        first = next(u for u in cfg.users if u.admin)
        pw = _password_for(first, env, report)
        jf.startup_configure(cfg.server_name, cfg.metadata.language, cfg.metadata.country)
        jf.startup_create_user(first.name, pw)
        jf.startup_finish()
        jf.login(first.name, pw)
        report.changes.append(f"completed startup wizard; created admin {first.name}")
    else:
        _authenticate(jf, cfg, env, data_dir)

    lib_ids = _ensure_libraries(jf, cfg, report)
    _ensure_users(jf, cfg, env, lib_ids, report)

    key = jf.api_key()
    if key is None:
        key = jf.create_api_key()
        report.api_key_created = True
        report.changes.append("created companion API key")
    if _read_key(data_dir, {}) != key:
        _write_key(data_dir, key)
        report.changes.append(f"saved API key to {data_dir / KEY_FILE}")
    return report
