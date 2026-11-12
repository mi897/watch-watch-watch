"""Run all checks; render human or JSON output with secrets redacted."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import httpx

from companion.bootstrap.run import read_key
from companion.config import Config
from companion.doctor import checks
from companion.doctor.checks import Check, Status
from companion.jellyfin import JellyfinClient

SECRET_ENV_HINTS = ("PASSWORD", "API_KEY", "TOKEN", "SECRET")


def run_doctor(
    cfg: Config,
    jf: JellyfinClient,
    *,
    env: Mapping[str, str],
    data_dir: Path,
    tmdb_transport: httpx.BaseTransport | None = None,
) -> list[Check]:
    results = [checks.media_path(cfg), checks.media_readonly(cfg)]
    version_check, _ = checks.jellyfin_version(jf)
    results.append(version_check)
    if version_check.status is not Status.FAIL:
        key = read_key(data_dir, env)
        key_check = checks.api_key(jf, key)
        results.append(key_check)
        if key_check.status is Status.OK:
            results.extend(checks.libraries(jf, cfg))
    results.append(checks.tmdb(dict(env), tmdb_transport))
    results.append(checks.disk(data_dir))
    return _redact(results, env, data_dir)


def _secrets(env: Mapping[str, str], data_dir: Path) -> list[str]:
    vals = [v for k, v in env.items() if v and any(h in k.upper() for h in SECRET_ENV_HINTS)]
    key = read_key(data_dir, {})
    if key:
        vals.append(key)
    return sorted({v for v in vals if len(v) >= 6}, key=len, reverse=True)


def _redact(results: list[Check], env: Mapping[str, str], data_dir: Path) -> list[Check]:
    secrets = _secrets(env, data_dir)
    for c in results:
        for s in secrets:
            c.detail = c.detail.replace(s, "***")
    return results


def exit_code(results: list[Check]) -> int:
    return 1 if any(c.status is Status.FAIL for c in results) else 0


def render_json(results: list[Check]) -> str:
    return json.dumps(
        {
            "ok": exit_code(results) == 0,
            "checks": [
                {"name": c.name, "status": c.status.value, "detail": c.detail} for c in results
            ],
        },
        indent=2,
    )


def render_human(results: list[Check]) -> str:
    tag = {Status.OK: " OK ", Status.WARN: "WARN", Status.FAIL: "FAIL"}
    lines = [f"[{tag[c.status]}] {c.name}: {c.detail}" for c in results]
    lines.append("")
    lines.append(
        "All required checks passed." if exit_code(results) == 0 else "Some checks FAILED."
    )
    return "\n".join(lines)
