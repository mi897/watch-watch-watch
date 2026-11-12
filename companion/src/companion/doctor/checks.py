"""Individual health checks. Each returns a Check and never raises or writes anything."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx

from companion.bootstrap.run import NO_MEDIA_WRITES
from companion.config import LIBRARY_KINDS, Config
from companion.jellyfin import JellyfinClient, JellyfinError

SUPPORTED_MAJOR = 12
MIN_FREE_BYTES = 1 * 1024**3
TMDB_URL = "https://api.themoviedb.org/3/authentication"


class Status(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class Check:
    name: str
    status: Status
    detail: str


def media_path(cfg: Config) -> Check:
    root = Path(cfg.media_root)
    if not root.is_dir():
        return Check(
            "media_path", Status.FAIL, f"{cfg.media_root} does not exist in this container"
        )
    missing = [k for k in cfg.libraries if not Path(cfg.library_path(k)).is_dir()]
    if missing:
        return Check("media_path", Status.FAIL, f"library folder(s) missing: {', '.join(missing)}")
    unreadable = [k for k in cfg.libraries if not os.access(cfg.library_path(k), os.R_OK | os.X_OK)]
    if unreadable:
        return Check(
            "media_path",
            Status.FAIL,
            f"not readable by uid {os.getuid()}: {', '.join(unreadable)}. Check PUID/PGID.",
        )
    return Check("media_path", Status.OK, f"{cfg.media_root} readable")


def media_readonly(cfg: Config) -> Check:
    """Uses statvfs flags only; never tries to write into the media tree."""
    try:
        ro = bool(os.statvfs(cfg.media_root).f_flag & os.ST_RDONLY)
    except OSError as e:
        return Check("media_readonly", Status.FAIL, f"cannot stat {cfg.media_root}: {e.strerror}")
    if ro:
        return Check("media_readonly", Status.OK, "media mount is read-only")
    return Check(
        "media_readonly", Status.FAIL, "media mount is WRITABLE; add ':ro' to the media volume"
    )


def jellyfin_version(jf: JellyfinClient) -> tuple[Check, dict[str, Any] | None]:
    try:
        info: dict[str, Any] = jf.get("/System/Info/Public")
    except JellyfinError as e:
        return Check("jellyfin_reachable", Status.FAIL, str(e)), None
    version = str(info.get("Version", "?"))
    try:
        major = int(version.split(".")[0])
    except ValueError:
        major = -1
    if major != SUPPORTED_MAJOR:
        return (
            Check(
                "jellyfin_reachable",
                Status.WARN,
                f"Jellyfin {version}; this release is tested with {SUPPORTED_MAJOR}.x",
            ),
            info,
        )
    return Check("jellyfin_reachable", Status.OK, f"Jellyfin {version}"), info


def api_key(jf: JellyfinClient, key: str | None) -> Check:
    if not key:
        return Check("api_key", Status.FAIL, "no API key found; run bootstrap")
    jf.use_token(key)
    try:
        jf.get("/Auth/Keys")
    except JellyfinError:
        return Check("api_key", Status.FAIL, "Jellyfin rejected the API key; re-run bootstrap")
    return Check("api_key", Status.OK, "API key accepted")


def libraries(jf: JellyfinClient, cfg: Config) -> list[Check]:
    try:
        folders = {f["Name"]: f for f in jf.virtual_folders()}
    except JellyfinError as e:
        return [Check("libraries", Status.FAIL, str(e))]
    out: list[Check] = []
    for key in cfg.libraries:
        name = LIBRARY_KINDS[key][0]
        f = folders.get(name)
        if f is None:
            out.append(Check(f"library_{key}", Status.FAIL, f"{name} not found; run bootstrap"))
            continue
        opts = f.get("LibraryOptions") or {}
        bad = [k for k, v in NO_MEDIA_WRITES.items() if opts.get(k) != v]
        if bad:
            out.append(
                Check(
                    f"library_{key}",
                    Status.FAIL,
                    f"{name} may write into media: {', '.join(bad)}; re-run bootstrap",
                )
            )
            continue
        status = str(f.get("RefreshStatus") or "Idle")
        if status != "Idle":
            pct = f.get("RefreshProgress")
            extra = f" ({pct:.0f}%)" if isinstance(pct, int | float) else ""
            out.append(Check(f"library_{key}", Status.WARN, f"{name} is scanning{extra}"))
        else:
            out.append(Check(f"library_{key}", Status.OK, f"{name} present, scan idle"))
    return out


def tmdb(
    env: dict[str, str] | os._Environ[str],
    transport: httpx.BaseTransport | None = None,
) -> Check:
    key = env.get("TMDB_API_KEY", "")
    if not key:
        return Check("tmdb_key", Status.WARN, "TMDB_API_KEY not set (needed for later phases)")
    try:
        with httpx.Client(transport=transport, timeout=10) as c:
            r = c.get(TMDB_URL, params={"api_key": key})
    except httpx.HTTPError as e:
        return Check("tmdb_key", Status.WARN, f"could not reach TMDB: {type(e).__name__}")
    if r.status_code == 200:
        return Check("tmdb_key", Status.OK, "TMDB key accepted")
    if r.status_code == 401:
        return Check("tmdb_key", Status.FAIL, "TMDB rejected the key")
    return Check("tmdb_key", Status.WARN, f"unexpected TMDB response HTTP {r.status_code}")


def disk(data_dir: Path, usage: Callable[[Path], Any] = shutil.disk_usage) -> Check:
    try:
        free = int(usage(data_dir).free)
    except OSError as e:
        return Check("disk_space", Status.FAIL, f"cannot check {data_dir}: {e.strerror}")
    gib = free / 1024**3
    if free < MIN_FREE_BYTES:
        return Check("disk_space", Status.FAIL, f"only {gib:.1f} GiB free in {data_dir}")
    return Check("disk_space", Status.OK, f"{gib:.1f} GiB free in {data_dir}")
