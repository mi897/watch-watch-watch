import json
from pathlib import Path
from typing import Any

import httpx
import pytest

import companion.bootstrap.run as run
from companion.bootstrap.run import BootstrapError, Report, _ensure_plugins
from companion.config import Config
from companion.jellyfin import JellyfinClient


class Fake:
    def __init__(self, installed: list[str], pending: bool, fail: bool = False) -> None:
        self.installed = installed
        self.pending = pending
        self.fail = fail
        self.calls: list[tuple[str, str, Any]] = []

    def handler(self, req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content) if req.content else None
        self.calls.append((req.method, req.url.path, body))
        p = req.url.path
        if p == "/Plugins":
            return httpx.Response(200, json=[{"Name": n} for n in self.installed])
        if p == "/Repositories" and req.method == "GET":
            return httpx.Response(200, json=[])
        if p.startswith("/Packages/Installed/") and self.fail:
            return httpx.Response(404, text="nope")
        if p == "/System/Info":
            return httpx.Response(200, json={"HasPendingRestart": self.pending})
        if p == "/System/Info/Public":
            return httpx.Response(200, json={"StartupWizardCompleted": True})
        return httpx.Response(204)

    def client(self) -> JellyfinClient:
        return JellyfinClient("http://jf", transport=httpx.MockTransport(self.handler))


def cfg(plugins: list[dict[str, Any]]) -> Config:
    return Config.model_validate(
        {
            "libraries": {"movies": "m"},
            "users": [{"name": "a", "admin": True}],
            "plugins": plugins,
        }
    )


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run.time, "sleep", lambda _s: None)


def test_installs_adds_repo_and_restarts() -> None:
    fake = Fake([], pending=True)
    rep = Report()
    plugins = [{"name": "AniList", "repository_url": "https://example.test/m.json"}]
    _ensure_plugins(fake.client(), cfg(plugins), rep)
    paths = [(m, p) for m, p, _ in fake.calls]
    assert ("POST", "/Repositories") in paths
    assert ("POST", "/Packages/Installed/AniList") in paths
    assert ("POST", "/System/Restart") in paths
    assert any("restarted" in c for c in rep.changes)


def test_already_installed_is_a_noop() -> None:
    fake = Fake(["AniList"], pending=False)
    c = fake.client()
    _ensure_plugins(c, cfg([{"name": "anilist"}]), Report())
    assert c.mutations == 0


def test_failed_install_has_clear_message() -> None:
    fake = Fake([], pending=False, fail=True)
    with pytest.raises(BootstrapError, match="could not install plugin 'X'"):
        _ensure_plugins(fake.client(), cfg([{"name": "X"}]), Report())


def test_no_plugins_means_no_calls(tmp_path: Path) -> None:
    fake = Fake([], pending=False)
    _ensure_plugins(fake.client(), cfg([]), Report())
    assert fake.calls == []
