# Hackathon Project: Country Facts Guessing Game

A web game where the player guesses a country from facts about it (population rank, GDP, crops, and so on).
The datasets in `data/` are provided for the hackathon.

## Hackathon context

Team of 5 KSE students at the Python hackathon of course CS201. About 3.5 hours of work, then a defence.

**Rules**
- Theme: Open Data. Python is the main language and holds all the logic; HTML/CSS only for display, JS minimal and without logic.
- Defence: a 1-2 minute demo. Anyone on the team must be able to explain any part of the code.
- Grading: working program 6, code quality 4 (functions, clear names, no repetition), idea 3, Git 1 (commits from different people), demo 1.
- Stability comes first: build a minimal working version, then add bonuses.

**Idea:** guess the country from hints. Hints open one by one, from vague to precise; the earlier the guess, the more points.

**Team rules**
- Everyone commits only their own files, often, with proper messages.
- Do not change other people's files; ask the owner instead.
- Agree function names and return values with the team; never change them silently.
- Handle edge cases so the demo does not crash.

The original plan used Flask + Jinja on Render with a flat module layout; the team chose NiceGUI instead (below).

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
  queries.py    lookups: get_country, get_value, accepted_names, search_countries
  api.py        JSON API router: /api/countries, /countries/search?q=, /countries/playable, /countries/{iso3}, /countries/{iso3}/hints
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
- At least one teammate review, CI/hooks green, then **rebase-merge** into `main` (or a plain merge commit).
  **Never squash:** every atomic commit must stay visible on `main`.

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
