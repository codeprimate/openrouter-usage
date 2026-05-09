"""Textual TUI for OpenRouter usage."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import ClassVar

import httpx
from rich.markup import escape as rich_escape
from rich.text import Text
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.coordinate import Coordinate
from textual.render import measure
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Select, Static
from textual.widgets._select import SelectCurrent, SelectOverlay

from openrouter_usage import client as api_client
from openrouter_usage.domain import (
    COLUMN_LABELS,
    HELP_COLUMN_LEGEND,
    SORT_ASC_INDICATOR,
    SORT_DESC_INDICATOR,
    ClientFilters,
    SortColumn,
    activity_row_from_api,
    aggregate_usd_per_request,
    apply_filters,
    column_index_to_key,
    format_int_commas,
    format_row_usd_per_request_cell,
    format_usd,
    format_usd_per_request,
    sort_rows,
    totals,
)
from openrouter_usage.version import package_version

# Short prompt keeps one line next to credits; full behavior unchanged (still filters refresh).
_KEY_SELECT_PROMPT = "API key"
_APP_VERSION = package_version()
# Header: name then version; title strip is right-aligned so ellipsis keeps the semver on the right.
_HEADER_TITLE_SEPARATOR = " · "
# Rich markup on Static: dim labels, bold numbers. Escape untrusted text with rich_escape.
_STATUS_BAR_SEP = "  [dim]│[/dim]  "


class HelpScreen(ModalScreen[None]):
    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "dismiss", "Close")]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen #help_text {
        width: auto;
        max-width: 96;
        max-height: 92%;
        border: thick $accent;
        background: $boost;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        legend = "\n".join(f"  {abbr} — {desc}" for abbr, desc in HELP_COLUMN_LEGEND)
        yield Static(
            f"[bold cyan]openrouter-usage[/bold cyan] [dim]{_APP_VERSION}[/dim] — "
            "[bold]Help[/bold] [dim](Esc to close)[/dim]\n\n"
            "[bold]Spend[/bold] = OpenRouter credits (usage) + BYOK inference (USD).\n"
            "[dim]Credits (account) vs Activity totals may differ.[/dim]\n\n"
            f"[bold]Column abbreviations[/bold]\n{legend}\n\n"
            "[bold]Navigation[/bold]\n"
            "Tab — from activity table (cell cursor): column cursor for sort. "
            "Tab again moves focus.\n"
            "Shift+Tab — normal focus order.\n"
            "↑↓←→ — cell mode: move by row/column. "
            "Sort mode (←→): pick column; column is highlighted.\n"
            "Enter — sort mode: sort by column. Cell mode: filter (Date/Model/Provider only).\n"
            "Esc — exit sort mode (column cursor) back to cell cursor.\n"
            "Esc — on API key selector: focus activity table; closes the key menu if open.\n"
            "Click a column header to sort (same as sort mode + Enter).\n\n"
            "[bold]Actions[/bold]\n"
            "c — clear all filters\n"
            "r — refresh from API\n"
            "q — quit\n"
            "? — this help\n",
            id="help_text",
        )

    def action_dismiss(self) -> None:
        self.dismiss()


class ActivityTable(DataTable):
    """Built-in header only; column cursor is for sort — restore cell cursor when focus leaves."""

    def _on_blur(self, event: events.Blur) -> None:
        self.cursor_type = "cell"
        super()._on_blur(event)


class KeySelectOverlay(SelectOverlay):
    """Esc returns to the activity table (same idea as Esc leaving column sort mode)."""

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            parent = self.parent
            exit_table = getattr(parent, "escape_to_activity_table", None)
            if callable(exit_table):
                exit_table()
            return
        await super()._on_key(event)


class KeySelect(Select[str]):
    """API key `Select` with Esc to activity table (collapsed or overlay focused)."""

    def compose(self) -> ComposeResult:
        yield SelectCurrent(self.prompt)
        yield KeySelectOverlay(type_to_search=self._type_to_search).data_bind(
            compact=KeySelect.compact
        )

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.escape_to_activity_table()
            return
        await super()._on_key(event)

    def escape_to_activity_table(self) -> None:
        self.expanded = False
        self.app.query_one("#activity", DataTable).focus()
        self.app.call_after_refresh(self._ping_idle)

    def _ping_idle(self) -> None:
        app = self.app
        if isinstance(app, UsageApp):
            app._set_status_idle()


class UsageApp(App[None]):
    TITLE = "openrouter-usage"
    SUB_TITLE = _APP_VERSION
    CSS = """
    Header HeaderIcon {
        display: none;
    }
    Header HeaderTitle {
        content-align: right middle;
    }
    /* Default Header height is 1; a thick bottom border covers the title row. */
    Header {
        background: $surface;
    }
    #main {
        background: $boost;
    }
    #stale_key {
        color: $warning;
        height: auto;
        text-style: bold;
        padding: 0 1;
        background: $warning 12%;
    }
    #status {
        height: auto;
        background: $panel;
        color: $text-muted;
        border-top: tall $border;
        padding: 0 1;
    }
    #credits_key_row {
        height: auto;
        align: left middle;
        background: $surface;
        border-bottom: wide $border;
        padding: 0 1;
    }
    #credits_key_row #credits {
        width: 1fr;
        height: auto;
    }
    #credits_key_row #key_select {
        width: auto;
        max-width: 42%;
        height: auto;
    }
    #totals {
        height: auto;
        padding: 0 1;
        background: $panel;
        border-bottom: wide $border;
        border-left: outer $accent;
    }
    #activity {
        height: 1fr;
        min-height: 3;
        border: tall $border;
    }
    #activity:focus > .datatable--header {
        background: $accent 22%;
        color: $foreground;
    }
    #activity > .datatable--even-row {
        background: $foreground 5%;
    }
    Select:focus {
        border: tall $accent;
    }
    /* Footer is height=1; a tall top border replaces the binding strip. */
    Footer {
        background: $panel;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("c", "clear_filters", "Clear filters", show=True),
        Binding("question_mark", "help", "Help", show=True),
    ]

    def format_title(self, title: str, sub_title: str) -> Content:
        """Name then version; right-aligned header keeps the full semver visible when clipped."""
        if sub_title:
            version_line = Content(sub_title).stylize("dim")
            return Content.assemble(
                Content(title),
                (_HEADER_TITLE_SEPARATOR, "dim"),
                version_line,
            )
        return Content(title)

    def __init__(self, management_key: str) -> None:
        super().__init__()
        self.management_key = management_key
        self._raw_rows: list = []
        self._keys: list[dict] = []
        self._credits: dict[str, float] | None = None
        self._client_filters = ClientFilters()
        self._sort_column: SortColumn = "date"
        self._sort_ascending = True
        self._last_fetched_key_hash: str | None = None
        self._selected_key_hash: str | None = None
        self._display_rows: list = []
        self._keys_loaded_n: int = 0
        self._activity_raw_n: int = 0
        self._last_refresh: str = "—"
        self._loading = False
        self._error: str | None = None
        self._flash_message: str | None = None
        self._flash_until: float = 0.0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Vertical(
            Horizontal(
                Static("", id="credits"),
                KeySelect(
                    [],
                    id="key_select",
                    prompt=_KEY_SELECT_PROMPT,
                    compact=True,
                ),
                id="credits_key_row",
            ),
            Static("", id="stale_key"),
            Static("", id="totals"),
            ActivityTable(id="activity", cursor_type="cell", zebra_stripes=True),
            Static("", id="status"),
            id="main",
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#activity", DataTable)
        for label in COLUMN_LABELS:
            table.add_column(label, key=label)
        self.query_one("#stale_key", Static).display = False
        self.call_after_refresh(self._focus_table)
        self.set_interval(0.4, self._tick_flash)
        self.load_remote()

    def _tick_flash(self) -> None:
        if self._flash_message and time.monotonic() >= self._flash_until:
            self._flash_message = None
            if not self._loading and not self._error:
                self._set_status_idle()

    def _focus_table(self) -> None:
        self.query_one("#activity", DataTable).focus()

    def _sync_fetch(self) -> tuple[list[dict], list[dict], dict[str, float]]:
        keys = api_client.fetch_all_keys(self.management_key)
        h = self._selected_key_hash
        if not h:
            h = None
        activity = api_client.fetch_activity(self.management_key, api_key_hash=h)
        credits = api_client.fetch_credits(self.management_key)
        return keys, activity, credits

    @work(exclusive=True, group="remote")
    async def load_remote(self) -> None:
        self._begin_load()
        try:
            keys, activity_raw, credits = await asyncio.to_thread(self._sync_fetch)
        except api_client.OpenRouterAPIError as e:
            self._end_load_error(str(e), e.status_code)
            return
        except OSError as e:
            self._end_load_error(str(e), None)
            return
        except httpx.HTTPError as e:
            self._end_load_error(str(e), None)
            return
        self._end_load_ok(keys, activity_raw, credits)

    def _begin_load(self) -> None:
        self._loading = True
        self._error = None
        self._set_status_loading()

    def _end_load_error(self, msg: str, code: int | None) -> None:
        self._loading = False
        hint = ""
        if code == 401:
            hint = " Check OPENROUTER_MANAGEMENT_KEY or pass -k with a valid management key."
        self._error = f"{msg}{hint}"
        self._set_status_error()

    def _end_load_ok(
        self,
        keys: list[dict],
        activity_raw: list[dict],
        credits: dict[str, float],
    ) -> None:
        self._loading = False
        self._error = None
        self._keys = keys
        self._keys_loaded_n = len(keys)
        self._raw_rows = [activity_row_from_api(d) for d in activity_raw]
        self._activity_raw_n = len(self._raw_rows)
        self._credits = credits
        self._last_fetched_key_hash = self._selected_key_hash if self._selected_key_hash else None
        self._last_refresh = datetime.now().strftime("%H:%M:%S")
        self._populate_key_select()
        self._update_credits_static()
        self._update_stale_banner()
        self.refresh_table()
        self._set_status_idle()
        self.call_after_refresh(self._focus_table)

    def _populate_key_select(self) -> None:
        sel = self.query_one("#key_select", Select)
        opts: list[tuple[str, str]] = [("All keys", "")]
        for k in self._keys:
            h = str(k.get("hash") or "")
            name = str(k.get("name") or k.get("label") or h)[:56]
            opts.append((name, h))
        sel.set_options(opts)
        cur = self._selected_key_hash or ""
        try:
            sel.value = cur
        except Exception:
            sel.value = ""

    @on(Select.Changed, "#key_select")
    def key_select_changed(self, event: Select.Changed) -> None:
        v = event.value
        self._selected_key_hash = v if v else None
        self._update_stale_banner()
        self._set_status_idle()

    def _update_stale_banner(self) -> None:
        st = self.query_one("#stale_key", Static)
        cur = self._selected_key_hash if self._selected_key_hash else None
        last = self._last_fetched_key_hash
        if cur != last and self._last_refresh != "—":
            st.update("[bold yellow]![/bold yellow] Key filter changed — press [bold]r[/bold]")
            st.display = True
        else:
            st.update("")
            st.display = False

    def _update_credits_static(self) -> None:
        s = self.query_one("#credits", Static)
        if not self._credits:
            s.update(
                "[dim]Credits (account):[/dim] —   "
                f"{_STATUS_BAR_SEP}[dim]Activity:[/dim] last 30d UTC — rows —"
            )
            return
        tc = self._credits["total_credits"]
        tu = self._credits["total_usage"]
        rem = tc - tu
        s.update(
            "[bold cyan]Account[/bold cyan] [dim]used[/dim] "
            f"[bold]{format_usd(tu)}[/bold] [dim]/ purchased[/dim] {format_usd(tc)} "
            f"[dim](remaining[/dim] [green]~{format_usd(rem)}[/green][dim])[/dim]"
            f"{_STATUS_BAR_SEP}"
            "[bold cyan]Activity[/bold cyan] [dim]last 30d UTC · fetched[/dim] "
            f"[bold]{self._activity_raw_n}[/bold] [dim]rows[/dim]"
        )

    def refresh_table(self) -> None:
        vis = apply_filters(self._raw_rows, self._client_filters)
        vis = sort_rows(vis, self._sort_column, self._sort_ascending)
        self._display_rows = vis
        t = self.query_one("#activity", DataTable)
        t.clear()
        for r in vis:
            t.add_row(
                r.date,
                r.model[:40] + ("…" if len(r.model) > 40 else ""),
                r.provider_name[:20],
                format_int_commas(r.requests),
                format_usd(r.spend),
                format_row_usd_per_request_cell(r),
                format_int_commas(r.prompt_tokens),
                format_int_commas(r.completion_tokens),
                format_int_commas(r.reasoning_tokens),
            )
        tot_line = ""
        if not vis and self._raw_rows:
            tot_line = (
                "[yellow]No rows match filters[/yellow] "
                "[dim]([/dim][bold]c[/bold][dim] to clear)[/dim]"
            )
        elif not self._raw_rows:
            tot_line = "[dim]No activity in window[/dim]"
        else:
            tot = totals(vis)
            pt, ct, rt = tot["prompt_tokens"], tot["completion_tokens"], tot["reasoning_tokens"]
            blend_upr = aggregate_usd_per_request(vis)
            upr_part = (
                f"  [dim]$/Req[/dim] [bold]{format_usd_per_request(blend_upr)}[/bold]"
                if blend_upr is not None
                else ""
            )
            tot_line = (
                "[bold magenta]Totals[/bold magenta] [dim](filtered)[/dim] · "
                f"[dim]Req[/dim] [bold]{format_int_commas(int(tot['requests']))}[/bold]  "
                f"[dim]Spend[/dim] [bold yellow]{format_usd(float(tot['spend']))}[/bold yellow]"
                f"{upr_part}  "
                f"[dim]Pr[/dim] [bold]{format_int_commas(int(pt))}[/bold]  "
                f"[dim]Cmp[/dim] [bold]{format_int_commas(int(ct))}[/bold]  "
                f"[dim]Rsn[/dim] [bold]{format_int_commas(int(rt))}[/bold]"
            )
        self.query_one("#totals", Static).update(tot_line)
        self._update_header_sort_indicators()
        self._set_status_idle()

    def _update_header_sort_indicators(self) -> None:
        table = self.query_one("#activity", DataTable)
        console = self.console
        for i, column in enumerate(table.ordered_columns):
            sort_key = column_index_to_key(i)
            base = COLUMN_LABELS[i]
            if sort_key == self._sort_column:
                arrow = SORT_ASC_INDICATOR if self._sort_ascending else SORT_DESC_INDICATOR
                label_plain = f"{base} {arrow}"
            else:
                label_plain = base
            column.label = Text(label_plain, no_wrap=True, end="")
            if column.auto_width:
                label_render_width = measure(console, column.label, 1)
                column.content_width = max(column.content_width, label_render_width)
        table.refresh()

    def _apply_sort_for_column_index(self, column_index: int) -> None:
        col = column_index_to_key(column_index)
        if col == self._sort_column:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = col
            self._sort_ascending = True
        self.refresh_table()

    def _set_status_loading(self) -> None:
        self.query_one("#status", Static).update(
            "[bold yellow]Loading…[/bold yellow]"
            f"{_STATUS_BAR_SEP}[dim]r ignored while loading[/dim]"
            f"{_STATUS_BAR_SEP}[dim]Keys[/dim] —"
            f"{_STATUS_BAR_SEP}[dim]Focus[/dim] —"
        )

    def _set_status_error(self) -> None:
        safe = rich_escape(self._error or "")
        self.query_one("#status", Static).update(
            f"[bold red]Error[/bold red]: {safe}"
            f"{_STATUS_BAR_SEP}[yellow]r[/yellow] [dim]retry[/dim]"
            f"{_STATUS_BAR_SEP}[dim]q quit[/dim]"
        )

    def _set_status_idle(self) -> None:
        if self._error:
            self._set_status_error()
            return
        if self._flash_message and time.monotonic() >= self._flash_until:
            self._flash_message = None
        focus = self._focus_label()
        flash = ""
        if self._flash_message and time.monotonic() < self._flash_until:
            flash = f"{_STATUS_BAR_SEP}[cyan]{rich_escape(self._flash_message)}[/cyan]"
        sort_arrow = (
            SORT_ASC_INDICATOR if self._sort_ascending else SORT_DESC_INDICATOR
        )
        self.query_one("#status", Static).update(
            f"[bold]{focus}[/bold]"
            f"{_STATUS_BAR_SEP}{rich_escape(self._client_filters.summary())}"
            f"{_STATUS_BAR_SEP}[dim]rows[/dim] [bold]{len(self._display_rows)}[/bold]"
            f"[dim]/[/dim][bold]{len(self._raw_rows)}[/bold]"
            f"{_STATUS_BAR_SEP}[dim]Sort[/dim] [bold]{self._sort_column}[/bold] {sort_arrow}"
            f"{_STATUS_BAR_SEP}[dim]Keys[/dim] [bold]{self._keys_loaded_n}[/bold]"
            f"{_STATUS_BAR_SEP}[dim]refresh[/dim] [bold]{self._last_refresh}[/bold]"
            f"{flash}"
        )

    def _focus_label(self) -> str:
        w = self.focused
        if w is None:
            return "TABLE"
        if isinstance(w, DataTable):
            return "SORT" if w.cursor_type == "column" else "TABLE"
        if isinstance(w, Select):
            return "KEY"
        return "OTHER"

    def action_quit(self) -> None:
        self.exit()

    def action_refresh(self) -> None:
        if self._loading:
            return
        self.load_remote()

    def action_clear_filters(self) -> None:
        if not self._client_filters.active_parts():
            self._flash("No active filters")
            return
        self._client_filters = ClientFilters()
        self.refresh_table()

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def _flash(self, text: str, seconds: float = 1.5) -> None:
        self._flash_message = text
        self._flash_until = time.monotonic() + seconds
        self._set_status_idle()

    @on(DataTable.CellSelected, "#activity")
    def activity_cell_selected(self, event: DataTable.CellSelected) -> None:
        self._apply_cell_filter(event.coordinate)

    @on(DataTable.ColumnSelected, "#activity")
    def activity_column_selected(self, event: DataTable.ColumnSelected) -> None:
        self._apply_sort_for_column_index(event.cursor_column)

    @on(DataTable.HeaderSelected, "#activity")
    def activity_header_selected(self, event: DataTable.HeaderSelected) -> None:
        self._apply_sort_for_column_index(event.column_index)

    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        if event.key == "escape":
            if isinstance(focused, DataTable) and focused.cursor_type == "column":
                event.prevent_default()
                event.stop()
                focused.cursor_type = "cell"
                self.call_after_refresh(self._set_status_idle)
                return
        if event.key == "tab":
            if isinstance(focused, DataTable) and focused.cursor_type == "cell":
                event.prevent_default()
                event.stop()
                focused.cursor_type = "column"
                self.call_after_refresh(self._set_status_idle)
                return
            self.call_after_refresh(self._set_status_idle)

    def _apply_cell_filter(self, coord: Coordinate) -> None:
        if not self._display_rows:
            return
        row_i, col_i = coord.row, coord.column
        if row_i < 0 or row_i >= len(self._display_rows):
            return
        row = self._display_rows[row_i]
        if col_i == 0:
            self._client_filters.date = row.date
        elif col_i == 1:
            self._client_filters.model = row.model
        elif col_i == 2:
            self._client_filters.provider = row.provider_name
        else:
            self._flash("Enter filters Date, Model, or Provider only")
            return
        self.refresh_table()
