"""Game page: hint cards, guess input with suggestions, victory screen."""

import random
from dataclasses import dataclass, field
from typing import Any

from nicegui import ui

from app.hints import get_hints, playable_countries
from app.queries import accepted_names
from app.round import Round

SILHOUETTE_COLOR = "#2e7d57"
MAX_SUGGESTIONS = 8

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


@dataclass(frozen=True)
class HintCard:
    label: str = ""
    value: str = ""
    is_silhouette: bool = False
    tall: bool = False
    wide: bool = False


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


def render_hint_card(card: HintCard, iso3: str) -> None:
    width_cls = "w-[300px]" if card.wide else "w-36"
    height_cls = "h-36" if card.tall else "h-24"
    base_cls = (
        f"{width_cls} {height_cls} bg-[#d6dde6] rounded-2xl p-3 "
        "flex flex-col items-center justify-center text-center text-slate-900 select-none"
    )
    with ui.element("div").classes(base_cls):
        if card.is_silhouette:
            render_silhouette(iso3, size_px=116)
        else:
            if card.label:
                ui.label(card.label).classes("text-sm font-medium leading-tight")
            if card.value:
                ui.label(card.value).classes("text-sm font-extrabold leading-tight mt-0.5")


@dataclass
class GameUIState:
    current_round: Round | None = None
    iso3: str = ""
    primary_name: str = ""
    ui_cards: list[HintCard] = field(default_factory=list)
    won: bool = False
    error_message: str = ""


def start_new_round(state: GameUIState) -> None:
    countries = playable_countries()
    if not countries:
        return

    iso3 = random.choice(countries)
    raw_hints = get_hints(iso3)
    names = accepted_names(iso3)
    primary_name = names[0] if names else iso3

    ui_cards = []
    for h in raw_hints:
        if h.kind == "map":
            ui_cards.append(HintCard(is_silhouette=True, tall=True, wide=True))
        else:
            ui_cards.append(HintCard(value=h.text))

    state.iso3 = iso3
    state.primary_name = primary_name
    state.ui_cards = ui_cards
    state.current_round = Round(hints=[h.text for h in raw_hints], accepted_names=list(names))
    state.won = False
    state.error_message = ""


@ui.page("/")
def index_page() -> None:
    state = GameUIState()
    start_new_round(state)
    country_options = load_country_options()

    ui.query("body").classes("bg-white text-slate-900 m-0")
    root = ui.column().classes("w-full min-h-screen items-center justify-center px-4 py-8 bg-white")

    def on_next_hint() -> None:
        if state.current_round and not state.current_round.is_over:
            state.current_round.reveal_next()
            state.error_message = ""
            refresh()

    def on_submit_guess(raw_value: str) -> None:
        if not state.current_round:
            return
        guess = raw_value.strip()
        if not guess:
            state.error_message = "Введи назву країни"
            refresh()
            return

        if state.current_round.guess(guess):
            state.won = True
            state.error_message = ""
        else:
            state.error_message = f"Неправильно! «{guess}» — не та країна"
        refresh()

    def on_next_country() -> None:
        start_new_round(state)
        refresh()

    def render_game_screen() -> None:
        with ui.column().classes("w-full max-w-[620px] items-center gap-7"):
            ui.label("ВГАДАЙТЕ КРАЇНУ").classes(
                "text-4xl sm:text-5xl font-black tracking-tight text-slate-900 text-center"
            )

            revealed_count = state.current_round.shown if state.current_round else 0
            visible = state.ui_cards[:revealed_count]

            with ui.row().classes("w-full justify-center items-stretch gap-3 flex-wrap"):
                if not visible:
                    ui.label("Підказки відсутні").classes(
                        "bg-[#d6dde6] rounded-2xl px-6 py-4 text-sm font-semibold"
                    )
                for card in visible:
                    render_hint_card(card, state.iso3)

            with ui.row().classes(
                "w-full max-w-[460px] items-stretch justify-center gap-3 flex-nowrap"
            ):
                border_cls = "border-red-600" if state.error_message else "border-slate-900"

                with ui.element("div").classes("relative flex-1 min-w-0"):
                    guess_input = (
                        ui.input(
                            placeholder="Назва країни",
                            on_change=lambda e: update_suggestions(str(e.value or "")),
                        )
                        .props("borderless dense")
                        .classes(
                            f"w-full bg-white border-2 {border_cls} rounded-full "
                            "px-6 py-2.5 text-lg text-slate-900"
                        )
                    )
                    suggestions_box = ui.column().classes(
                        "absolute left-0 right-0 top-full mt-2 z-50 bg-white "
                        "border-2 border-slate-900 rounded-2xl shadow-lg "
                        "overflow-hidden gap-0 max-h-60 overflow-y-auto py-1"
                    )
                    suggestions_box.set_visibility(False)

                def select_country(country_name: str) -> None:
                    guess_input.value = country_name
                    suggestions_box.set_visibility(False)
                    on_submit_guess(country_name)

                def update_suggestions(raw_query: str) -> None:
                    query = raw_query.strip()
                    suggestions_box.clear()
                    if not query:
                        suggestions_box.set_visibility(False)
                        return

                    matches = filter_countries(query, country_options)
                    with suggestions_box:
                        if not matches:
                            ui.label("Країну не знайдено").classes(
                                "w-full px-5 py-2 text-sm text-slate-500 italic text-left"
                            )
                        else:
                            for opt in matches:
                                (
                                    ui.label(opt.name_uk)
                                    .classes(
                                        "w-full px-5 py-2 text-base font-medium text-slate-900 "
                                        "hover:bg-[#d6dde6] cursor-pointer text-left "
                                        "transition-colors"
                                    )
                                    .on(
                                        "click",
                                        lambda _, picked=opt.name_uk: select_country(picked),
                                    )
                                )
                    suggestions_box.set_visibility(True)

                guess_input.on("keydown.enter", lambda: on_submit_guess(guess_input.value or ""))

                has_more = revealed_count < len(state.ui_cards)
                btn_label = "Наступна\nпідказка" if has_more else "Усі підказки\nвідкрито"
                next_btn = (
                    ui.button(btn_label, on_click=on_next_hint)
                    .props('flat no-caps text-color="grey-10"')
                    .classes(
                        "bg-[#a8d5c2] hover:bg-[#93c9b2] font-semibold "
                        "rounded-2xl px-5 py-2.5 text-sm leading-tight whitespace-pre-line shrink-0"
                    )
                )
                next_btn.set_enabled(has_more)

            if state.error_message:
                ui.label(state.error_message).classes(
                    "bg-red-100 text-red-700 text-sm font-semibold px-4 py-1.5 rounded-full -mt-3"
                )

    def render_win_screen() -> None:
        with ui.column().classes("w-full max-w-[520px] items-center text-center gap-6"):
            ui.label("ПРАВИЛЬНО!").classes(
                "text-4xl sm:text-5xl font-black tracking-tight text-slate-900"
            )
            render_silhouette(state.iso3, size_px=220)
            score = state.current_round.score if state.current_round else 0
            ui.label(f"{state.primary_name} · +{score}").classes(
                "text-2xl font-bold text-slate-900"
            )
            (
                ui.button("Наступна країна", on_click=on_next_country)
                .props('flat no-caps text-color="grey-10"')
                .classes(
                    "bg-[#a8d5c2] hover:bg-[#93c9b2] font-semibold rounded-2xl px-9 py-4 text-base"
                )
            )

    def refresh() -> None:
        root.clear()
        with root:
            if not state.current_round:
                ui.label("Гру неможливо завантажити").classes("text-lg font-bold text-slate-700")
                return
            if state.won:
                render_win_screen()
            else:
                render_game_screen()

    refresh()
