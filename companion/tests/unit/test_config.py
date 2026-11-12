from pathlib import Path

import pytest

from companion.config import ConfigError, load_config

EXAMPLE = Path(__file__).parents[3] / "config.example.yml"


def write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "config.yml"
    p.write_text(text)
    return p


def test_example_config_is_valid() -> None:
    cfg = load_config(EXAMPLE)
    assert cfg.library_path("movies") == "/media/movies"
    assert any(u.admin for u in cfg.users)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yml")


@pytest.mark.parametrize(
    ("text", "msg"),
    [
        ("libraries: {tv: tv}\nusers: [{name: a, admin: true}]", "unknown library"),
        ("libraries: {movies: m}\nusers: [{name: a}]", "admin"),
        ("libraries: {}\nusers: [{name: a, admin: true}]", "at least one library"),
        ("libraries: {movies: m}\nusers: [{name: a, admin: true}, {name: A}]", "duplicate"),
        (
            "libraries: {movies: m}\nusers: [{name: a, admin: true, libraries: [anime]}]",
            "undefined library",
        ),
        ("libraries: {movies: m}\nbogus: 1\nusers: [{name: a, admin: true}]", "bogus"),
        ("- a list", "mapping"),
    ],
)
def test_invalid_configs(tmp_path: Path, text: str, msg: str) -> None:
    with pytest.raises(ConfigError, match=msg):
        load_config(write(tmp_path, text))
