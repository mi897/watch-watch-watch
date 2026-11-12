import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from companion.bootstrap.run import NO_MEDIA_WRITES
from companion.config import Config
from companion.doctor import Status, checks, render_human, render_json, run_doctor
from companion.jellyfin import JellyfinClient


def cfg(root: Path) -> Config:
    return Config.model_validate(
        {
            "media_root": str(root),
            "libraries": {"movies": "movies"},
            "users": [{"name": "a", "admin": True}],
        }
    )


def jf_with(routes: dict[str, Any]) -> JellyfinClient:
    def handler(req: httpx.Request) -> httpx.Response:
        r = routes.get(req.url.path)
        if r is None:
            return httpx.Response(404, text="no route")
        if isinstance(r, int):
            return httpx.Response(r, text="err")
        return httpx.Response(200, json=r)

    return JellyfinClient("http://jf", transport=httpx.MockTransport(handler))


# --- media_path -------------------------------------------------------------
def test_media_path_ok_and_fail(tmp_path: Path) -> None:
    (tmp_path / "movies").mkdir()
    assert checks.media_path(cfg(tmp_path)).status is Status.OK
    assert checks.media_path(cfg(tmp_path / "x")).status is Status.FAIL


def test_media_path_missing_library_folder(tmp_path: Path) -> None:
    assert checks.media_path(cfg(tmp_path)).status is Status.FAIL


@pytest.mark.skipif(os.getuid() == 0, reason="root can read anything")
def test_media_path_unreadable(tmp_path: Path) -> None:
    d = tmp_path / "movies"
    d.mkdir()
    d.chmod(0)
    try:
        assert checks.media_path(cfg(tmp_path)).status is Status.FAIL
    finally:
        d.chmod(0o755)


# --- media_readonly -----------------------------------------------------------
def test_media_readonly(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(os, "statvfs", lambda _p: SimpleNamespace(f_flag=os.ST_RDONLY))
    assert checks.media_readonly(cfg(tmp_path)).status is Status.OK
    monkeypatch.setattr(os, "statvfs", lambda _p: SimpleNamespace(f_flag=0))
    assert checks.media_readonly(cfg(tmp_path)).status is Status.FAIL


# --- jellyfin ---------------------------------------------------------------
def test_jellyfin_version() -> None:
    c, _ = checks.jellyfin_version(jf_with({"/System/Info/Public": {"Version": "12.4.0"}}))
    assert c.status is Status.OK
    c, _ = checks.jellyfin_version(jf_with({"/System/Info/Public": {"Version": "10.11.1"}}))
    assert c.status is Status.WARN
    c, _ = checks.jellyfin_version(jf_with({"/System/Info/Public": 500}))
    assert c.status is Status.FAIL


def test_api_key() -> None:
    assert checks.api_key(jf_with({"/Auth/Keys": {"Items": []}}), "k").status is Status.OK
    assert checks.api_key(jf_with({"/Auth/Keys": 401}), "k").status is Status.FAIL
    assert checks.api_key(jf_with({}), None).status is Status.FAIL


# --- libraries --------------------------------------------------------------
def folder(opts: dict[str, Any] | None = None, status: str = "Idle") -> dict[str, Any]:
    return {
        "Name": "Movies",
        "RefreshStatus": status,
        "RefreshProgress": 40.0,
        "LibraryOptions": {**NO_MEDIA_WRITES, **(opts or {})},
    }


def test_libraries(tmp_path: Path) -> None:
    c = cfg(tmp_path)
    ok = checks.libraries(jf_with({"/Library/VirtualFolders": [folder()]}), c)
    assert ok[0].status is Status.OK
    scanning = checks.libraries(jf_with({"/Library/VirtualFolders": [folder(status="Active")]}), c)
    assert scanning[0].status is Status.WARN
    assert "40%" in scanning[0].detail
    writes = checks.libraries(
        jf_with({"/Library/VirtualFolders": [folder({"SaveLocalMetadata": True})]}), c
    )
    assert writes[0].status is Status.FAIL
    missing = checks.libraries(jf_with({"/Library/VirtualFolders": []}), c)
    assert missing[0].status is Status.FAIL


# --- tmdb -------------------------------------------------------------------
def tmdb_transport(code: int) -> httpx.MockTransport:
    return httpx.MockTransport(lambda _r: httpx.Response(code, json={}))


def test_tmdb() -> None:
    assert checks.tmdb({}, None).status is Status.WARN
    env = {"TMDB_API_KEY": "abc123"}
    assert checks.tmdb(env, tmdb_transport(200)).status is Status.OK
    assert checks.tmdb(env, tmdb_transport(401)).status is Status.FAIL
    assert checks.tmdb(env, tmdb_transport(503)).status is Status.WARN


def test_tmdb_unreachable_is_warning_not_failure() -> None:
    def boom(_r: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    assert checks.tmdb({"TMDB_API_KEY": "abc123"}, httpx.MockTransport(boom)).status is Status.WARN


# --- disk -------------------------------------------------------------------
def test_disk(tmp_path: Path) -> None:
    big = checks.disk(tmp_path, lambda _p: SimpleNamespace(free=50 * 1024**3))
    small = checks.disk(tmp_path, lambda _p: SimpleNamespace(free=1024))
    assert big.status is Status.OK
    assert small.status is Status.FAIL


# --- end to end + redaction -------------------------------------------------
def test_run_doctor_redacts_secrets_and_sets_exit(tmp_path: Path) -> None:
    (tmp_path / "movies").mkdir()
    (tmp_path / "data").mkdir()
    secret = "SUPERSECRETKEY123"
    jf = jf_with({"/System/Info/Public": {"Version": f"12.4.0-{secret}"}, "/Auth/Keys": 401})
    env = {"JELLYFIN_API_KEY": secret}
    res = run_doctor(cfg(tmp_path), jf, env=env, data_dir=tmp_path / "data")
    assert any(c.status is Status.FAIL for c in res)
    for text in (render_json(res), render_human(res)):
        assert secret not in text
    data = json.loads(render_json(res))
    assert data["ok"] is False
    assert {c["name"] for c in data["checks"]} >= {"media_path", "api_key", "disk_space"}
