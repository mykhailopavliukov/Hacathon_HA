# Hackathon Project: Country Facts Guessing Game

A web game where the player guesses a country from facts about it (population rank, GDP, crops, and so on).
The datasets in `data/` are provided for the hackathon.

## Stack (decided)

- **Python only.** No hand-written JS/TS/HTML/CSS, no Node toolchain.
- **Python 3.12+**, managed with [uv](https://docs.astral.sh/uv/).
- **[NiceGUI](https://nicegui.io/)** for UI and server (FastAPI underneath); its Leaflet element renders the map from `shapes.geojson`.
- **ruff** for linting and formatting, **pytest** for tests.
- No database: CSV/GeoJSON are loaded once at startup (`app/data.py`) and kept in memory.

Why NiceGUI: per-player state and event handlers fit a game better than rerun-the-script frameworks (Streamlit),
and it supports map clicks and GeoJSON layers out of the box without any JS.

## Getting started

```bash
git clone <repo-url>
cd Hackathon
uv sync                        # install Python deps into .venv
sh scripts/setup-hooks.sh      # enable shared git hooks (once per clone)
uv run python -m app.main      # run the app at http://localhost:8080
```

Other commands:

```bash
uv run pytest                  # tests
uv run ruff check .            # lint (add --fix to autofix)
uv run ruff format .           # format
```

## Repository layout

```
app/            application code
  main.py       NiceGUI entry point and pages
  data.py       loads and caches the datasets from data/
tests/          pytest tests (game logic is tested without the UI)
data/           provided datasets, read-only (see below)
scripts/        helper scripts (setup-hooks.sh)
.githooks/      shared git hooks: pre-commit, commit-msg
.github/        PR template
pyproject.toml  dependencies and tool config (ruff, pytest)
CLAUDE.md       rules for AI coding agents
```

Keep game logic (hint selection, answer checking, scoring) in plain Python modules under `app/`,
separate from the UI code, so it can be tested without a browser.

## Repository rules

### Branches
- Never commit to `main` directly; every change goes through a PR.
- Name: `<type>/<short-kebab-topic>`, with the same types as commits.
  Examples: `feat/map-guess`, `fix/empty-stats`, `docs/readme`, `chore/ci`.
- Branch from an up-to-date `main`; keep branches short-lived.

### Commits
- [Conventional Commits](https://www.conventionalcommits.org/): `<type>[(scope)]: <imperative summary>`.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Summary: imperative mood, lowercase, no trailing period, at most 100 characters.
  Examples: `feat(game): add progressive hints`, `fix(data): skip empty stats cells`.
- **Atomic commits**: one logical change per commit; the code builds, lints and passes tests at every commit.
  Do not mix refactors with features, or formatting with logic. Put tests in the same commit as the code they cover.
  Split large work into a series of small commits instead of one big one.
- **Short messages only:** the subject line is enough. Add a body only when the *why* is not obvious, and keep it to a line or two.
- **No attribution trailers:** no `Co-Authored-By`, no `Signed-off-by`, and no "Generated with ..." or other AI-tool
  markers in commit messages, PR descriptions, code or docs. Commits and PRs carry the author's own name only.
- Never skip hooks (`--no-verify`) and never force-push shared branches.

### Pull requests
- Use the PR template; keep PRs small and focused on one topic.
- At least one teammate review, CI/hooks green, then squash-merge into `main`
  (the squashed title must follow the commit format).

### Code and documentation
- **Documentation stays minimal.** Add a comment or docstring only where the code cannot say it itself
  (a non-obvious *why*, a constraint, a gotcha). No restating the code, no boilerplate docstrings, no changelog-style comments.
- Keep README and CLAUDE.md short and current; update them when the stack or workflow changes.
- Python only: do not add JS/TS files or frontend build tooling.
- Prefer the standard library and existing dependencies; add a dependency only with a clear reason
  (`uv add <pkg>`, commit `pyproject.toml` and `uv.lock` together).
- Type-hint public functions. Follow `ruff` (line length 100) and `.editorconfig`.

### Data and secrets
- `data/` is read-only source data. The pre-commit hook blocks changes there
  (override deliberately with `ALLOW_DATA_CHANGE=1`). Derived data is produced by a script into a different folder.
- Never commit secrets or `.env` files; commit `.env.example` with placeholders instead.

### Hooks (enabled by `scripts/setup-hooks.sh`)
- **pre-commit**: secret scan, `.env` guard, files over 5 MB, conflict markers/whitespace, `data/` guard, `ruff` check and format check on staged `.py` files.
- **commit-msg**: Conventional Commits format, no co-author/sign-off trailers or AI attribution, short messages only.

## Data

All files are joined on `iso3` (ISO 3166-1 alpha-3; Kosovo is `XKX`, as in the World Bank data).

| File | Contents |
|---|---|
| `countries.csv` | 197 countries: Ukrainian/English names, capital, region, languages, currencies, neighbours, area, centroid, flag |
| `shapes.geojson` | Country outlines (MultiPolygon) with an `iso3` property. Crimea is part of Ukraine |
| `indicators.csv` | Selected indicators and Ukrainian phrase templates (`{rank}` placeholder) |
| `stats.csv` | Indicator values: one row per country, one column per indicator `id` (latest value; empty = no data) |

Known quirk: `stats.csv` has a `vanilla` column with no row in `indicators.csv`.

Sources: [mledoze/countries](https://github.com/mledoze/countries) (ODbL), [Natural Earth](https://www.naturalearthdata.com/) (public domain), [World Bank WDI](https://data.worldbank.org/), [FAOSTAT](https://www.fao.org/faostat/).

## License

Code: [MIT](LICENSE). The datasets in `data/` keep the licenses of their original sources listed above
(notably ODbL for the country metadata, which requires attribution and share-alike for derived databases).
