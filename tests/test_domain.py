"""Tests for openrouter_usage.domain."""

import pytest
from openrouter_usage.domain import (
    COLUMN_LABELS,
    HELP_COLUMN_LEGEND,
    ActivityRow,
    ClientFilters,
    activity_row_from_api,
    aggregate_usd_per_request,
    apply_filters,
    format_int_commas,
    format_row_usd_per_request_cell,
    format_usd,
    format_usd_per_request,
    sort_rows,
    totals,
)


def sample_rows() -> list[ActivityRow]:
    return [
        ActivityRow(
            date="2024-01-02",
            model="a/m",
            provider_name="P1",
            endpoint_id="e1",
            requests=1,
            usage=0.5,
            byok_usage_inference=0.25,
            prompt_tokens=10,
            completion_tokens=20,
            reasoning_tokens=0,
        ),
        ActivityRow(
            date="2024-01-01",
            model="b/m",
            provider_name="P2",
            endpoint_id="e2",
            requests=2,
            usage=1.0,
            byok_usage_inference=0.0,
            prompt_tokens=5,
            completion_tokens=5,
            reasoning_tokens=1,
        ),
    ]


def test_spend() -> None:
    r = sample_rows()[0]
    assert r.spend == 0.75


def test_activity_row_from_api() -> None:
    r = activity_row_from_api(
        {
            "date": "2024-01-01",
            "model": "x",
            "provider_name": "  z  ",
            "endpoint_id": "ep",
            "requests": 3,
            "usage": 1.5,
            "byok_usage_inference": 0.5,
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "reasoning_tokens": 3,
        }
    )
    assert r.provider_name == "z"
    assert r.spend == 2.0


def test_apply_filters_stack() -> None:
    rows = sample_rows()
    f = ClientFilters(date="2024-01-02")
    out = apply_filters(rows, f)
    assert len(out) == 1
    f2 = ClientFilters(date="2024-01-02", model="a/m")
    out2 = apply_filters(rows, f2)
    assert len(out2) == 1


def test_sort_requests_tiebreak_date_desc() -> None:
    # same requests — tie-break by date desc then endpoint_id
    r0 = ActivityRow(
        date="2024-01-02",
        model="a",
        provider_name="P",
        endpoint_id="b",
        requests=5,
        usage=0.0,
        byok_usage_inference=0.0,
        prompt_tokens=0,
        completion_tokens=0,
        reasoning_tokens=0,
    )
    r1 = ActivityRow(
        date="2024-01-01",
        model="b",
        provider_name="P",
        endpoint_id="a",
        requests=5,
        usage=0.0,
        byok_usage_inference=0.0,
        prompt_tokens=0,
        completion_tokens=0,
        reasoning_tokens=0,
    )
    s = sort_rows([r0, r1], "requests", ascending=True)
    assert s[0].date == "2024-01-02"  # newer date first on tie


def test_totals() -> None:
    t = totals(sample_rows())
    assert t["requests"] == 3
    assert t["spend"] == 0.75 + 1.0


def test_aggregate_usd_per_request() -> None:
    assert aggregate_usd_per_request(sample_rows()) == pytest.approx((0.75 + 1.0) / 3.0)


def test_format_row_usd_per_request_cell() -> None:
    r0 = sample_rows()[0]
    assert format_row_usd_per_request_cell(r0) == format_usd_per_request(0.75)
    zero = ActivityRow(
        date="2024-01-03",
        model="z",
        provider_name="P",
        endpoint_id="e",
        requests=0,
        usage=1.0,
        byok_usage_inference=0.0,
        prompt_tokens=0,
        completion_tokens=0,
        reasoning_tokens=0,
    )
    assert format_row_usd_per_request_cell(zero) == "—"


def test_sort_usd_per_request() -> None:
    s = sort_rows(sample_rows(), "usd_per_request", ascending=True)
    assert s[0].date == "2024-01-01"
    assert s[1].date == "2024-01-02"


def test_help_column_legend_uses_real_header_abbrs() -> None:
    labels = set(COLUMN_LABELS)
    for abbr, _desc in HELP_COLUMN_LEGEND:
        assert abbr in labels


def test_format_usd() -> None:
    assert format_usd(0.0) == "$0.00"
    assert format_usd(1234.5) == "$1,234.50"
    assert format_usd(1_000_000.999) == "$1,000,001.00"


def test_format_int_commas() -> None:
    assert format_int_commas(0) == "0"
    assert format_int_commas(999) == "999"
    assert format_int_commas(1000) == "1,000"
    assert format_int_commas(1_234_567) == "1,234,567"
