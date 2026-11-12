from pathlib import Path

import pytest

from companion.bootstrap.run import NO_MEDIA_WRITES, BootstrapError, _check_media
from companion.config import Config


def cfg(root: Path) -> Config:
    return Config.model_validate(
        {
            "media_root": str(root),
            "libraries": {"movies": "movies"},
            "users": [{"name": "a", "admin": True}],
        }
    )


def test_missing_media_root_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(BootstrapError, match="does not exist"):
        _check_media(cfg(tmp_path / "wrong"))


def test_missing_library_folder(tmp_path: Path) -> None:
    with pytest.raises(BootstrapError, match="library 'movies'"):
        _check_media(cfg(tmp_path))


def test_ok(tmp_path: Path) -> None:
    (tmp_path / "movies").mkdir()
    _check_media(cfg(tmp_path))


def test_no_media_writes_all_disabled() -> None:
    assert NO_MEDIA_WRITES["SaveLocalMetadata"] is False
    assert NO_MEDIA_WRITES["MetadataSavers"] == []
    assert all(v in (False, []) for v in NO_MEDIA_WRITES.values())
