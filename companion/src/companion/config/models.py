"""Config schema. Secrets are never stored here: passwords come from env vars by name."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

# library key -> (display name, Jellyfin collection type)
LIBRARY_KINDS: dict[str, tuple[str, str]] = {
    "movies": ("Movies", "movies"),
    "shows": ("Shows", "tvshows"),
    "anime": ("Anime", "tvshows"),
    "cartoons": ("Cartoons", "tvshows"),
}


class ConfigError(Exception):
    """Raised for any user-facing configuration problem."""


class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = "en"
    country: str = "US"


class UserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    admin: bool = False
    password_env: str | None = None
    max_rating: str | None = None
    libraries: list[str] | None = None


class PluginConfig(BaseModel):
    """A Jellyfin plugin to install. Third-party repositories are an explicit opt-in."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    version: str | None = None
    repository_url: str | None = None


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    media_root: str = "/media"
    server_name: str = "watch-watch-watch"
    libraries: dict[str, str] = Field(default_factory=dict)
    metadata: Metadata = Metadata()
    users: list[UserConfig] = Field(default_factory=list)
    plugins: list[PluginConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> Config:
        for key in self.libraries:
            if key not in LIBRARY_KINDS:
                raise ValueError(f"unknown library '{key}'; use one of {sorted(LIBRARY_KINDS)}")
        if not self.libraries:
            raise ValueError("define at least one library under 'libraries'")
        names = [u.name.lower() for u in self.users]
        if len(names) != len(set(names)):
            raise ValueError("duplicate user names")
        if not any(u.admin for u in self.users):
            raise ValueError("at least one user must have admin: true")
        for u in self.users:
            for lib in u.libraries or []:
                if lib not in self.libraries:
                    raise ValueError(f"user '{u.name}' references undefined library '{lib}'")
        return self

    def library_path(self, key: str) -> str:
        return str(Path(self.media_root) / self.libraries[key])


def load_config(path: str | Path) -> Config:
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {p} (copy config.example.yml to config.yml)")
    try:
        raw: Any = yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        raise ConfigError(f"{p}: invalid YAML: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"{p}: expected a mapping at the top level")
    try:
        return Config.model_validate(raw)
    except ValidationError as e:
        lines = [
            f"  {'.'.join(str(x) for x in err['loc']) or '(root)'}: {err['msg']}"
            for err in e.errors()
        ]
        raise ConfigError(f"{p}: invalid config:\n" + "\n".join(lines)) from e
