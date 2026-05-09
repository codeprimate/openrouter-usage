"""Sort mode: Tab switches DataTable from cell cursor to column cursor (no extra header row)."""

import asyncio

import openrouter_usage.app as app_mod
import pytest
from openrouter_usage.app import KeySelect, UsageApp
from textual.widgets import DataTable


def test_tab_from_table_sets_column_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_mod.api_client, "fetch_all_keys", lambda k: [])
    monkeypatch.setattr(app_mod.api_client, "fetch_activity", lambda k, **kw: [])
    monkeypatch.setattr(
        app_mod.api_client,
        "fetch_credits",
        lambda k: {"total_credits": 0.0, "total_usage": 0.0},
    )

    async def run() -> None:
        app = UsageApp("k")
        async with app.run_test() as pilot:
            await pilot.pause(0.35)
            table = app.query_one("#activity", DataTable)
            table.focus()
            assert isinstance(app.focused, DataTable)
            assert table.cursor_type == "cell"
            await pilot.press("tab")
            await pilot.pause(0.08)
            assert isinstance(app.focused, DataTable)
            assert table.cursor_type == "column"
            await pilot.press("escape")
            await pilot.pause(0.08)
            assert table.cursor_type == "cell"

    asyncio.run(run())


def test_escape_from_key_select_focuses_activity_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(app_mod.api_client, "fetch_all_keys", lambda k: [])
    monkeypatch.setattr(app_mod.api_client, "fetch_activity", lambda k, **kw: [])
    monkeypatch.setattr(
        app_mod.api_client,
        "fetch_credits",
        lambda k: {"total_credits": 0.0, "total_usage": 0.0},
    )

    async def run() -> None:
        app = UsageApp("k")
        async with app.run_test() as pilot:
            await pilot.pause(0.35)
            app.query_one("#key_select", KeySelect).focus()
            await pilot.pause(0.08)
            assert isinstance(app.focused, KeySelect)
            await pilot.press("escape")
            await pilot.pause(0.12)
            assert isinstance(app.focused, DataTable)

    asyncio.run(run())
