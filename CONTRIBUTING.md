# Contributing

All rules (branches, atomic commits, commit format, PRs, documentation policy, data and secrets)
live in the [README](README.md#repository-rules). Quick checklist:

1. `uv sync && sh scripts/setup-hooks.sh` once per clone.
2. Branch from up-to-date `main`: `<type>/<kebab-topic>`.
3. Make small, atomic Conventional Commits; tests with the code they cover.
4. `uv run pytest` and `uv run ruff check .` pass before pushing.
5. Open a PR with the template, get a review, rebase-merge (never squash).

To intentionally change source data: `ALLOW_DATA_CHANGE=1 git commit ...`.
