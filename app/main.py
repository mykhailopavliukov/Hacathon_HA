"""NiceGUI entry point. Run with `uv run python -m app.main`."""

import os

from nicegui import app as server
from nicegui import ui

from app import data
from app.api import router

server.include_router(router)


def server_settings() -> dict:
    """Host and port, overridable through HOST and PORT (hosting platforms set them).

    The default host is local-only; a public host needs HOST=0.0.0.0.
    """
    return {
        "host": os.environ.get("HOST", "127.0.0.1"),
        "port": int(os.environ.get("PORT", 8080)),
    }


@ui.page("/")
def index() -> None:
    ui.label("Country facts guessing game").classes("text-2xl")
    ui.label(f"{len(data.countries())} countries loaded")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Guess the country", reload=False, **server_settings())
