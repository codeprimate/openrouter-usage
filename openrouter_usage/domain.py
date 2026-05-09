"""Pure logic: activity rows, Spend, filters, sort, totals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_cls
from functools import cmp_to_key
from typing import Literal

SortColumn = Literal[
    "date",
    "model",
    "provider_name",
    "requests",
    "spend",
    "usd_per_request",
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
]


@dataclass(frozen=True)
class ActivityRow:
    date: str
    model: str
    provider_name: str
    endpoint_id: str
    requests: int
    usage: float
    byok_usage_inference: float
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int

    @property
    def spend(self) -> float:
        return self.usage + self.byok_usage_inference


def activity_row_from_api(d: dict) -> ActivityRow:
    return ActivityRow(
        date=str(d["date"]),
        model=str(d["model"]),
        provider_name=str(d.get("provider_name") or "").strip(),
        endpoint_id=str(d.get("endpoint_id") or ""),
        requests=int(d.get("requests") or 0),
        usage=float(d.get("usage") or 0.0),
        byok_usage_inference=float(d.get("byok_usage_inference") or 0.0),
        prompt_tokens=int(d.get("prompt_tokens") or 0),
        completion_tokens=int(d.get("completion_tokens") or 0),
        reasoning_tokens=int(d.get("reasoning_tokens") or 0),
    )


@dataclass
class ClientFilters:
    """Exact-match client filters (any None means inactive)."""

    date: str | None = None
    model: str | None = None
    provider: str | None = None

    def active_parts(self) -> list[str]:
        parts: list[str] = []
        if self.date is not None:
            parts.append(f"date={self.date}")
        if self.model is not None:
            parts.append(f"model={self.model}")
        if self.provider is not None:
            parts.append(f"provider={self.provider}")
        return parts

    def summary(self) -> str:
        if not self.active_parts():
            return "filters: none"
        return " ".join(self.active_parts())


def apply_filters(rows: list[ActivityRow], f: ClientFilters) -> list[ActivityRow]:
    out = rows
    if f.date is not None:
        out = [r for r in out if r.date == f.date]
    if f.model is not None:
        out = [r for r in out if r.model == f.model]
    if f.provider is not None:
        out = [r for r in out if r.provider_name == f.provider]
    return out


def _date_ordinal(row: ActivityRow) -> int:
    try:
        y, m, d = (int(x) for x in row.date.split("-"))
        return date_cls(y, m, d).toordinal()
    except (ValueError, TypeError):
        return 0


def _primary_value(row: ActivityRow, column: SortColumn):
    if column == "date":
        return row.date
    if column == "model":
        return row.model
    if column == "provider_name":
        return row.provider_name
    if column == "requests":
        return row.requests
    if column == "spend":
        return row.spend
    if column == "usd_per_request":
        return row_usd_per_request_sort_value(row)
    if column == "prompt_tokens":
        return row.prompt_tokens
    if column == "completion_tokens":
        return row.completion_tokens
    if column == "reasoning_tokens":
        return row.reasoning_tokens
    raise ValueError(f"unknown column {column}")


def sort_rows(
    rows: list[ActivityRow],
    column: SortColumn,
    ascending: bool,
) -> list[ActivityRow]:
    """Sort by primary column; tie-break: date descending, then endpoint_id lex."""

    def cmp(a: ActivityRow, b: ActivityRow) -> int:
        va = _primary_value(a, column)
        vb = _primary_value(b, column)
        if va != vb:
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                c = (va > vb) - (va < vb)
            else:
                c = (str(va) > str(vb)) - (str(va) < str(vb))
            return c if ascending else -c
        # tie-break: date desc
        da, db = _date_ordinal(a), _date_ordinal(b)
        if da != db:
            return (db > da) - (db < da)
        if a.endpoint_id != b.endpoint_id:
            return (a.endpoint_id > b.endpoint_id) - (a.endpoint_id < b.endpoint_id)
        return 0

    return sorted(rows, key=cmp_to_key(cmp))


def totals(rows: list[ActivityRow]) -> dict[str, float | int]:
    return {
        "spend": sum(r.spend for r in rows),
        "requests": sum(r.requests for r in rows),
        "prompt_tokens": sum(r.prompt_tokens for r in rows),
        "completion_tokens": sum(r.completion_tokens for r in rows),
        "reasoning_tokens": sum(r.reasoning_tokens for r in rows),
    }


def row_usd_per_request_sort_value(row: ActivityRow) -> float:
    """Numeric value for sorting; zero requests sorts as 0.0."""

    if row.requests <= 0:
        return 0.0
    return row.spend / row.requests


def aggregate_usd_per_request(rows: list[ActivityRow]) -> float | None:
    """Blended spend divided by total requests over filtered rows, or None if no requests."""

    t = totals(rows)
    req = int(t["requests"])
    if req <= 0:
        return None
    return float(t["spend"]) / float(req)


USD_PER_REQUEST_DECIMALS = 3


def format_usd_per_request(amount: float) -> str:
    """Format dollars-per-request to a fixed number of fractional digits (see constant)."""

    d = USD_PER_REQUEST_DECIMALS
    return f"${amount:,.{d}f}"


def format_row_usd_per_request_cell(row: ActivityRow) -> str:
    """Table cell: em dash when request count is zero."""

    if row.requests <= 0:
        return "—"
    return format_usd_per_request(row.spend / row.requests)


COLUMN_KEYS: tuple[SortColumn, ...] = (
    "date",
    "model",
    "provider_name",
    "requests",
    "spend",
    "usd_per_request",
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
)

COLUMN_LABELS: tuple[str, ...] = (
    "Date",
    "Model",
    "Provider",
    "Req",
    "Spend",
    "$/Req",
    "Pr",
    "Cmp",
    "Rsn",
)

# Shown in table headers and status when ascending vs descending sort is active.
SORT_ASC_INDICATOR = "^"
SORT_DESC_INDICATOR = "v"

# Shown on help overlay; keys match COLUMN_LABELS where abbreviated or jargon.
HELP_COLUMN_LEGEND: tuple[tuple[str, str], ...] = (
    ("Req", "API request count for that row"),
    ("Spend", "USD: OpenRouter usage + BYOK inference"),
    ("$/Req", "Spend divided by requests for that row (— if requests is 0)"),
    ("Pr", "Prompt (input) tokens"),
    ("Cmp", "Completion (output) tokens"),
    ("Rsn", "Reasoning tokens (when the model reports them)"),
)


def format_usd(amount: float) -> str:
    """Format a USD amount with $, thousands separators, and two decimal places."""
    return f"${amount:,.2f}"


def format_int_commas(n: int) -> str:
    """Format an integer with thousands separators (ASCII comma)."""
    return f"{n:,}"


def column_index_to_key(idx: int) -> SortColumn:
    return COLUMN_KEYS[idx]
