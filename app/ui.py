"""Game UI in a Spotle-like dark style: top bar, game, login, logout and leaderboard pages."""

import contextlib
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nicegui import app as webapp
from nicegui import ui

from app import auth, db
from app.compare import Tile, compare
from app.hints import get_hints, playable_countries
from app.leaderboard import top_players
from app.queries import accepted_names
from app.round import Round

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
REPO_URL = "https://github.com/mykhailopavliukov/Hacathon_HA"
DEVELOPERS = (
    "Heir-of-God",
    "mykhailopavliukov",
    "SamInUkraine",
    "maksymlytvyn26-pixel",
    "yehorivannykov26-stack",
)
MAX_SUGGESTIONS = 8
FIREWORK_EMOJIS = ("🎆", "🎇", "✨", "🎉", "🥳")
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
LONG_HINT_CHARS = 26  # longer hints get a full-width tile

# Palette: dark Spotle base + the colours of our icon
BG = "#121212"
BAR = "#1b1a1f"
EDGE = "#2c2a33"
HINT = "#5b2bd6"
MATCH = "#00b86b"
MISS = "#3a3940"
ACCENT = "#00ff87"
PINK = "#ff007a"
SILHOUETTE_COLOR = "#00e58a"

TILE_COLORS = {"match": MATCH, "up": MISS, "down": MISS, "miss": MISS}
ARROWS = {"up": " ↑", "down": " ↓"}

# Only the newest block gets .pop-in, so old blocks do not re-animate on every refresh.
GLOBAL_CSS = f"""
body {{ background: {BG}; color: #fff; }}
@keyframes pop-in {{
  from {{ opacity: 0; transform: translateY(14px) scale(0.96); }}
  to {{ opacity: 1; transform: none; }}
}}
.pop-in {{ animation: pop-in 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both; }}
@keyframes firework-pop {{
  0% {{ transform: translateY(30px) scale(0.3); opacity: 0; }}
  25% {{ opacity: 1; }}
  100% {{ transform: translateY(-80px) scale(1.9); opacity: 0; }}
}}
.firework {{
  position: absolute;
  animation: firework-pop 1.5s ease-out infinite;
  pointer-events: none;
}}
"""

FALLBACK_COUNTRIES: list[tuple[str, str, str]] = [
    ("BRA", "Бразилія", "Brazil"),
    ("UKR", "Україна", "Ukraine"),
    ("FRA", "Франція", "France"),
    ("JPN", "Японія", "Japan"),
    ("CAN", "Канада", "Canada"),
]


@dataclass(frozen=True)
class CountryOption:
    iso3: str
    name_uk: str
    search_terms: tuple[str, ...]


def normalize_search_text(text: str) -> str:
    """Normalize case, apostrophes, and hyphens for consistent substring matching."""
    cleaned = text.strip().casefold()
    for ch in ("’", "`", "ʼ", "-", "–", "—"):
        cleaned = cleaned.replace(ch, " ")
    return " ".join(cleaned.split())


def _build_option(iso3: str, name_uk: str, name_en: str = "") -> CountryOption:
    raw_terms = [name_uk, name_en]
    terms = tuple(dict.fromkeys(normalize_search_text(t) for t in raw_terms if t.strip()))
    return CountryOption(iso3=iso3.upper(), name_uk=name_uk, search_terms=terms)


def load_country_options() -> list[CountryOption]:
    """Load sorted country options from app.data.countries() with safe fallback."""
    try:
        from app.data import countries

        raw = countries()
    except Exception:
        options = [_build_option(iso, uk, en) for iso, uk, en in FALLBACK_COUNTRIES]
        return sorted(options, key=lambda item: item.name_uk)

    if hasattr(raw, "to_dict"):
        rows = raw.to_dict(orient="records")
    elif isinstance(raw, dict):
        rows = list(raw.values())
    else:
        rows = list(raw or [])

    options: list[CountryOption] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        iso3 = str(row.get("iso3", "")).strip()
        name_uk = str(row.get("name_uk") or row.get("name") or iso3).strip()
        name_en = str(row.get("name_en") or row.get("name") or "").strip()
        if iso3 and name_uk:
            options.append(_build_option(iso3, name_uk, name_en))

    if not options:
        options = [_build_option(iso, uk, en) for iso, uk, en in FALLBACK_COUNTRIES]
    return sorted(options, key=lambda item: item.name_uk)


def _match_rank(query: str, tokens: list[str], term: str) -> int | None:
    if term.startswith(query):
        return 0
    words = term.split()
    if any(word.startswith(query) for word in words):
        return 1
    if query in term:
        return 2
    if len(tokens) > 1 and all(tok in term for tok in tokens):
        return 3
    return None


def filter_countries(
    query: str,
    options: list[CountryOption],
    limit: int = MAX_SUGGESTIONS,
) -> list[CountryOption]:
    """Match countries by prefix, word prefix, inner substring, or multi-word tokens."""
    normalized = normalize_search_text(query)
    if not normalized or not options:
        return []

    tokens = normalized.split()
    iso_query = query.strip().upper()
    ranked: list[tuple[int, str, CountryOption]] = []

    for option in options:
        best_rank: int | None = 0 if iso_query == option.iso3 else None
        for term in option.search_terms:
            rank = _match_rank(normalized, tokens, term)
            if rank is not None and (best_rank is None or rank < best_rank):
                best_rank = rank
        if best_rank is not None:
            ranked.append((best_rank, option.name_uk, option))

    ranked.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in ranked[:limit]]


def find_country_shape(iso3: str) -> dict[str, Any] | None:
    """Find a GeoJSON feature or geometry by iso3 without failing if missing."""
    try:
        from app.data import shapes

        raw = shapes()
    except Exception:
        return None

    if isinstance(raw, dict):
        if iso3 in raw and isinstance(raw[iso3], dict):
            return raw[iso3]
        for feature in raw.get("features", []):
            props = (feature or {}).get("properties") or {}
            if props.get("iso3") == iso3:
                return feature
    elif isinstance(raw, list):
        for feature in raw:
            props = (feature or {}).get("properties") or {}
            if props.get("iso3") == iso3:
                return feature
    return None


FAR_PART_DEGREES = 15  # drop overseas parts like French Guiana


def _extract_polygons(feature: dict[str, Any] | None) -> list[list[list[list[float]]]]:
    if not isinstance(feature, dict):
        return []
    geometry = feature.get("geometry") if "geometry" in feature else feature
    if not isinstance(geometry, dict):
        return []
    coords = geometry.get("coordinates") or []
    if geometry.get("type") == "Polygon":
        polygons = [coords]
    elif geometry.get("type") == "MultiPolygon":
        polygons = coords
    else:
        return []
    return _keep_main_parts(_fix_antimeridian(polygons))


def _fix_antimeridian(polygons: list) -> list:
    """Russia and Fiji cross 180°: shift the western half so the shape stays in one piece."""
    lons = [pt[0] for poly in polygons for ring in poly for pt in ring]
    if not (min(lons) < -170 and max(lons) > 170):
        return polygons
    return [
        [[[lon + 360 if lon < 0 else lon, lat, *rest] for lon, lat, *rest in ring] for ring in poly]
        for poly in polygons
    ]


def _keep_main_parts(polygons: list) -> list:
    if len(polygons) < 2:
        return polygons

    def center(poly: list) -> tuple[float, float]:
        ring = poly[0]
        return sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)

    main = max(polygons, key=lambda poly: len(poly[0]))
    mx, my = center(main)
    return [
        poly
        for poly in polygons
        if abs(center(poly)[0] - mx) <= FAR_PART_DEGREES
        and abs(center(poly)[1] - my) <= FAR_PART_DEGREES
    ]


def geojson_to_svg_path(
    feature: dict[str, Any] | None,
    size: int = 120,
    padding: int = 8,
) -> str:
    """Project GeoJSON Polygon/MultiPolygon coordinates into a normalized SVG path."""
    polygons = _extract_polygons(feature)
    points = [pt for poly in polygons for ring in poly for pt in ring if len(pt) >= 2]
    if not points:
        return ""

    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    drawable = size - 2 * padding
    scale = drawable / max(span_x, span_y)
    offset_x = padding + (drawable - span_x * scale) / 2
    offset_y = padding + (drawable - span_y * scale) / 2

    commands: list[str] = []
    for poly in polygons:
        for ring in poly:
            valid = [pt for pt in ring if len(pt) >= 2]
            if len(valid) < 3:
                continue
            for idx, (lon, lat, *_) in enumerate(valid):
                x = offset_x + (lon - min_x) * scale
                # SVG Y-axis grows downward, whereas latitude grows upward.
                y = offset_y + (max_y - lat) * scale
                prefix = "M" if idx == 0 else "L"
                commands.append(f"{prefix}{x:.1f} {y:.1f}")
            commands.append("Z")
    return " ".join(commands)


def render_silhouette(iso3: str, size_px: int) -> None:
    path_data = geojson_to_svg_path(find_country_shape(iso3))
    if not path_data:
        ui.label("Контур відсутній").classes("text-xs font-semibold text-slate-500")
        return

    svg = (
        f'<svg viewBox="0 0 120 120" width="{size_px}" height="{size_px}" '
        f'style="display:block;margin:auto;">'
        f'<path d="{path_data}" fill="{SILHOUETTE_COLOR}" />'
        f"</svg>"
    )
    try:
        ui.html(svg, sanitize=False)
    except TypeError:
        ui.html(svg)


def split_hint(text: str) -> tuple[str, str]:
    """'Населення: 39 млн осіб' -> ('Населення', '39 млн осіб'); other hints get a generic label."""
    label, sep, value = text.partition(": ")
    if sep and len(label) <= 20:
        return label, value
    if "місце" in text:
        return "Рекорд", text
    return "Підказка", text


def tile(label: str, value: str, color: str, *, wide: bool = False, animate: bool = False) -> None:
    width = "w-full" if wide else "flex-1 min-w-[110px]"
    with (
        ui.column()
        .classes(f"{width} items-center justify-center text-center gap-0 rounded-xl px-3 py-2")
        .classes("pop-in" if animate else "")
        .style(f"background:{color}; min-height:72px")
    ):
        ui.label(label).classes("text-sm text-white/80 leading-tight")
        ui.label(value).classes("text-lg font-extrabold text-white leading-tight")


# ---------- session helpers ----------


def _storage() -> dict:
    """Per-browser storage; an empty dict when storage is not configured (plain tests)."""
    try:
        return webapp.storage.user
    except RuntimeError:
        return {}


def current_user() -> dict | None:
    """{"id", "username"} of the signed-in user, or None."""
    token = _storage().get("token", "")
    return auth.get_session_user(token) if token else None


def _sign_in(user_id: int) -> None:
    _storage()["token"] = auth.create_session(user_id)
    ui.navigate.to("/")


def _log_out() -> None:
    token = _storage().pop("token", "")
    if token:
        auth.delete_session(token)
    ui.navigate.to("/")


def auth_error_text(error: Exception) -> str:
    """auth.py raises English messages; the players see Ukrainian ones."""
    if isinstance(error, auth.TooManyAttempts):
        return "Забагато невдалих спроб — зачекай хвилину"
    if isinstance(error, auth.UsernameTaken):
        return "Це імʼя вже зайняте"
    if str(error).startswith("Username"):
        return "Імʼя: 3–30 символів — літери, цифри, _ . -"
    if str(error).startswith("Password"):
        return f"Пароль: від {auth.MIN_PASSWORD_LENGTH} до {auth.MAX_PASSWORD_LENGTH} символів"
    return str(error)


# ---------- shared page frame ----------

PILL_BTN = "rounded-full font-semibold px-4"


def page_frame(width: str = "max-w-[460px]") -> tuple[dict | None, ui.column]:
    """Top bar + footer around an empty content column; returns (user, content)."""
    user = current_user()
    ui.dark_mode(True)
    ui.add_css(GLOBAL_CSS)
    ui.query(".q-page").style(f"background:{BG}")
    with ui.column().classes("w-full items-center gap-6 px-3 pt-4 pb-10"):
        render_top_bar(user)
        content = ui.column().classes(f"w-full {width} items-stretch gap-4")
        render_footer()
    return user, content


def render_footer() -> None:
    with ui.column().classes("items-center gap-1 mt-6 text-xs text-white/50"):
        with ui.row().classes("items-center justify-center gap-x-1 flex-wrap"):
            ui.label("Developed by:")
            for index, name in enumerate(DEVELOPERS):
                ui.link(name, f"https://github.com/{name}", new_tab=True).classes(
                    "text-white/70 hover:text-white"
                )
                if index < len(DEVELOPERS) - 1:
                    ui.label(",")
            ui.label("·")
            ui.link("MIT License", f"{REPO_URL}/blob/main/LICENSE", new_tab=True).classes(
                "text-white/70 hover:text-white"
            )
        ui.label(
            "KSE CS201 hackathon · Open Data: World Bank, FAOSTAT, Natural Earth, mledoze (ODbL)"
        )


def render_top_bar(user: dict | None) -> None:
    with (
        ui.row()
        .classes("w-full max-w-[800px] items-center gap-2 rounded-2xl px-4 py-2 flex-nowrap")
        .style(f"background:{BAR}; border:1px solid {EDGE}")
    ):
        with (
            ui.row()
            .classes("items-center gap-2 cursor-pointer flex-nowrap")
            .on("click", lambda: ui.navigate.to("/"))
        ):
            ui.image(ASSETS_DIR / "icon.svg").classes("w-11 h-11")
            ui.label("ХАлепа Guesser").classes("text-2xl font-black tracking-tight text-white")
        ui.space()
        ui.button(icon="emoji_events", on_click=lambda: ui.navigate.to("/leaderboard")).props(
            "flat round color=white"
        ).tooltip("Лідерборд")
        ui.button(icon="help_outline", on_click=show_help).props("flat round color=white").tooltip(
            "Як грати"
        )
        if user:
            with ui.row().classes("items-center gap-1 flex-nowrap"):
                ui.icon("account_circle").classes("text-3xl text-white/70")
                ui.label(user["username"]).classes("font-bold text-white")
            ui.button("Log out", on_click=lambda: ui.navigate.to("/logout")).props(
                "outline no-caps color=white"
            ).classes(PILL_BTN)
        else:
            ui.button("Sign in", icon="person", on_click=lambda: ui.navigate.to("/login")).props(
                "unelevated no-caps text-color=black"
            ).classes(PILL_BTN).style(f"background:{ACCENT}")


def show_help() -> None:
    with ui.dialog() as dialog, ui.card().style(f"background:{BAR}; color:#fff"):
        ui.label("Як грати").classes("text-xl font-black")
        ui.label("Вгадай країну за підказками — від загальних до точних.")
        ui.label("Що раніше вгадаєш, то більше балів. Кожна помилка — мінус бали.")
        ui.label(
            "Після помилки бачиш, наскільки близько: зелене — збіг, ↑/↓ — у відповіді більше/менше."
        )
        ui.label("Увійди в акаунт, щоб потрапити в лідерборд.")
        ui.button("Зрозуміло", on_click=dialog.close).props(
            "no-caps unelevated text-color=black"
        ).style(f"background:{ACCENT}")
    dialog.open()


# ---------- login / logout ----------


@ui.page("/login")
def login_page() -> None:
    user, content = page_frame(width="max-w-[380px]")
    if user:
        ui.navigate.to("/")
        return
    with content:
        ui.label("Вхід").classes("text-3xl font-black text-center pop-in")
        username = ui.input("Імʼя користувача").props("outlined rounded dark").classes("w-full")
        password = (
            ui.input("Пароль", password=True, password_toggle_button=True)
            .props("outlined rounded dark")
            .classes("w-full")
        )
        error = ui.label("").classes("text-sm font-semibold text-center").style(f"color:{PINK}")

        def do_login() -> None:
            try:
                found = auth.login(username.value or "", password.value or "")
            except auth.TooManyAttempts as exc:
                error.text = auth_error_text(exc)
                return
            if found is None:
                error.text = "Невірне імʼя користувача або пароль"
                return
            _sign_in(found["id"])

        def do_register() -> None:
            try:
                user_id = auth.register(username.value or "", password.value or "")
            except ValueError as exc:  # UsernameTaken is a ValueError too
                error.text = auth_error_text(exc)
                return
            _sign_in(user_id)

        password.on("keydown.enter", do_login)
        ui.button("Увійти", on_click=do_login).props("unelevated no-caps text-color=black").classes(
            "w-full rounded-full font-bold py-2"
        ).style(f"background:{ACCENT}")
        ui.button("Створити акаунт", on_click=do_register).props(
            "outline no-caps color=white"
        ).classes("w-full rounded-full font-semibold")
        ui.label("Грати можна і без акаунту, але тоді без лідерборду").classes(
            "text-xs text-white/40 text-center"
        )


@ui.page("/logout")
def logout_page() -> None:
    user, content = page_frame(width="max-w-[380px]")
    if user is None:
        ui.navigate.to("/")
        return
    with content, ui.column().classes("w-full items-center gap-4 text-center pop-in"):
        ui.icon("account_circle").classes("text-7xl text-white/60")
        ui.label(f"Вийти з акаунту {user['username']}?").classes("text-2xl font-black")
        ui.button("Log out", on_click=_log_out).props(
            "unelevated no-caps text-color=black"
        ).classes("w-full rounded-full font-bold py-2").style(f"background:{ACCENT}").mark(
            "confirm-logout"
        )
        ui.button("Скасувати", on_click=lambda: ui.navigate.to("/")).props(
            "outline no-caps color=white"
        ).classes("w-full rounded-full")


# ---------- leaderboard ----------


@ui.page("/leaderboard")
def leaderboard_page() -> None:
    user, content = page_frame()
    with content:
        ui.label("Лідерборд").classes("text-4xl font-black text-center")
        ui.label("Сума балів за всі вгадані країни").classes("text-sm text-white/50 text-center")
        rows = top_players(10)
        if not rows:
            ui.label("Поки порожньо — зіграй перший раунд!").classes(
                "text-white/50 text-center py-6"
            )
        me = user["username"] if user else None
        for place, row in enumerate(rows, start=1):
            border = ACCENT if row["player"] == me else EDGE
            delay = f"animation-delay:{place * 0.05:.2f}s"
            with (
                ui.row()
                .classes("w-full items-center rounded-xl px-4 py-3 flex-nowrap pop-in")
                .style(f"background:{BAR}; border:1px solid {border}; {delay}")
            ):
                ui.label(MEDALS.get(place, f"{place}.")).classes("w-8 text-lg font-bold")
                ui.label(row["player"]).classes("font-bold flex-1 truncate")
                ui.label(f"{row['wins']} 🌍").classes("text-sm text-white/60 w-14 text-right")
                ui.label(str(row["total"])).classes("font-black text-xl w-16 text-right").style(
                    f"color:{ACCENT}"
                )
        ui.button("Грати", on_click=lambda: ui.navigate.to("/")).props(
            "unelevated no-caps text-color=black"
        ).classes("w-full rounded-full font-bold py-2 mt-2").style(f"background:{ACCENT}")


# ---------- game page ----------


@dataclass
class GameUIState:
    current_round: Round | None = None
    iso3: str = ""
    primary_name: str = ""
    hints: list = field(default_factory=list)  # list[Hint] from app.hints
    guesses: list[str] = field(default_factory=list)  # wrong guesses, iso3, oldest first
    won: bool = False
    animate: str = ""  # "hint" or "guess": which newest block should pop in
    score_saved: bool = False
    error_message: str = ""


def start_new_round(state: GameUIState) -> None:
    countries = playable_countries()
    if not countries:
        return
    iso3 = random.choice(countries)
    names = accepted_names(iso3)
    state.iso3 = iso3
    state.primary_name = names[0] if names else iso3
    state.hints = get_hints(iso3)
    state.current_round = Round(hints=[h.text for h in state.hints], accepted_names=list(names))
    state.guesses = []
    state.won = False
    state.animate = "hint"
    state.score_saved = False
    state.error_message = ""


def resolve_country(text: str, options: list[CountryOption]) -> str | None:
    """iso3 for an exact Ukrainian or English name (or iso3 code), otherwise None."""
    query = normalize_search_text(text)
    for option in options:
        if query in option.search_terms or text.strip().upper() == option.iso3:
            return option.iso3
    return None


def render_fireworks() -> None:
    """Self-contained emoji fireworks: no network needed on the demo."""
    with ui.element("div").classes("fixed inset-0 overflow-hidden pointer-events-none z-50"):
        for _ in range(18):
            ui.label(random.choice(FIREWORK_EMOJIS)).classes("firework").style(
                f"left:{random.randint(2, 92)}%; top:{random.randint(5, 75)}%; "
                f"animation-delay:{random.uniform(0, 1.4):.2f}s; "
                f"font-size:{random.uniform(1.6, 3.2):.1f}rem"
            )


def render_hints(state: GameUIState) -> None:
    shown = state.current_round.shown
    with ui.row().classes("w-full gap-2"):
        for index, hint in enumerate(state.hints[:shown]):
            animate = state.animate == "hint" and index == shown - 1
            if hint.kind == "map":
                with (
                    ui.column()
                    .classes("w-full items-center rounded-xl py-3 gap-1")
                    .classes("pop-in" if animate else "")
                    .style(f"background:{HINT}")
                ):
                    ui.label(hint.text).classes("text-sm text-white/80")
                    render_silhouette(state.iso3, size_px=150)
                continue
            label, value = split_hint(hint.text)
            wide = len(value) > LONG_HINT_CHARS
            tile(label, value, HINT, wide=wide, animate=animate)


def render_guess(iso3: str, target: str, animate: bool) -> None:
    from app.data import countries

    country = countries()[iso3]
    with ui.column().classes("w-full gap-2" + (" pop-in" if animate else "")):
        with ui.row().classes("items-center gap-3 flex-nowrap"):
            ui.label(country["flag"]).classes("text-4xl leading-none")
            ui.label(country["name_uk"]).classes("text-2xl font-black")
        with ui.row().classes("w-full gap-2"):
            for t in compare(iso3, target):
                render_compare_tile(t)


def render_compare_tile(t: Tile) -> None:
    tile(t.label, t.value + ARROWS.get(t.status, ""), TILE_COLORS[t.status])


@ui.page("/")
def index_page() -> None:
    user, content = page_frame()
    state = GameUIState()
    start_new_round(state)
    country_options = load_country_options()

    def save_victory() -> None:
        if state.score_saved or not state.current_round:
            return
        state.score_saved = True
        if user is None:
            return
        with contextlib.suppress(ValueError):  # a weird score must not crash the demo
            db.add_score(user["username"], state.current_round.score)

    def on_next_hint() -> None:
        if state.current_round and state.current_round.can_reveal:
            state.current_round.reveal_next()
            state.error_message = ""
            state.animate = "hint"
            refresh()

    def on_submit_guess(raw_value: str) -> None:
        if not state.current_round or not raw_value.strip():
            return
        state.animate = ""
        iso3 = resolve_country(raw_value, country_options)
        if iso3 is None:
            state.error_message = "Такої країни немає у списку — обери з підказок"
        elif iso3 in state.guesses:
            state.error_message = "Цю країну ти вже пробував"
        elif state.current_round.guess(state.primary_name if iso3 == state.iso3 else iso3):
            state.won = True
            state.error_message = ""
            save_victory()
        else:
            state.guesses.append(iso3)
            state.error_message = ""
            state.animate = "guess"
        refresh()

    def on_next_country() -> None:
        start_new_round(state)
        refresh()

    def render_status_row() -> None:
        rnd = state.current_round
        with ui.row().classes("w-full items-center justify-between"):
            ui.button(
                "Ще підказка ›" if rnd.can_reveal else "Підказки скінчились",
                on_click=on_next_hint,
            ).props("outline rounded no-caps dense color=positive").classes(
                "px-3 font-semibold"
            ).set_enabled(rnd.can_reveal)
            ui.label(
                f"Підказка {rnd.shown} з {len(state.hints)} · {rnd.points_available} балів"
            ).classes("font-bold text-white")

    def render_guess_input() -> None:
        with ui.element("div").classes("relative w-full"):
            guess_input = (
                ui.input(placeholder="Введи країну...")
                .props("outlined rounded dark dense")
                .classes("w-full text-lg")
            )
            with guess_input.add_slot("append"):
                ui.icon("search").classes("text-white/50")
            suggestions = (
                ui.column()
                .classes("absolute left-0 right-0 top-full mt-1 z-40 rounded-xl gap-0 py-1")
                .classes("max-h-64 overflow-y-auto shadow-xl")
                .style(f"background:{BAR}; border:1px solid {EDGE}")
            )
            suggestions.set_visibility(False)

        def pick(name: str) -> None:
            suggestions.set_visibility(False)
            on_submit_guess(name)

        def update(raw: str) -> None:
            suggestions.clear()
            matches = filter_countries(raw, country_options) if raw.strip() else []
            with suggestions:
                for opt in matches:
                    ui.label(opt.name_uk).classes(
                        "w-full px-4 py-2 cursor-pointer text-white hover:bg-white/10"
                    ).on("click", lambda _, n=opt.name_uk: pick(n))
            suggestions.set_visibility(bool(matches))

        guess_input.on_value_change(lambda e: update(str(e.value or "")))
        guess_input.on("keydown.enter", lambda: on_submit_guess(guess_input.value or ""))

    def render_game_screen() -> None:
        render_status_row()
        render_guess_input()
        if state.error_message:
            ui.label(state.error_message).classes("text-sm font-semibold pop-in").style(
                f"color:{PINK}"
            )
        if state.animate == "guess":
            with ui.row().classes("w-full justify-center"):
                ui.image(ASSETS_DIR / "wrong_guess.png").classes("w-28 rounded-xl pop-in").props(
                    'alt="не вгадав"'
                )
        render_hints(state)
        # newest guess on top, like Spotle
        for position, iso3 in enumerate(reversed(state.guesses)):
            render_guess(iso3, state.iso3, animate=state.animate == "guess" and position == 0)

    def render_win_screen() -> None:
        render_fireworks()
        with ui.column().classes("w-full items-center text-center gap-4 pop-in"):
            ui.label("ПРАВИЛЬНО!").classes("text-5xl font-black").style(f"color:{ACCENT}")
            render_silhouette(state.iso3, size_px=200)
            with ui.row().classes("items-center gap-2"):
                ui.label(state.primary_name).classes("text-3xl font-black")
                ui.label(f"+{state.current_round.score}").classes(
                    "text-xl font-black rounded-full px-3 py-1 text-black"
                ).style(f"background:{ACCENT}")
            ui.label(
                f"Підказок: {state.current_round.shown} · помилок: {len(state.guesses)}"
            ).classes("text-white/60")
            if user is None:
                ui.label("Увійди, щоб результат потрапив у лідерборд").classes(
                    "text-sm text-white/50"
                )
            ui.button("Наступна країна", on_click=on_next_country).props(
                "unelevated no-caps text-color=black"
            ).classes("rounded-full font-bold px-8 py-2").style(f"background:{ACCENT}")

    def refresh() -> None:
        content.clear()
        with content:
            if not state.current_round:
                ui.label("Гру неможливо завантажити").classes("text-lg font-bold")
            elif state.won:
                render_win_screen()
            else:
                render_game_screen()

    refresh()
