"""Command line entry point: `watch-companion bootstrap`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from companion import __version__
from companion.bootstrap import BootstrapError, run_bootstrap
from companion.config import ConfigError, load_config
from companion.jellyfin import JellyfinClient, JellyfinError


def _bootstrap(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
        jf = JellyfinClient(args.jellyfin_url, version=__version__)
        report = run_bootstrap(cfg, jf, env=os.environ, data_dir=Path(args.data_dir))
    except (ConfigError, BootstrapError, JellyfinError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for line in report.changes:
        print(f"changed: {line}")
    for line in report.drift:
        print(f"drift:   {line}")
    if not report.changes:
        print("nothing to change; Jellyfin already matches the config")
    print(f"mutating Jellyfin calls: {jf.mutations}")
    if report.generated_passwords:
        print("\nGenerated passwords (shown ONCE, never stored; change them after first login):")
        for name, pw in report.generated_passwords.items():
            print(f"  {name}: {pw}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="watch-companion")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bootstrap", help="reconcile config.yml into Jellyfin (idempotent)")
    b.add_argument("--config", default=os.environ.get("COMPANION_CONFIG", "/config/config.yml"))
    b.add_argument("--jellyfin-url", default=os.environ.get("JELLYFIN_URL", "http://jellyfin:8096"))
    b.add_argument("--data-dir", default=os.environ.get("COMPANION_DATA_DIR", "/data"))
    b.set_defaults(func=_bootstrap)
    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
