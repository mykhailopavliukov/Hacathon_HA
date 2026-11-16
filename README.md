# Guess the Country 🌍

[![created-at](https://img.shields.io/github/created-at/mykhailopavliukov/Hacathon_HA)](https://github.com/mykhailopavliukov/Hacathon_HA)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![using-nicegui](https://img.shields.io/badge/Using-NiceGUI%20%7C%20FastAPI%20%7C%20SQLite-1f425f.svg)](https://github.com/mykhailopavliukov/Hacathon_HA/blob/main/requirements.txt)
[![repo-stars](https://img.shields.io/github/stars/mykhailopavliukov/Hacathon_HA)](https://github.com/mykhailopavliukov/Hacathon_HA/stargazers)
[![license](https://img.shields.io/badge/License-MIT-1f425f.svg)](https://github.com/mykhailopavliukov/Hacathon_HA/blob/main/LICENSE)

Welcome! 👋 Guess the Country is a web game built in one afternoon by five KSE students at the CS201 Python hackathon (theme: Open Data). A country is hidden behind a ladder of hints that goes from vague (population rank, area, GDP) to precise (neighbours, languages, the outline on a map, the first letter of the capital). The earlier you guess, the more points you get. 🏆 Everything is written in Python: the game logic, the API and even the UI. 🐍

🌐 **Live demo:** https://guess-the-country-hfw2.onrender.com (free hosting: the first load after a pause takes about a minute ⏳)

## 🎮 How to play

1. Read the first hint, then guess the country in the box (suggestions appear as you type).
2. Stuck? Open the next hint, but every hint you open lowers the points you can win. 📉
3. A wrong guess costs points too. A correct one ends the round and shows the country's outline. 🗺️
4. Create an account to keep a win streak 🔥 and appear on the leaderboard.

## ✨ Features

- **Hint ladder**: at least 8 hints per country, ordered from general to precise, generated from the open datasets in `data/`
- **Scoring**: points drop with every opened hint and every wrong guess (minimum 10 for a win)
- **Smart answer checking**: case, accents and apostrophes are ignored, so `Вєтнам` and `В'єтнам` are the same
- **Country search**: prefix and substring search in Ukrainian and English
- **Accounts**: sign-up and login with scrypt-hashed passwords, 7-day sessions, login lockout after 5 failures
- **Win streaks and leaderboard**: current and best streak per account, top scores
- **JSON API**: countries, hints, search, accounts, streaks and leaderboard under `/api`
- **Tests**: 100+ pytest tests, checked by pre-commit hooks on every commit ✅

## 🧰 Stack

- **Python only**, no hand-written JS/TS/HTML/CSS and no Node toolchain
- **[NiceGUI](https://nicegui.io/)** for the UI and the server (FastAPI underneath), **Python 3.12+**, managed with [uv](https://docs.astral.sh/uv/)
- **SQLite** (standard library) for accounts, streaks and the leaderboard; country data is loaded once from CSV/GeoJSON into memory
- **ruff** for linting and formatting, **pytest** for tests

Why NiceGUI: per-player state and event handlers fit a game better than rerun-the-script frameworks, and it needs no JS.

## 📥 Getting started

```bash
git clone https://github.com/mykhailopavliukov/Hacathon_HA.git
cd Hacathon_HA
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

Optional settings: `HOST` (default `127.0.0.1`), `PORT` (default `8080`), `SCORES_DB` (SQLite file, default `scores.db`).

## ☁️ Deploy (Render or any Python host)

- Python version: `.python-version` (3.12)
- Build command: `pip install -r requirements.txt`
- Start command: `python -m app.main`
- Environment: `HOST=0.0.0.0` (the default is local-only); `PORT` is set by the host
- `requirements.txt` is generated from `uv.lock`; regenerate it after every `uv add` / `uv remove`:
  `uv export --no-dev --no-hashes --no-emit-project -o requirements.txt`
- On a free host the SQLite file is wiped on every restart, so accounts and the leaderboard reset. Fine for a demo. 🙂

## 📂 Project structure

```
Hacathon_HA/
├── app/
│   ├── main.py         # NiceGUI entry point; HOST/PORT from environment
│   ├── ui.py           # game pages
│   ├── round.py        # round state, answer check, scoring
│   ├── hints.py        # hint ladder and playable countries
│   ├── data.py         # loads and caches the datasets from data/
│   ├── queries.py      # get_country, get_value, accepted_names, search_countries
│   ├── db.py           # SQLite schema, add_score, top_scores
│   ├── auth.py         # hash_password, register, login, sessions
│   ├── streaks.py      # record_round, get_streak, top_streaks
│   ├── api.py          # JSON API: countries, search, hints, scores, leaderboard
│   ├── account_api.py  # JSON API: /auth/*, /streak, /streaks/top
│   └── map_*.py        # GeoJSON lookup and Leaflet highlight
├── tests/              # pytest tests (game logic is tested without the UI)
├── data/               # provided open datasets, read-only (see below)
├── scripts/            # setup-hooks.sh
├── .githooks/          # shared git hooks: pre-commit, commit-msg
├── .github/            # PR template
├── pyproject.toml      # dependencies and tool config (ruff, pytest)
└── CLAUDE.md           # rules for AI coding agents
```

Game logic (hint selection, answer checking, scoring) lives in plain Python modules, separate from the UI code, so it can be tested without a browser.

## 🔌 API at a glance

| Method and path | What it does |
|---|---|
| `GET /api/countries`, `/api/countries/search?q=`, `/api/countries/playable` | list, search, playable codes |
| `GET /api/countries/{iso3}`, `/api/countries/{iso3}/hints` | one country, its hint ladder |
| `POST /api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `GET /api/auth/me` | accounts (bearer token) |
| `GET`, `POST /api/streak`, `GET /api/streaks/top` | win streaks |
| `POST /api/scores`, `GET /api/leaderboard` | leaderboard |

Routes are defined in `app/api.py` and `app/account_api.py`.

## 🏆 Hackathon context

Team of 5 KSE students at the Python hackathon of course CS201, about 3.5 hours of work, then a defence.

- Theme: Open Data. Python is the main language and holds all the logic; HTML/CSS only for display, JS minimal and without logic.
- Defence: a 1-2 minute demo. Anyone on the team must be able to explain any part of the code.
- Grading: working program 6, code quality 4 (functions, clear names, no repetition), idea 3, Git 1 (commits from different people), demo 1.
- Stability comes first: a minimal working version, then bonuses.

Team rules:
- Everyone commits only their own files, often, with proper messages.
- Do not change other people's files; ask the owner instead.
- Agree function names and return values with the team; never change them silently.
- Handle edge cases so the demo does not crash.

## 👾 Contributing

Contributions are welcome! Open an issue or a pull request, and please read the rules below first.

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
  (`uv add <pkg>`, commit `pyproject.toml`, `uv.lock` and the regenerated `requirements.txt` together).
- Type-hint public functions. Follow `ruff` (line length 100) and `.editorconfig`.

### Data and secrets
- `data/` is read-only source data. The pre-commit hook blocks changes there
  (override deliberately with `ALLOW_DATA_CHANGE=1`). Derived data is produced by a script into a different folder.
- Never commit secrets or `.env` files; commit `.env.example` with placeholders instead.

### Hooks (enabled by `scripts/setup-hooks.sh`)
- **pre-commit**: secret scan, `.env` guard, files over 5 MB, conflict markers/whitespace, `data/` guard, `ruff` check and format check on staged `.py` files.
- **commit-msg**: Conventional Commits format, no co-author/sign-off trailers or AI attribution, short messages only.

## 🗂️ Data

All files are joined on `iso3` (ISO 3166-1 alpha-3; Kosovo is `XKX`, as in the World Bank data).

| File | Contents |
|---|---|
| `countries.csv` | 197 countries: Ukrainian/English names, capital, region, languages, currencies, neighbours, area, centroid, flag |
| `shapes.geojson` | Country outlines (MultiPolygon) with an `iso3` property. Crimea is part of Ukraine |
| `indicators.csv` | Selected indicators and Ukrainian phrase templates (`{rank}` placeholder) |
| `stats.csv` | Indicator values: one row per country, one column per indicator `id` (latest value; empty = no data) |

Known quirk: `stats.csv` has a `vanilla` column with no row in `indicators.csv`.

Sources: [mledoze/countries](https://github.com/mledoze/countries) (ODbL), [Natural Earth](https://www.naturalearthdata.com/) (public domain), [World Bank WDI](https://data.worldbank.org/), [FAOSTAT](https://www.fao.org/faostat/).

## 👥 Developed by

[Heir-of-God](https://github.com/Heir-of-God), [mykhailopavliukov](https://github.com/mykhailopavliukov), [SamInUkraine](https://github.com/SamInUkraine), [maksymlytvyn26-pixel](https://github.com/maksymlytvyn26-pixel), [yehorivannykov26-stack](https://github.com/yehorivannykov26-stack)

## 📃 License

Code: [MIT](LICENSE). The datasets in `data/` keep the licenses of their original sources listed above
(notably ODbL for the country metadata, which requires attribution and share-alike for derived databases).

<div align="center">

### Show ❤️ By Starring This Repo💎

</div>
