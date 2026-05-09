"""CLI entry: resolve management key and launch TUI."""

from __future__ import annotations

import argparse
import os
import sys

from openrouter_usage.app import UsageApp
from openrouter_usage.version import package_version

ENV_KEY = "OPENROUTER_MANAGEMENT_KEY"
_APP_VERSION = package_version()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="openrouter-usage",
        description=(
            "TUI for OpenRouter management API usage (activity, keys, credits). "
            f"Version {_APP_VERSION} (installed metadata; same as pyproject.toml when built)."
        ),
        epilog=(
            f"Management key: set environment variable {ENV_KEY} or pass --management-key / -k. "
            f"Use `export` so {ENV_KEY} is visible to child processes (e.g. uv run)."
        ),
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_APP_VERSION}",
    )
    p.add_argument(
        "--management-key",
        "-k",
        default=None,
        metavar="KEY",
        help=f"Override {ENV_KEY} (non-empty wins over environment).",
    )
    return p.parse_args(argv)


def resolve_management_key(cli_value: str | None) -> str:
    if cli_value and cli_value.strip():
        return cli_value.strip()
    env = os.environ.get(ENV_KEY, "").strip()
    if env:
        return env
    print(
        f"Missing management key: set {ENV_KEY} or use --management-key / -k.\n"
        f"Export {ENV_KEY} in this shell, then run: uv run openrouter-usage",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    key = resolve_management_key(args.management_key)
    UsageApp(management_key=key).run()


if __name__ == "__main__":
    main()
