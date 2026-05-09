# openrouter-usage

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

A small **terminal app** for OpenRouter: see recent usage, your API keys list, and account credits.

## Install

You need **Python 3.11 or newer**. Then:

```bash
pip install git+https://github.com/codeprimate/openrouter-usage.git
```

## Usage

### Run it

OpenRouter expects a **management** key (the one you use for account management in the dashboard, not a model API key).

Put it in your shell so the app can see it. Use **`export`** so it applies to the command you run next:

```bash
export OPENROUTER_MANAGEMENT_KEY=your_key_here
openrouter-usage
```

To pass the key just once, without saving it in the shell:

```bash
openrouter-usage -k 'your_key_here'
```

You can also start with `python -m openrouter_usage`. For flags and version: `openrouter-usage --help` and `openrouter-usage --version`.

### What you will see

- **Account credits** at the top.
- An **API key** menu: view **all keys** together or pick **one key**. The numbers match the last time you pressed **r** to refresh. If you change the menu and a warning says the data is old, press **r** again.
- A **totals** line that adds up only the rows still showing after you filter.
- A **table** of activity: mostly **by calendar day** (in UTC), with model and provider. OpenRouter sends about the **last 30 finished UTC days**; **today** might not appear until that day is included on their side. At first the table is sorted with **older days above** and **newer days below**. You can change that with sorting (below).

Press **?** inside the app for a full key list and short labels for the columns (requests, spend, dollars per request, token columns).

### Narrow the table (filters)

Use **Tab** and **Shift+Tab** until the bottom status line shows **Focus: TABLE** and the arrow keys move **one cell** at a time. Move to a **date**, **model**, or **provider** cell, then press **Enter**. The table keeps only rows that match that value. Press **Enter** again on another cell in those columns to change that filter. **c** clears every filter.

**Mouse:** In terminals that forward mouse events to the app, you can click a cell to focus it, then use **Enter** as above.

### Change the sort order

**With the keyboard**

1. Stay in **Focus: TABLE** with the highlight on **one cell** (not a whole column). Press **Tab** once. The status line switches to **Focus: SORT** and a full column, including its header, is highlighted.
2. Press **←** or **→** to choose which column to sort by.
3. Press **Enter** to apply the sort. Press **Esc** to leave sort mode and go back to moving cell by cell.

While the table has focus, **Tab** again moves focus to the next control (for example the footer). **Shift+Tab** moves backward.

**Mouse:** Click a column header to sort. That does the same thing as sort mode plus **Enter**. Clicking the table can move focus there if your terminal supports it.

### Handy keys

| Key | What it does |
|-----|----------------|
| **r** | Load the latest data from OpenRouter |
| **q** | Exit the app |
| **?** | Open the help panel (**Esc** closes it) |
| **Esc** | Exit "pick a column to sort" mode, or close the key menu and return to the table |

If something goes wrong (network, wrong key, server error), you will get a short message and a tip to try again. Your key is **never** printed on screen.

## Contributing

Bug reports and ideas are welcome in [GitHub Issues](https://github.com/codeprimate/openrouter-usage/issues).

Pull requests are welcome too. Clone the repo, install dev dependencies (`uv sync --extra dev`, or `pip install "git+https://github.com/codeprimate/openrouter-usage.git#egg=openrouter-usage[dev]"` if you prefer pip), then run `uv run ruff check .` and `uv run pytest` (or `make check` after `make install-dev`). Behavior and review expectations are in [docs/SRS.md](docs/SRS.md). [AGENTS.md](AGENTS.md) has notes for contributors and automation in this repo.

**Source:** [github.com/codeprimate/openrouter-usage](https://github.com/codeprimate/openrouter-usage)

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) for the HTTP API this app calls (activity, keys, credits). This project is independent community tooling, not an official OpenRouter product.
- [Textual](https://textual.textualize.io/) for the terminal UI.
- [httpx](https://www.python-httpx.org/) for HTTP.

## Security

If you find a security-sensitive problem, please use [GitHub Security](https://github.com/codeprimate/openrouter-usage/security) (private reporting) instead of a public issue when that is appropriate.
