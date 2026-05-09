"""Installed distribution version (matches ``pyproject.toml`` ``[project].version`` when built)."""

from __future__ import annotations

import importlib.metadata

DISTRIBUTION_NAME = "openrouter-usage"
_UNKNOWN_VERSION = "0.0.0+unknown"


def package_version() -> str:
    """Return the version string from package metadata."""
    try:
        return importlib.metadata.version(DISTRIBUTION_NAME)
    except importlib.metadata.PackageNotFoundError:
        return _UNKNOWN_VERSION
