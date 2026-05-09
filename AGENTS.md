# Agentic development: openrouter-usage

Guidance for AI agents and humans automating work on this repository. Prefer reading source and tests over guessing behavior.

## What this project is

Python 3.11+ terminal UI (Textual) that calls the OpenRouter **management** API (`/activity`, `/keys`, `/credits`). Layout and behavior live in `openrouter_usage/` (`client`, `domain`, `app`, `main`). Tests live in `tests/`.

## Requirements: SRS first

- **Canonical spec:** `docs/SRS.md` — versioned, living requirements (FR/NFR, UX, API assumptions, acceptance smoke).
- **Planning archive only:** `docs/CURSOR_PLAN.md` — historical snapshot; do not treat it as the current contract when it conflicts with `docs/SRS.md` or the code.
- **SRS management:** When you change user-visible behavior, API usage, or acceptance criteria, update `docs/SRS.md` in the same change set. Bump the **Version** line when the spec meaningfully moves. Keep FR/NFR and acceptance criteria aligned with what `pytest` and manual smoke would verify.

## Workflow (before you edit)

1. Read the relevant sections of `docs/SRS.md` for the feature or bug.
2. Trace behavior in `openrouter_usage/domain.py` (pure logic, filters, sort keys, help legend) and `openrouter_usage/app.py` (Textual wiring, focus, errors).
3. Read or extend tests in `tests/` — they encode expected domain and app contracts.

## Tooling and commands

Use **uv** for the environment and runs (`docs/SRS.md` NFR-001). **`Makefile`** targets **`make install`** / **`make install-dev`** use **`python3 -m pip`** (not uv) so installs follow the interpreter you choose. **`make build`** runs **`python3 -m build`**; install the **`build`** package into that Python first (included in **`[dev]`** extras).

```bash
uv sync --extra dev    # optional dev deps (pytest, ruff, build)
uv run ruff check .
uv run ruff format .
uv run pytest
uv run python -m openrouter_usage
```

Local API access needs `OPENROUTER_MANAGEMENT_KEY` in the process environment (or `-k` / `--management-key`). Shell files must **export** the variable; see SRS and README.

## Versioning (release and UI)

- **Single source:** bump **`pyproject.toml`** `[project].version` only. Do not hardcode a semver elsewhere for user-facing output.
- **Runtime:** `openrouter_usage/version.py` exposes `package_version()` via `importlib.metadata.version("openrouter-usage")` (installed wheel reflects pyproject). `openrouter_usage/__init__.py` sets `__version__` from that call. If the distribution is missing, the code falls back to `0.0.0+unknown`.
- **Surfaces:** CLI **`--version`** and **`--help`** (`main.py`), TUI header (`UsageApp.format_title` + `SUB_TITLE` in `app.py`), and **`?`** help text must stay aligned with the same helper. Header order is **app name · version** with a **right-aligned** title strip so ellipsis does not hide the patch. See **NFR-005** in `docs/SRS.md`.
- **Verify:** `tests/test_version.py` checks metadata matches **`pyproject.toml`**. After changing **`[project].version`**, run **`uv sync`** (or reinstall) so **`importlib.metadata`** inside **`uv run`** picks up the new value, then **`uv run pytest`**.
- **Spec doc:** the SRS **Version** line (document revision) is independent of the package semver. Bump it when requirements text changes meaningfully, not for every patch bump unless the spec moved.

## Best practices (project-specific)

- **Textual `App`:** Do not bind domain or UI state to names reserved by Textual’s `App` (SRS NFR-004). Example: use `_client_filters`, not `_filters`, for row filters.
- **Secrets:** Never print keys or tokens in UI, logs, or test output. Error copy for 401 may remind users to fix `OPENROUTER_MANAGEMENT_KEY` or `-k` without embedding secrets.
- **Spend and $/Req:** Spend is `usage + byok_usage_inference`; $/Req and sort tie-break rules are defined in SRS — match `domain` and tests.
- **HTTP errors:** Surface non-2xx and transport failures with actionable retry hints; use httpx patterns consistent with `client` and `app`.
- **Constants:** Prefer named constants in `domain` or a small dedicated module over magic strings for columns and messages already centralized there.

## Definition of done

- `uv run ruff check .` and `uv run pytest` pass.
- Behavior matches `docs/SRS.md`; spec updated when requirements change.
- New edge behavior gets a focused test unless it is purely visual and covered by existing smoke patterns.

## Quick map

| Area | Primary files |
|------|----------------|
| API client | `openrouter_usage/client.py` |
| Types, spend, filters, sort | `openrouter_usage/domain.py` |
| TUI | `openrouter_usage/app.py` |
| Entry | `openrouter_usage/main.py` |
| Package version | `pyproject.toml`, `openrouter_usage/version.py`, `tests/test_version.py` |
| Tests | `tests/test_domain.py`, `tests/test_app_focus.py`, … |
