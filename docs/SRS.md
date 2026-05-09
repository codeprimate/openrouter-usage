# Software Requirements Specification: openrouter-usage

**Version:** 0.1.6  
**Living document:** update with intentional spec or code changes.

## 1. Purpose

Terminal UI (TUI) to inspect OpenRouter **management API** usage: filter activity rows, sort columns, and show **combined spend** (OpenRouter credits + BYOK inference) over the **last 30 completed UTC days** of activity data.

**Activity window:** Rows reflect whatever `GET /api/v1/activity` returns (no client-side date range beyond optional API `date` query). The API is understood to expose **completed UTC calendar days** in that window; the **current UTC day may be absent** until it rolls into “completed” aggregates. Row **Date** values are UTC `YYYY-MM-DD`. Default table sort is **Date ascending**, so the **newest day appears at the bottom** unless the user changes sort.

## 2. Scope

### In scope (v1)

- Authenticate with **management key** only (`OPENROUTER_MANAGEMENT_KEY` or `--management-key` / `-k`). The key must be in the **process environment** when the CLI runs (e.g. `export OPENROUTER_MANAGEMENT_KEY=…` or `source` a file that **exports** variables; assignment-only lines in a shell file do not propagate to `uv run`).
- Fetch `GET /api/v1/activity`, `GET /api/v1/keys` (paginated), `GET /api/v1/credits` from `https://openrouter.ai/api/v1`.
- Display credits banner (account), **API key selector** (server filter on next refresh), totals strip (filtered), activity table.
- **Credits + key row:** a single **horizontal** strip: credits text (**`1fr`**) and the key **`Select`** (**compact** style, short placeholder **“API key”**) so the row stays **one line tall** and the table keeps vertical space. The activity **`DataTable`** uses **flex height** below totals.
- **Sort UX (DataTable only):** one **built-in header row** (no duplicate row of sort buttons). **Tab** while the table is focused and the cursor is in **cell** mode switches to **column** cursor mode (whole column highlighted, including the header). **← / →** move the active column; **Enter** applies sort on that column (**`ColumnSelected`**). **Esc** leaves column mode and returns to **cell** cursor on the same table. **Blur** leaving the table also restores **cell** cursor. **Click** a header cell still sorts (**`HeaderSelected`**). Active sort column and direction are shown in header labels (**`^` / `v`**) and in the status strip.
- **Key selector Esc:** With focus on the key control (collapsed or on its dropdown overlay), **Esc** moves focus to the **activity table** (same “exit this mode / return to main grid” idea as Esc from column sort mode). Implemented via **`KeySelect`** / **`KeySelectOverlay`** so Esc is handled when the overlay owns focus.
- **App header:** the default Textual **`Header`** left “icon” is **hidden in CSS**; its Unicode glyph often mis-renders in common fonts/terminals (e.g. as **`o`**).
- Client-side filters: exact match on **date**, **model** (slug), **provider** (`provider_name`, strip only, case-sensitive) from cell drill-down; **`c`** clears all.
- Sort by any column with tie-break: primary column, then **date** descending, then **endpoint_id** lexicographic.
- **Spend** per row = `usage + byok_usage_inference` (USD); single column and total.
- **$/Req** per row = spend ÷ requests when `requests > 0`; table shows **—** when `requests == 0`; values formatted to **three** fractional digits; column appears **after Spend**. Over visible rows, the totals strip also shows a **blended** $/Req (total spend ÷ total requests) when total requests are positive, **after** the Spend aggregate in the sentence order.
- Keyboard (see also **`?`** help overlay):
  - **`Tab`** on the activity table in **cell** mode: enter **column** (sort) mode. **`Tab`** again follows normal focus order (e.g. toward footer). **`Shift+Tab`** follows Textual’s focus chain.
  - In **column** mode: **Esc** returns to **cell** mode; **Enter** sorts the highlighted column.
  - Table **cell** mode: arrows move the cell cursor; **`Enter`** on Date / Model / Provider sets filter; other columns flash a short hint.
  - **`r`** refresh, **`q`** quit, **`?`** help (Esc closes), **`c`** clear filters.
- Help overlay (`?`): keyboard summary plus a **column abbreviation legend** (sourced from **`HELP_COLUMN_LEGEND`** in **`domain`**): Req, Spend, **$/Req**, Pr, Cmp, Rsn with human-readable descriptions.
- Status strip: focus mode (**TABLE** vs **SORT** when column cursor is active, **KEY** on key selector), filters text, M of N rows, sort direction, last refresh time, keys loaded N, stale key banner when selection ≠ last fetch.
- Loading / empty / error states: HTTP API errors (non-2xx), **transport failures** (e.g. timeouts, connection errors via **httpx**), and OS-level errors are surfaced with retry hint; **401** mentions management key / env or **`-k`** (no secrets in UI).

### Out of scope (v1)

- `user_id` org filter on activity.
- Workspace filter on keys.
- Activity beyond 30-day API window; CSV import.
- Chat/completions using a normal API key.

## 3. Definitions

| Term | Meaning |
|------|---------|
| Spend | `usage + byok_usage_inference` for an activity row (USD). |
| **$/Req** | Spend divided by **requests** for that row; undefined at zero requests → table shows **—**; sort uses numeric **0.0** for zero-request rows. |
| Raw rows | Rows returned by last `/activity` fetch (after server `api_key_hash` if any). |
| Visible rows | Raw rows after client-side dimension filters. |
| Req (header) | API **request count** for that row (`requests`). |
| Pr / Cmp / Rsn (headers) | **Prompt**, **completion**, and **reasoning** token counts (`prompt_tokens`, `completion_tokens`, `reasoning_tokens`). |
| Column sort mode | `DataTable` **column** cursor: pick a column for sort; **Esc** or blur restores **cell** cursor. |

## 4. External interfaces

### 4.1 Management API

- Base URL: `https://openrouter.ai/api/v1`
- Header: `Authorization: Bearer <management_key>`
- Endpoints: `/activity` (optional query `date`, `api_key_hash`), `/keys` (optional `offset`, … paginate until empty), `/credits`.

### 4.2 CLI

- `openrouter-usage` / `python -m openrouter_usage`
- `--version` prints the version from **installed package metadata** (the value in **pyproject.toml** `[project].version` when the distribution is built/installed).
- `--management-key` / `-k` overrides `OPENROUTER_MANAGEMENT_KEY`.
- `--help` includes the same version string and documents env; local dev must **export** `OPENROUTER_MANAGEMENT_KEY` into the shell (or pass **`-k`**). Assignment in a non-sourced script does not propagate to `uv run`.

## 5. Functional requirements

1. **FR-001** On start, resolve key (CLI over env); if missing, exit with usage message.
2. **FR-002** On start and on **`r`**, fetch keys (all pages), activity (with current server key hash or none), credits; merge key hash → display name for Select options.
3. **FR-003** Table columns (labels): **Date**, **Model**, **Provider**, **Req**, **Spend**, **$/Req**, **Pr**, **Cmp**, **Rsn** — mapped from API `date`, `model`, `provider_name`, `requests`, spend (usage + BYOK), derived **$/Req**, `prompt_tokens`, `completion_tokens`, `reasoning_tokens`.
4. **FR-004** Totals strip: over **visible** rows, show **Req**, **Spend**, blended **$/Req** (when total request count is positive), and sums of **Pr**, **Cmp**, **Rsn**.
5. **FR-005** Enter on Date/Model/Provider cell sets/replaces filter for that dimension; Enter on other columns flashes help text.
6. **FR-006** Sort: use **DataTable** header + **column** cursor mode (**Tab** from cell mode) or **header click**; **Enter** on the highlighted column sorts (toggle ascending/descending when the same column stays active). Header labels and status show sort indicators.
7. **FR-007** Changing API key Select without refresh shows stale banner until **`r`**.
8. **FR-008** Non-2xx API responses: show error and retry hint; 401 mentions management key and **`OPENROUTER_MANAGEMENT_KEY`** or **`-k`**. **Transport** errors from the HTTP client are shown the same class of user-visible error (message + retry), without leaking secrets.
9. **FR-009** **`?`** help overlay lists keyboard behavior (including **Tab** / **Esc** for sort mode and **Esc** from the key selector), the **column abbreviation legend** aligned with table headers, and the **app version** (same value as **`--version`** / **pyproject** when installed).
10. **FR-010** **Esc** with focus inside the key selector (including open dropdown) moves focus to the activity table and dismisses an open dropdown.

## 6. Non-functional

- **NFR-001** Use **uv** for env (`uv sync`, `uv run`).
- **NFR-002** **Ruff** + **pytest** in dev loop: `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`.
- **NFR-003** Package layout: `openrouter_usage/` (`client`, `domain`, `app`, `main`), `tests/`.
- **NFR-004** **Textual `App` subclass:** do not bind app state to names reserved by Textual’s `App` (e.g. do not use `_filters` for domain “row filters”; use a distinct name such as `_client_filters`).
- **NFR-005** **Version string:** a single runtime source — `importlib.metadata.version("openrouter-usage")` — so **CLI** (`--help`, **`--version`**), **TUI** header (app name then version; header title **right-aligned** so narrow one-line terminals keep the full semver on the right), and **`?`** help show the same value as **pyproject.toml** `[project].version` after a normal install (`uv sync` / wheel).

## 7. Acceptance criteria (v1 smoke)

- With valid key: table shows data or empty message; credits banner populated.
- Filter + clear + sort change visible rows and totals consistently.
- From table **cell** focus, **Tab** enters **column** sort mode; **Esc** returns to **cell** mode; **Enter** in column mode changes sort.
- From key selector focus, **Esc** focuses the activity table.
- `uv run pytest` passes; `uv run ruff check .` passes.

## 8. Development commands

```bash
cd ~/Code/openrouter-usage
export OPENROUTER_MANAGEMENT_KEY=…   # must be exported for uv run / CLI
uv sync --extra dev   # optional: pytest, ruff, build for local checks / make build
uv run ruff check .
uv run ruff format .
uv run pytest
uv run python -m openrouter_usage
# or
uv run openrouter-usage
```
