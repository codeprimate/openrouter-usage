"""HTTP client for OpenRouter management API."""

from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _auth_headers(management_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {management_key}",
        "Content-Type": "application/json",
    }


def _error_message(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        err = body.get("error")
        if isinstance(err, dict) and "message" in err:
            return str(err["message"])
    except Exception:
        pass
    return resp.text or resp.reason_phrase


def fetch_activity(
    management_key: str,
    *,
    date: str | None = None,
    api_key_hash: str | None = None,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {}
    if date:
        params["date"] = date
    if api_key_hash:
        params["api_key_hash"] = api_key_hash
    own = client is None
    c = client or httpx.Client(timeout=60.0)
    try:
        r = c.get(f"{BASE_URL}/activity", headers=_auth_headers(management_key), params=params)
        if r.status_code != 200:
            raise OpenRouterAPIError(_error_message(r), r.status_code)
        data = r.json()
        return list(data.get("data") or [])
    finally:
        if own:
            c.close()


def fetch_all_keys(
    management_key: str,
    *,
    include_disabled: bool = False,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    own = client is None
    c = client or httpx.Client(timeout=60.0)
    try:
        out: list[dict[str, Any]] = []
        offset = 0
        while True:
            params: dict[str, str | int] = {"offset": offset}
            if include_disabled:
                params["include_disabled"] = "true"
            r = c.get(f"{BASE_URL}/keys", headers=_auth_headers(management_key), params=params)
            if r.status_code != 200:
                raise OpenRouterAPIError(_error_message(r), r.status_code)
            chunk = list(r.json().get("data") or [])
            if not chunk:
                break
            out.extend(chunk)
            if len(chunk) < 100:
                break
            offset += 100
        return out
    finally:
        if own:
            c.close()


def fetch_credits(
    management_key: str,
    *,
    client: httpx.Client | None = None,
) -> dict[str, float]:
    own = client is None
    c = client or httpx.Client(timeout=60.0)
    try:
        r = c.get(f"{BASE_URL}/credits", headers=_auth_headers(management_key))
        if r.status_code != 200:
            raise OpenRouterAPIError(_error_message(r), r.status_code)
        data = r.json().get("data") or {}
        return {
            "total_credits": float(data.get("total_credits") or 0.0),
            "total_usage": float(data.get("total_usage") or 0.0),
        }
    finally:
        if own:
            c.close()
