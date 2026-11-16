"""NiceGUI entry point. Run with `uv run python -m app.main`."""

from nicegui import ui

from app import data


@ui.page("/")
def index() -> None:
    ui.label("Country facts guessing game").classes("text-2xl")
    ui.label(f"{len(data.countries())} countries loaded")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Guess the country", reload=False)
