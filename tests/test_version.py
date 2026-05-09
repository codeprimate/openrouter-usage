"""Package version from metadata (pyproject when installed)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from openrouter_usage import __version__
from openrouter_usage.main import parse_args
from openrouter_usage.version import DISTRIBUTION_NAME, package_version


def test_package_version_matches_pyproject() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    assert package_version() == expected
    assert __version__ == expected


def test_version_cli_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--version"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "openrouter-usage" in out
    assert package_version() in out


def test_distribution_name_constant() -> None:
    assert DISTRIBUTION_NAME == "openrouter-usage"
