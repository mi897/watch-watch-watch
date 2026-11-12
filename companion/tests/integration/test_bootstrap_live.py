"""Needs a real, fresh Jellyfin. Set JELLYFIN_TEST_URL and JELLYFIN_TEST_MEDIA.

JELLYFIN_TEST_MEDIA must be the same absolute path on the host and inside the Jellyfin
container (mounted read-only there). Run with: pytest -m integration
"""

import hashlib
import os
from pathlib import Path

import pytest

from companion.bootstrap import run_bootstrap
from companion.config import Config
from companion.doctor import Status, run_doctor
from companion.jellyfin import JellyfinClient

pytestmark = pytest.mark.integration
URL = os.environ.get("JELLYFIN_TEST_URL")
MEDIA = os.environ.get("JELLYFIN_TEST_MEDIA")


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        st = p.stat()
        h.update(f"{p.relative_to(root)}:{st.st_size}:{st.st_mtime_ns}".encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


@pytest.mark.skipif(not (URL and MEDIA), reason="no Jellyfin configured")
def test_bootstrap_converges_and_is_idempotent(tmp_path: Path) -> None:
    assert URL and MEDIA
    media = Path(MEDIA)
    for d in ("movies", "shows", "cartoons"):
        (media / d).mkdir(parents=True, exist_ok=True)
    (media / "movies" / "Heat (1995).mkv").write_bytes(b"stub")
    (media / "shows" / "Show - S01E01.mkv").write_bytes(b"stub")
    before = tree_hash(media)

    cfg = Config.model_validate(
        {
            "media_root": MEDIA,
            "libraries": {"movies": "movies", "shows": "shows", "cartoons": "cartoons"},
            "users": [
                {"name": "alice", "admin": True, "password_env": "PW_ALICE"},
                {"name": "kid", "max_rating": "PG", "libraries": ["cartoons"]},
            ],
        }
    )
    env = {"PW_ALICE": "test-password-1"}

    first_client = JellyfinClient(URL)
    first = run_bootstrap(cfg, first_client, env=env, data_dir=tmp_path)
    assert first_client.mutations > 0
    assert "kid" in first.generated_passwords
    assert "alice" not in first.generated_passwords
    assert (tmp_path / "jellyfin_api_key").stat().st_mode & 0o777 == 0o600

    second_client = JellyfinClient(URL)
    second = run_bootstrap(cfg, second_client, env=env, data_dir=tmp_path)
    assert second.changes == []
    assert second_client.mutations == 0

    # Library options that write into media folders must be off.
    for folder in second_client.virtual_folders():
        opts = folder["LibraryOptions"]
        assert opts["SaveLocalMetadata"] is False
        assert opts["MetadataSavers"] == []
        assert opts["SaveSubtitlesWithMedia"] is False

    results = run_doctor(cfg, second_client, env={}, data_dir=tmp_path)
    failed = {c.name for c in results if c.status is Status.FAIL}
    # The media dir is a plain host dir in CI, so only these two may legitimately fail.
    assert failed <= {"media_readonly", "api_key"}, failed

    assert tree_hash(media) == before
