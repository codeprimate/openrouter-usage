"""Smoke: same import chain as the `openrouter-usage` console script."""


def test_console_entry_imports() -> None:
    from openrouter_usage.main import main

    assert callable(main)
