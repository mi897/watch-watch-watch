"""Thin Jellyfin REST client. Verified against the 12.4.0 OpenAPI spec.

Every non-GET request is counted in `mutations` so idempotence can be asserted in tests.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

APP_NAME = "watch-companion"
_DEVICE_ID = "watch-companion-bootstrap"


class JellyfinError(Exception):
    pass


class JellyfinClient:
    def __init__(
        self, base_url: str, *, transport: httpx.BaseTransport | None = None, version: str = "0"
    ) -> None:
        self._http = httpx.Client(base_url=base_url.rstrip("/"), transport=transport, timeout=30)
        self._version = version
        self._token: str | None = None
        self.mutations = 0

    # -- auth ---------------------------------------------------------------
    def _auth_header(self) -> str:
        parts = (
            f'Client="{APP_NAME}", Device="bootstrap", DeviceId="{_DEVICE_ID}", '
            f'Version="{self._version}"'
        )
        if self._token:
            parts += f', Token="{self._token}"'
        return f"MediaBrowser {parts}"

    def use_token(self, token: str) -> None:
        self._token = token

    def login(self, username: str, password: str) -> None:
        r = self.request(
            "POST", "/Users/AuthenticateByName", json={"Username": username, "Pw": password}
        )
        self._token = r.json()["AccessToken"]

    # -- plumbing -----------------------------------------------------------
    def request(self, method: str, path: str, **kw: Any) -> httpx.Response:
        if method != "GET" and path != "/Users/AuthenticateByName":
            self.mutations += 1
        try:
            r = self._http.request(
                method, path, headers={"Authorization": self._auth_header()}, **kw
            )
        except httpx.HTTPError as e:
            raise JellyfinError(f"cannot reach Jellyfin: {e}") from e
        if r.status_code >= 400:
            hint = " (wrong credentials or key?)" if r.status_code in (401, 403) else ""
            raise JellyfinError(f"{method} {path} -> HTTP {r.status_code}{hint}: {r.text[:200]}")
        return r

    def get(self, path: str, **kw: Any) -> Any:
        return self.request("GET", path, **kw).json()

    def wait_ready(self, timeout: float = 120) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last: Exception | None = None
        while time.monotonic() < deadline:
            try:
                info: dict[str, Any] = self.get("/System/Info/Public")
                return info
            except JellyfinError as e:
                last = e
                time.sleep(2)
        raise JellyfinError(f"Jellyfin not ready after {timeout:.0f}s: {last}")

    # -- startup wizard -----------------------------------------------------
    def startup_configure(self, server_name: str, language: str, country: str) -> None:
        self.request(
            "POST",
            "/Startup/Configuration",
            json={
                "ServerName": server_name,
                "UICulture": "en-US",
                "MetadataCountryCode": country,
                "PreferredMetadataLanguage": language,
            },
        )

    def startup_create_user(self, name: str, password: str) -> None:
        self.get("/Startup/User")  # initialises the default user row; required before POST
        self.request("POST", "/Startup/User", json={"Name": name, "Password": password})

    def startup_finish(self) -> None:
        self.request("POST", "/Startup/RemoteAccess", json={"EnableRemoteAccess": True})
        self.request("POST", "/Startup/Complete")

    # -- users --------------------------------------------------------------
    def users(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = self.get("/Users")
        return out

    def create_user(self, name: str, password: str) -> dict[str, Any]:
        out: dict[str, Any] = self.request(
            "POST", "/Users/New", json={"Name": name, "Password": password}
        ).json()
        return out

    def set_policy(self, user_id: str, policy: dict[str, Any]) -> None:
        self.request("POST", f"/Users/{user_id}/Policy", json=policy)

    def parental_ratings(self) -> dict[str, int]:
        rows: list[dict[str, Any]] = self.get("/Localization/ParentalRatings")
        return {r["Name"].upper(): r["Value"] for r in rows if r.get("Value") is not None}

    # -- libraries ----------------------------------------------------------
    def virtual_folders(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = self.get("/Library/VirtualFolders")
        return out

    def add_library(self, name: str, ctype: str, path: str, options: dict[str, Any]) -> None:
        self.request(
            "POST",
            "/Library/VirtualFolders",
            params={
                "name": name,
                "collectionType": ctype,
                "paths": path,
                "refreshLibrary": "false",
            },
            json={"LibraryOptions": options},
        )

    def update_library_options(self, item_id: str, options: dict[str, Any]) -> None:
        self.request(
            "POST",
            "/Library/VirtualFolders/LibraryOptions",
            json={"Id": item_id, "LibraryOptions": options},
        )

    # -- api keys -----------------------------------------------------------
    def api_key(self) -> str | None:
        items = self.get("/Auth/Keys")["Items"]
        for it in items:
            if it.get("AppName") == APP_NAME:
                return str(it["AccessToken"])
        return None

    def create_api_key(self) -> str:
        self.request("POST", "/Auth/Keys", params={"app": APP_NAME})
        key = self.api_key()
        if key is None:
            raise JellyfinError("API key was created but not found in /Auth/Keys")
        return key
