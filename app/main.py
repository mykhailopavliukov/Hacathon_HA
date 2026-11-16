"""NiceGUI entry point. Run with `uv run python -m app.main`."""

import os
from pathlib import Path

from nicegui import app as server
from nicegui import ui

import app.ui  # noqa: F401  (registers the "/" page)
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


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="ХАлепа Guesser",
        favicon=str(Path(__file__).resolve().parent / "assets" / "icon.svg"),
        # storage_secret signs the browser-session cookie that keeps players logged in
        storage_secret=os.environ.get("STORAGE_SECRET", "halepa-guesser-dev"),
        reload=False,
        **server_settings(),
    )
