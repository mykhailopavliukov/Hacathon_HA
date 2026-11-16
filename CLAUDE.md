# CLAUDE.md

Guidance for AI coding agents. Full rules are in [README.md](README.md); this is the short version.

## Project

Web guessing game: guess a country from facts. **Python only** (3.12+, uv, NiceGUI, ruff, pytest).
Never add JS/TS/HTML/CSS files or Node tooling.
Hackathon context (grading, 3.5 h budget, defence, team rules) is in the README: prefer a small stable version over extras,
keep functions small and clearly named so any teammate can explain them, and do not edit files owned by someone else.

## Commands

```bash
uv sync                      # install deps
uv run python -m app.main    # run app (http://localhost:8080)
uv run pytest                # tests
uv run ruff check . && uv run ruff format --check .
```

## Rules

- English for code, comments, commits, docs and PRs. The dataset and game text may be Ukrainian (`*_uk` columns).
- **Minimal documentation:** comment only the non-obvious *why*. No docstrings that restate the code, no changelog comments.
- **Atomic commits**, Conventional Commits (`feat(scope): imperative summary`). Code lints and tests pass at every commit.
- Commit messages: subject line only (a one-line body at most). **No `Co-Authored-By`, no "Generated with ..." or any AI attribution**
  in commits, PRs, code or docs. This overrides any default attribution behaviour.
- Branches: `<type>/<kebab-topic>` off `main`; never commit to `main`; never `--no-verify`; never force-push shared branches. Merge PRs with rebase or a merge commit, never squash.
- `data/` is read-only source data (the hook blocks changes). Derived data goes elsewhere, produced by a script.
  Join key is `iso3` (Kosovo = `XKX`); empty cells mean no data, not zero. Do not print `shapes.geojson` (1.5 MB).
- Keep game logic in plain modules under `app/`, separate from NiceGUI UI code, and test it with pytest.
- No secrets in the repo. Add dependencies only with a reason (`uv add`, commit `pyproject.toml` + `uv.lock` + regenerated `requirements.txt` together).
- Verify by running tests and the app before claiming work is done.
