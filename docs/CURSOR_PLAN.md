<!-- Archived 2026-05-09 from ~/.cursor/plans/openrouter_usage_tui_fcdc7ee7.plan.md -->
---
name: OpenRouter usage TUI
overview: "Research shows OpenRouter’s “management” surface is a small REST API under `https://openrouter.ai/api/v1/`, authenticated with your management key as `Authorization: Bearer <key>`. A Python TUI can call `/activity`, `/keys`, and `/credits`, then filter and aggregate client-side; you confirmed API-only (30-day activity window) is sufficient. Before SRS, the approved Cursor plan is copied into the project repo as a frozen markdown archive; then SRS-first delivery under ~/Code/openrouter-usage, then code. The project uses uv, ruff, and pytest throughout development."
todos:
  - id: plan-archive
    content: "Before SRS: copy this Cursor plan from .cursor/plans/ (openrouter_usage_tui_*.plan.md) to ~/Code/openrouter-usage/CURSOR_PLAN.md; optional one-line header with copy date; do not edit in place—archive only"
    status: in_progress
  - id: srs-spec
    content: "After CURSOR_PLAN.md exists: create ~/Code/openrouter-usage/SRS.md from plan + archive; maintain and revise SRS during development as understanding improves"
    status: pending
  - id: uv-project
    content: "Complete uv project under ~/Code/openrouter-usage: pyproject + uv.lock, Directory layout package/tests, uv add textual httpx, uv add --dev pytest ruff, [project.scripts] openrouter-usage; document uv run in SRS (minimal uv init may be first step of bootstrap before CURSOR_PLAN.md)"
    status: pending
  - id: quality-tooling
    content: Configure ruff (lint+format) and pytest in pyproject; add tests alongside each feature (pure logic first, mocked HTTP for client); run uv run ruff check . and uv run pytest habitually; optional CI later
    status: pending
  - id: client-module
    content: Add small OpenRouter client (GET activity/keys/credits, Bearer auth, typed parsing or TypedDict); pytest coverage for parsing, errors, and query params (mocked transport)
    status: pending
  - id: tui-shell
    content: "Build TUI: DataTable with header+body focus modes; arrow nav; Enter=sort on header / filter-from-cell on date|model|provider; clear-filters key; single Spend column (usage+byok_usage_inference) and matching footer total; refresh"
    status: pending
  - id: key-mapping
    content: Merge /keys hashes with activity when filtering by key or displaying key names
    status: pending
  - id: config-env
    content: "Resolve management key: default from env OPENROUTER_MANAGEMENT_KEY; override if CLI flag is set (e.g. --management-key / -k); fail fast with clear message if unset after merge; --help notes exporting the key for uv run"
    status: pending
  - id: ux-affordances
    content: "Implement inventory outcomes: status strip (focus, filters, M/N, sort, refresh time); loading disables r; stale key banner; credits vs activity labels; ? overlay; scroll-into-view for cursor; focus ring on API key Select; Enter no-op flash; optional c when no filters; mouse optional on Select only"
    status: pending
isProject: false
---

# OpenRouter management API research and TUI direction

## Script naming and location

- **Project directory:** **`~/Code/openrouter-usage`** — all implementation for this TUI lives here (its own folder/repo), not under `misc_scripts`.
- **Python distribution name / import package:** **`openrouter_usage`** (a **small package**, not a single giant script file—see **Directory layout** below).
- **Python toolchain:** use **[uv](https://docs.astral.sh/uv/)** in this folder only—`pyproject.toml` + **`uv.lock`**, dependencies added with **`uv add`**, runs with **`uv run …`**. Do not rely on ad hoc global `pip install` for project deps.
- **Run locally:** `cd ~/Code/openrouter-usage && uv run python -m openrouter_usage …` (CLI flags per Configuration), and/or **`uv run openrouter-usage …`** once **`[project.scripts]`** maps `openrouter-usage` → **`openrouter_usage.main:main`** (or equivalent).
- **Installed CLI:** **`[project.scripts]`** in `pyproject.toml`: `openrouter-usage = "openrouter_usage.main:main"` (exact callable name to match implementation).
- **In-app title / window chrome:** use **`openrouter-usage`** (or `OpenRouter usage`) consistently with the installed CLI name so the running process is easy to spot in the window list and terminal title.

### Modularization level (intent)

- **Appropriate for a “script-grade” product:** one **installable package** with a **few modules** separated by responsibility—not a monolithic `openrouter_usage.py`, and not deep layered architecture (no `services/repositories/factories` unless the project outgrows this plan).
- **Split when:** a file becomes hard to navigate (~300+ lines or mixed concerns), or Textual widgets deserve their own file—**defer** `widgets/` / `screens/` until that threshold.
- **Keep pure logic out of the UI:** HTTP and JSON live in **`client`**, row math (Spend, filter, sort, tie-break) in **`domain`** (or similarly named), Textual wiring in **`app`** (+ optional small **`widgets`** later).

## Directory layout (`~/Code/openrouter-usage`)

Planned tree (v1). Paths are relative to the project root.

```
openrouter-usage/
├── CURSOR_PLAN.md               # frozen copy of this Cursor plan (written before SRS.md)
├── SRS.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── README.md                    # optional; brief run + dev commands if you want
│
├── openrouter_usage/            # import package (editable install / uv run -m)
│   ├── __init__.py              # version string optional; re-export main if useful
│   ├── __main__.py              # entry for: python -m openrouter_usage
│   ├── main.py                  # argparse / key resolution; calls into app.run()
│   ├── client.py                # httpx Management API: activity, keys, credits
│   ├── domain.py                # pure: Spend, filter rows, sort + tie-break, totals
│   └── app.py                   # Textual App: layout, focus modes, key bindings, widgets inline
│
└── tests/
    ├── conftest.py              # shared fixtures (e.g. sample JSON, mock client) as needed
    ├── test_domain.py
    ├── test_client.py
    └── test_app.py              # minimal; expand only if high-value pilot tests
```

**Notes:**

- **No `src/` layout** for v1—keeps `uv` and imports simple (`openrouter_usage` package sits at repo root).
- **`domain.py`** holds everything testable without Textual or the network; **`client.py`** is IO-only; **`app.py`** owns UI state and delegates to **`domain`** / **`client`**.
- If **`app.py`** grows large, extract **`openrouter_usage/widgets/`** (e.g. `activity_table.py`, `status_bar.py`) in a later revision and update this layout in `SRS.md`.
- **Ruff / pytest** configuration lives in **`pyproject.toml`** `[tool.ruff]` / `[tool.pytest.ini_options]` unless you prefer a tiny `ruff.toml`.

## SRS-first development process

### Plan archive (historical persistence, **before** `SRS.md`)

- **Action:** copy the **approved Cursor plan** (this document: typically **`~/.cursor/plans/openrouter_usage_tui_*.plan.md`** on the machine where planning happened, or the same file from the workspace’s **`.cursor/plans/`** if checked in) into the project folder as **`~/Code/openrouter-usage/CURSOR_PLAN.md`**.
- **Purpose:** preserve the **full planning narrative** (research, UX decisions, directory layout, tooling) inside the repo even if the Cursor plan store moves or is pruned. **`CURSOR_PLAN.md` is a snapshot—do not treat it as the living spec** (living spec = **`SRS.md`**).
- **Optional:** prepend one line, e.g. `<!-- Copied YYYY-MM-DD from Cursor plan: … -->`, then the raw markdown body.
- **Ordering:** this copy happens **after** the project folder exists (e.g. minimal **`uv init`**) and **strictly before** the first meaningful write to **`SRS.md`**. Never overwrite **`CURSOR_PLAN.md`** with the SRS; keep two files.

### SRS (living requirements)

**Before any application code:** create a **Software Requirements Specification (SRS)** document in the project folder **`~/Code/openrouter-usage`**.

- **Primary artifact:** **`SRS.md`** at the project root (alongside **`CURSOR_PLAN.md`**, **`openrouter_usage/`**, **`tests/`**). Alternative: `docs/SRS.md` if you prefer a `docs/` layout—pick one location and keep the SRS there for the lifetime of the project.
- **Initial content:** distill **`CURSOR_PLAN.md`** (and this plan) into the SRS—scope, user-facing behavior, keyboard model, API endpoints, data definitions (e.g. `Spend`), non-goals, acceptance-style requirements, and affordance/signifier expectations. The first draft **does not need to be perfect**; it is the baseline to implement against.
- **During development:** **update and revise `SRS.md` whenever** behavior, UX, error handling, or API details change or become clearer. Treat mismatches between code and SRS as either a **bug in code** or an **intentional spec change**—in the latter case, edit the SRS in the same PR/session as the code change so the SRS remains the authoritative requirements view for the repo.
- **Ordering rule (bootstrap):** **`uv init`** (minimal) → **`CURSOR_PLAN.md`** (copy) → **`SRS.md`** (initial) → application code. No substantial feature work until **`SRS.md`** exists and names v1 scope.
- **Quality in the SRS:** the SRS should name the **canonical dev commands** (e.g. `uv run ruff check .`, `uv run ruff format .`, `uv run pytest`) and state that **tests and lint are part of routine development**, not a final-phase bolt-on.

## Quality: linting and pytest (throughout development)

**Goal:** faster feedback, fewer regressions, and a codebase that stays easy to change while the SRS evolves.

- **Lint / format:** use **[Ruff](https://docs.astral.sh/ruff/)** as the primary **linter and formatter** (`uv add --dev ruff`). Run **`uv run ruff check .`** and **`uv run ruff format .`** (or `ruff format --check` in CI) regularly—ideally before every commit; wire into editor if desired. Add **`ruff.toml`** / `[tool.ruff]` in `pyproject.toml` only as much as defaults need tuning.
- **Tests:** use **`pytest`** (`uv add --dev pytest`). Run **`uv run pytest`** often while building features.
- **When to write tests:** **alongside** (or immediately after) each slice of behavior—e.g. **`Spend`** derivation, client JSON parsing, filter/sort/tie-break logic, query-string building for `/activity`—not deferred to the end. For the TUI, prioritize **fast unit tests** on pure functions and **HTTP tests** with **`httpx` mocked** or `respx` / `pytest-httpx` if added; add **minimal pilot tests** for Textual only where high value (complex key routing), to avoid brittle full-screen tests dominating runtime.
- **SRS linkage:** when acceptance criteria in `SRS.md` change, update or add tests in the **same change** when practical so the SRS, code, and tests move together.
- **Optional later:** type checking (**ty**, **mypy**, or **pyright**), **`uv run`** in CI, pre-commit hook calling ruff + pytest—omit from v1 unless desired; the plan does not require them.

## How the “management UI” is really exposed

OpenRouter does not document a separate private browser API for the settings/activity dashboards. What you want is the **Management API**: normal HTTPS JSON endpoints on the same host as the public API, using the **management key** only for admin reads/writes (not for chat completions).

Per [Management API Keys](https://openrouter.ai/docs/guides/overview/auth/management-api-keys):

- Create the key at [openrouter.ai/settings/management-keys](https://openrouter.ai/settings/management-keys).
- **Management keys cannot** call completion/chat routes; they are for administrative operations.
- Authenticate every request with:

```http
Authorization: Bearer <your_management_key>
```

Optional: `Content-Type: application/json` for bodies (list/get are GET-only).

The docs also point to machine-readable indexes: [llms.txt](https://openrouter.ai/docs/llms.txt) and [llms-full.txt](https://openrouter.ai/docs/llms-full.txt) for exhaustive endpoint lists.

## Endpoints relevant to “filter and total usage”


| Endpoint                                    | Role                                           | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET https://openrouter.ai/api/v1/activity` | **Primary breakdown** for a TUI table          | Returns `{ "data": [ ActivityItem, ... ] }`. Each row: `date`, `model`, `model_permaslug`, `endpoint_id`, `provider_name`, `requests`, `prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `usage` (USD OpenRouter credits), `byok_usage_inference` (USD external/BYOK). **Server filters:** `date` (single `YYYY-MM-DD` in last 30 days), `api_key_hash`, `user_id` (orgs). Docs: [Get user activity](https://openrouter.ai/docs/api/api-reference/analytics/get-user-activity). |
| `GET https://openrouter.ai/api/v1/keys`     | **Per-key rollups** + hash for activity filter | Each key: `hash`, `name`, `label`, limits, `usage` / `usage_daily` / `usage_weekly` / `usage_monthly`, parallel `byok_`*. Query: `offset`, `workspace_id`, `include_disabled`. Docs: [List API keys](https://openrouter.ai/docs/api/api-reference/api-keys/list). Guide notes **100 keys per page** and `offset` pagination.                                                                                                                                                            |
| `GET https://openrouter.ai/api/v1/credits`  | **Account totals**                             | `{ "data": { "total_credits", "total_usage" } }`. Docs: [Get remaining credits](https://openrouter.ai/docs/api/api-reference/credits/get-credits).                                                                                                                                                                                                                                                                                                                                      |


**Important limitation (matches your choice):** `/activity` covers the **last 30 completed UTC days** only—not the full range of filters on the human [Activity page](https://openrouter.ai/activity) (which supports longer windows and export). The API still returns `usage` (OpenRouter credits, USD) and `byok_usage_inference` (BYOK inference, USD) separately; the TUI will **derive a single `Spend` column** as `usage + byok_usage_inference` per row and use that for display, footer totals, and sorting—no separate OR/BYOK columns in the grid.

## Suggested data flow for the TUI

```mermaid
flowchart LR
  MK[Management_key]
  subgraph api [OpenRouter_api_v1]
    A[/activity]
    K[/keys]
    C[/credits]
  end
  TUI[Python_TUI]
  MK --> TUI
  TUI --> A
  TUI --> K
  TUI --> C
  A --> agg[Filter_and_aggregate]
  K --> agg
  C --> header[Account_summary_bar]
```



1. **Fetch** `/activity` (optionally with `date` or `api_key_hash` when the user picks a day or key).
2. **Resolve key names** via `/keys` (map `hash` → `name`/`label`) for nicer filters.
3. **Fetch** `/credits` once for a header: purchased vs used (and derived remaining if you subtract).
4. **Filter in the TUI** using **drill-down from cells** (date / model / provider exact match to that cell’s value) plus optional **API key** control for server-side `api_key_hash` on fetch; numeric columns are not filter targets from cells in v1.
5. **Totals row**: over the filtered subset, sum `**Spend`** (`usage + byok_usage_inference`), `requests`, and token fields; do not show separate OR vs BYOK subtotals in v1.

## Configuration (management key)

- **Environment variable:** `OPENROUTER_MANAGEMENT_KEY` — default source when present.
- **CLI override:** e.g. `--management-key` / `-k <value>` — if passed, it **wins** over the env var (non-empty value only).
- **Precedence:** CLI wins over env when the flag is provided with a non-empty value. If no key is available after merge, exit with a short usage hint (document both mechanisms in `--help`).

### Local development (this machine)

- Before running the TUI during development, **export** `OPENROUTER_MANAGEMENT_KEY` in the same shell (or pass **`-k`**) so the process sees the management key.
- This script’s management endpoints only **consume** the management key; having the regular OpenRouter API key in the environment is for your broader dev workflow and other tools, not required for the TUI’s HTTP calls unless you later add features that need it.
- **Agents / contributors:** when running or testing the app from a terminal, prefix the session with sourcing that file if keys are not otherwise set (do not read or paste the file contents into the repo or chat).

## Proposed TUI layout (single main screen)

ASCII wireframe (table-centric; filters mostly implicit from the grid):

```
+-- openrouter-usage --------------------------------------------------------+
| Credits: $used / $purchased  (remaining ~$rem)     Activity: last 30d UTC |
+---------------------------------------------------------------------------+
| API key (server filter on refresh):  [ All keys                          v] |
+---------------------------------------------------------------------------+
| Totals (filtered rows):  Spend $…  Req …  Prompt/Comp/Reason tok …         |
+---------------------------------------------------------------------------+
| >Date< | Model | Provider | Req | Spend | Pr | Cmp | Rsn |
|--------+-------+----------+-----+-------+----+-----+-----|
|  …     | …     | …        | …   | …     | …  | …   | …   |
+---------------------------------------------------------------------------+
| Tab: header <-> body   Enter: sort (header) / filter (body: Date|Model|Prov)|
| c clear filters   ? help   r refresh   q quit   | status: TABLE  M/N rows |
+---------------------------------------------------------------------------+
```

## Keyboard interaction (accepted direction)

Two **focus modes** on the same table so arrow keys have unambiguous meaning:

### A) Header row focused (`Tab` from body; initial focus stays **body** per sanity check—Tab reaches header)

- **Left / Right:** move **column focus** across header cells (visual highlight on the active column).
- **Enter:** **sort** the table by that column (toggle ascending / descending on repeat Enter; show indicator on header).
- **Down:** move focus into the **body** (same column index preserved if possible).

### B) Body (data rows) focused (`Tab` from header, or `Down` from header)

- **Up / Down:** move **row selection** (cursor).
- **Left / Right:** move **column selection** within the current row (highlight active cell).
- **Enter:** if the active column is one of `**Date`**, `**Model**` (slug), or `**Provider**`, apply a **filter** so only rows matching that cell’s **exact** value remain (replace any previous filter for that dimension). Stack filters across dimensions: e.g. filter date then model narrows further.
- **Enter** on other columns (requests, **Spend**, tokens, etc.): **no-op** (or brief status message), so drill-down stays predictable.
- **Tab:** return focus to **header** (for sorting without changing filters).

### Clear filters

- `**c`:** **clear all** client-side filters (date / model / provider) at once; table returns to full in-memory dataset for the current fetch. Does not change API key selection or management key.
- Optional: document in footer that `**c**` is “clear filters” (not “clear screen”).

### Other keys (align with earlier plan)

- `**r`:** refresh from network (`/activity`, `/keys` paginated, `/credits`); reapply current API key server filter; then reapply any active client filters to the new payload.
- `**q`:** quit.

### Implementation note

- **Textual** `DataTable` can support cursor and column cursor; wiring **header vs body** may require either two coordinated widgets or custom key handlers that track `focus_region` (`header`|`body`). If header column navigation is awkward in `DataTable`, fallback: a thin custom grid on `rich` + manual cursor state—prefer the simplest widget that can deliver Left/Right header + body cell focus reliably.

### API key row (kept above the grid)

- Still use a **single** “API key” selector above the table: changing it affects the **next** `GET /activity?api_key_hash=…` (and refresh). It is **not** toggled by Enter-on-cell (activity rows are aggregated by endpoint, not per key in the public schema—unless you later add a column from joined metadata).

### Combined spend (simplification)

- **Per activity row:** `Spend = usage + byok_usage_inference` (both USD fields from the API).
- **UI:** one **Spend** column + one **Spend** subtotal in the totals strip; sort-by-Spend uses this derived value.
- **Credits banner:** keep `**GET /credits**` `total_usage` / `total_credits` as returned by OpenRouter (account-level; may not equal the sum of activity `Spend` over 30d—no need to reconcile in v1; optional small note in `--help` or footer if confusing).

## Implementation notes (when you leave plan mode)

- **Project path:** create or use **`~/Code/openrouter-usage`** as the working tree; follow **Directory layout** (package `openrouter_usage/`, `tests/`) (aligns with Script naming and location above).
- **Plan archive gate:** copy this plan to **`CURSOR_PLAN.md`** in the project root **before** authoring **`SRS.md`** (see **Plan archive** in SRS-first process).
- **SRS gate:** follow **SRS-first development process** above—write **`SRS.md`** after the archive, then implement; keep the SRS current as the spec evolves.
- **uv:** all installs and interpreter use go through **`uv`** in `~/Code/openrouter-usage` (`uv sync`, `uv add`, `uv run`); CI or agents should assume uv is available.
- **Lint and tests:** **`uv run ruff check .`**, **`uv run ruff format .`**, **`uv run pytest`** are part of the default development loop; see **Quality: linting and pytest**.
- **Dev shell:** document in `--help` that developers must **export** `OPENROUTER_MANAGEMENT_KEY` (or use **`-k`**) for the CLI and `uv run`.
- **HTTP client:** `httpx` or `urllib.request` (stdlib); key from env/CLI only, never committed.
- **Errors:** Handle `401`/`403`/`429` from OpenAPI-shaped JSON (`error.message`).
- **TUI stack:** `textual` or `prompt_toolkit` + a simple table; both work with async refresh if you use `httpx.AsyncClient`.
- **No browser automation** unless you explicitly need UI-only features (e.g. one-click CSV export); the documented API is the stable path.

## Specification and UX sanity check

### Resolved ambiguities (pin these in implementation)


| Topic                         | Decision                                                                                                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model column**              | Display and filter on API field `**model**` (slug). Do not use `model_permaslug` in v1 unless a second column is added later.                                                                                                                           |
| **Provider column**           | Map to `**provider_name**`. Filter value is **exact string match** after **strip** only; **case-sensitive** unless we discover inconsistent casing from API (then revisit).                                                                             |
| **Date filter**               | Filter on `**date**` string (`YYYY-MM-DD`) exact match to the cell; all filtering is over the **last in-memory fetch** (30d window unless you add optional `?date=` on refresh later).                                                                  |
| **Initial focus**             | Start in **body** (table) so arrows immediately move rows; first **Tab** jumps to **header** for column sort. Alternative (header-first) is OK if documented in footer—pick one and stick to it.                                                        |
| **Up/Down at boundaries**     | **Stop** at first/last row (no wrap). **Up** on the **first body row** optionally moves focus to **header** on the same column index (nice affordance); if hard to implement, document that user must **Tab** to header.                                |
| **Sort tie-break**            | When two rows compare equal on the sort column, secondary sort by `**date**` desc then `**endpoint_id**` lexicographic for stable ordering.                                                                                                             |
| **Token columns**             | Fixed set in v1: **Prompt**, **Completion**, **Reasoning** (three columns), matching API integers; totals strip sums the same three over filtered rows.                                                                                                 |
| **API key dropdown vs fetch** | Track `**last_fetched_api_key_hash**` (sentinel for “all”). If current selection ≠ last fetched, show `**[!] Key filter changed — press r**` in the status strip **or** auto-refresh on change (pick one; banner is safer against accidental rate use). |
| **Credits banner semantics**  | Label explicitly: e.g. `**Credits (account): used … / purchased …**` so users do not expect it to equal **Activity total (30d, filtered): Spend …`** in the totals strip.                                                                               |
| **Env name**  | Implementation reads `**OPENROUTER_MANAGEMENT_KEY`** only for this app; `--help` documents export vs **`-k`**.           |


### Remaining product limits (document in `--help` / `?`)

- `**user_id`** query for org accounts is **out of scope v1** (no UI control).
- **Workspace** filter on `/keys` is **out of scope v1** unless added explicitly.
- Activity window remains **30 completed UTC days**; no “custom range” without a future export/import feature.

### Major UX misses — affordances to implement

1. **Always-visible status strip** (footer or second line under totals): **focus mode** (`TABLE` / `HEADER`), **active filters** as compact chips or text (`date=… model=…` or `none`), **row count** `showing M of N`, **sort** `Spend v` / `Date ^`, last **refresh time** (local clock).
2. **Loading**: on startup and `**r`**, disable duplicate refresh and show `**Loading…**` (spinner optional); restore table or error when done.
3. **Empty states**: **0 rows after filters** → message `**No rows match filters (c to clear)`**; **0 rows from API** → `**No activity in window`**.
4. **Errors**: non-2xx or parse failure → **replace or overlay** main area with **message + `r` retry**; **401** text should hint `**OPENROUTER_MANAGEMENT_KEY`** / **`-k`** without echoing secrets.
5. **Enter no-op feedback**: on **Spend / Req / tokens**, show **1–2s status flash**: `**Enter filters Date, Model, or Provider only`**.
6. `**?` key**: toggle or pop a **short keybinding cheat sheet** (same content as footer, expanded)—reduces memorization cost.
7. **Quit**: `**q`** with **no confirmation** in v1 (no unsaved state); if you add export later, revisit.
8. **Wide table**: ensure **horizontal scroll** follows **cursor column** so Spend/tokens are reachable on small terminals.
9. **Key list >100**: paginate `/keys` until empty; show `**Keys loaded: N`** in status after merge so user knows pagination finished.

### Spec/UX risks to watch during buildj

- **Textual `DataTable` + header focus**: if library fights custom header/body Tab model, ship a **minimal** version (body-only + **sort mode** on `Shift+Enter` or separate row of sort hotkeys) rather than blocking—document deviation from plan in README only if unavoidable (user prefers minimal extra markdown; a one-line comment in code is enough).
- **Rate limits (429)**: backoff message and **retry** hint on `**r`**.

## Affordance and signifier inventory

*Affordance* = action the UI supports. *Signifier* = perceptible cue that the action exists or how state reads. This table sanity-checks **coverage** and **gaps** for v1.

### Primary affordances (interactive)


| Affordance                                   | Control                                 | Signifier (planned)                                                       | Gap / mitigation                                                                                                                         |
| -------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Move row cursor                              | `↑` `↓` in **TABLE**                    | Highlighted row; table scrolls                                            | **Scroll-into-view**: if cursor moves off-screen, auto-scroll so the row is visible (otherwise affordance exists but signifier is lost). |
| Move column cursor (body)                    | `←` `→` in **TABLE**                    | Highlighted cell                                                          | Same for **horizontal scroll** when columns clip.                                                                                        |
| Move column focus (header)                   | `←` `→` in **HEADER**                   | Header cell highlight + **^ / v** (or ▲/▼) on sorted column               | **Discoverability**: user must **Tab** into header—footer + `**?*`* must state this.                                                     |
| Sort by column                               | `Enter` in **HEADER**                   | Sort glyphs on header + status strip `Sort: Col ^`                        | First visit: brief **?** panel lists “Tab → header → Enter”.                                                                             |
| Add/replace filter (date / model / provider) | `Enter` on drill-down cell in **TABLE** | Status strip shows `date=…`, `model=…`, `provider=…` (or `filters: none`) | **No per-dimension clear** in v1: signifier text should say `**c` clears all** whenever any filter active.                               |
| Clear all client filters                     | `c`                                     | Footer lists `c`; filters disappear from strip                            | Optional: `**c` with no filters** → flash `No active filters` so `c` is not a silent no-op.                                              |
| Refresh network data                         | `r`                                     | `Loading…` disables duplicate refresh; **last refresh time** in status    | **Busy state**: if `r` ignored while loading, status line says `**Loading… (r queued)`** or simply `**Loading…**`—never silent ignore.   |
| Change API key server filter                 | `Select` widget + `**r**`               | `[!] Key filter changed — press r` when selection ≠ last fetch            | **Select focus**: visible **focus ring** when Tab lands on Select so user knows this row is actionable separately from the grid.         |
| Discover bindings                            | `?`                                     | Footer shows `? help`; overlay repeats + expands                          | **Overlay focus**: Esc closes `**?`** and returns focus to prior widget (signifier: title bar “Help (Esc to close)”).                    |
| Quit                                         | `q`                                     | None (instant exit)                                                       | **Risk**: accidental quit—accepted in v1; `**?`** can note “no save”.                                                                    |


### Read-only / interpretive affordances (no direct edit)


| Affordance                                               | Signifier                                                                                    | Gap / mitigation                                                                                                                                 |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Understand **Spend** is combined OR+BYOK                 | Column header `**Spend`**; `**?**` line: “Spend = OpenRouter credits + BYOK inference (USD)” | Avoid bare `$` without column context in totals strip—keep `**Spend (sum):**` prefix.                                                            |
| Distinguish **account credits** from **activity totals** | Banner label `**Credits (account):`** vs totals strip `**Activity (filtered):**`             | Already in sanity check—treat as **required** signifiers, not optional.                                                                          |
| Know **time window**                                     | `**Activity: last 30d UTC`** in banner                                                       | Add **fetched row count** `N rows` next to it after refresh so “empty API” vs “filtered empty” is easier to reason about (pairs with M/N below). |
| Know **keys loaded** for dropdown                        | Status `**Keys loaded: N`** after pagination                                                 | If `N=0`, warn **No keys returned** (unlikely but signifier for broken token).                                                                   |


### System states (must be readable)


| State                                                     | Signifier                                                      | Notes                                                                                          |
| --------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **TABLE** vs **HEADER** vs **Select** vs **Help overlay** | Status `Focus: TABLE` / `HEADER` / `KEY` / `HELP`              | Reduces “wrong Enter” confusion.                                                               |
| **Filters active**                                        | `date=…` etc. or `filters: none`                               | Single source of truth next to M/N.                                                            |
| **Loading**                                               | Replace table body or dim + `Loading…`; `r` disabled or queued | Do not leave old data without a **Stale** or **Loading** label if new fetch replaces in place. |
| **Error**                                                 | Full-width message + `r` retry + HTTP/code                     | **401**: hint env/CLI key; no secret echo.                                      |
| **Empty (unfiltered)**                                    | `No activity in window`                                        | Distinct copy from filtered empty.                                                             |
| **Empty (filtered)**                                      | `No rows match filters (c to clear)`                           | Ties signifier to `**c`**.                                                                     |


### Sanity check summary (based on inventory)

- **Strong**: Stale API-key banner, credits vs activity labeling, `?`, status strip dimensions (focus, filters, sort, refresh time), Enter flash on wrong column, loading/empty/error patterns.
- **Must add vs earlier prose**: explicit **scroll-into-view** for row and column cursor; **focus ring / Focus: KEY** when the API key `Select` is active; **Esc closes `?`**; **Spend** semantics in `**?`** one-liner; **busy `r`** behavior spelled out.
- **Residual risk**: **Mouse-first users**—keyboard is primary; minimum mitigation is **Tab order** `Select → table` documented in `**?`**, optional mouse on `Select` only if zero-cost in framework.
- **Residual risk**: **Accidental `q`**—accepted; no new signifier unless you add `**Shift+q**` quit later.

## References (official)

- [Management API Keys guide](https://openrouter.ai/docs/guides/overview/auth/management-api-keys)
- [GET /api/v1/activity](https://openrouter.ai/docs/api/api-reference/analytics/get-user-activity)
- [GET /api/v1/keys](https://openrouter.ai/docs/api/api-reference/api-keys/list)
- [GET /api/v1/credits](https://openrouter.ai/docs/api/api-reference/credits/get-credits)
- [Activity export (web-only context)](https://openrouter.ai/docs/cookbook/administration/activity-export) — useful to understand how UI metrics relate to API fields, not required for API-only scope.

