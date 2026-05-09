"""Tests for openrouter_usage.client."""

import httpx
from openrouter_usage import client as c


def test_fetch_activity_success() -> None:
    class FC(httpx.Client):
        def get(self, url, **kwargs):  # noqa: ANN001
            assert "/activity" in url
            assert "Bearer" in kwargs["headers"]["Authorization"]
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "date": "2024-01-01",
                            "model": "m",
                            "provider_name": "p",
                            "endpoint_id": "e",
                            "requests": 1,
                            "usage": 0.1,
                            "byok_usage_inference": 0.2,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "reasoning_tokens": 0,
                        }
                    ]
                },
            )

    rows = c.fetch_activity("k", client=FC())
    assert len(rows) == 1
    assert rows[0]["model"] == "m"


def test_fetch_activity_error() -> None:
    class FC(httpx.Client):
        def get(self, url, **kwargs):  # noqa: ANN001
            return httpx.Response(401, json={"error": {"message": "bad"}})

    try:
        c.fetch_activity("k", client=FC())
    except c.OpenRouterAPIError as e:
        assert e.status_code == 401
        assert "bad" in str(e)
    else:
        raise AssertionError("expected error")


def test_fetch_all_keys_pagination() -> None:
    calls: list[int] = []

    class FC(httpx.Client):
        def get(self, url, **kwargs):  # noqa: ANN001
            off = kwargs.get("params", {}).get("offset", 0)
            calls.append(int(off))
            if off == 0:
                data = [{"hash": str(i), "name": "n"} for i in range(100)]
            else:
                data = [{"hash": "last", "name": "last"}]
            return httpx.Response(200, json={"data": data})

    keys = c.fetch_all_keys("k", client=FC())
    assert len(keys) == 101
    assert calls == [0, 100]
