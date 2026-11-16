from dataclasses import dataclass
from typing import Any

from nicegui import ui

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


@dataclass(frozen=True)
class RoundData:
    iso3: str
    country_name: str
    hints: list[HintCard]


@dataclass
class GameUIState:
    rounds: list[RoundData]
    round_index: int = 0
    revealed_count: int = 1
    won: bool = False
    last_points: int = 0
    error_message: str = ""


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


def build_demo_rounds() -> list[RoundData]:
    """Provide fallback rounds until the teammate game logic module is wired in."""
    return [
        RoundData(
            iso3="BRA",
            country_name="Бразилія",
            hints=[
                HintCard(label="Населення:", value="216 млн"),
                HintCard(label="ВВП:", value="$2,2 трлн"),
                HintCard(label="Площа:", value="8,5 млн км²"),
                HintCard(label="№1 з виробництва", value="кави"),
                HintCard(label="Південна", value="Америка", tall=True),
                HintCard(label="Мова:", value="португальська", tall=True),
                HintCard(is_silhouette=True, tall=True, wide=True),
            ],
        ),
        RoundData(
            iso3="UKR",
            country_name="Україна",
            hints=[
                HintCard(label="Населення:", value="37 млн"),
                HintCard(label="Площа:", value="603 тис. км²"),
                HintCard(label="Регіон:", value="Східна Європа"),
                HintCard(label="Столиця:", value="Київ", tall=True),
                HintCard(label="Мова:", value="українська", tall=True),
                HintCard(is_silhouette=True, tall=True, wide=True),
            ],
        ),
    ]


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


def _extract_polygons(feature: dict[str, Any] | None) -> list[list[list[list[float]]]]:
    if not isinstance(feature, dict):
        return []
    geometry = feature.get("geometry") if "geometry" in feature else feature
    if not isinstance(geometry, dict):
        return []
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if geo_type == "Polygon":
        return [coords]
    if geo_type == "MultiPolygon":
        return coords
    return []


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


def calculate_points(revealed_count: int, total_hints: int) -> int:
    return max(1, total_hints - revealed_count + 1)


@ui.page("/")
def index_page() -> None:
    # Per-page state isolates concurrent players in different browser tabs.
    state = GameUIState(rounds=build_demo_rounds())
    country_options = load_country_options()

    ui.query("body").classes("bg-white text-slate-900 m-0")
    root = ui.column().classes(
        "w-full min-h-screen items-center justify-center px-4 py-8 bg-white"
    )

    def current_round() -> RoundData | None:
        if not state.rounds:
            return None
        return state.rounds[state.round_index % len(state.rounds)]

    def on_next_hint() -> None:
        rnd = current_round()
        if not rnd or state.revealed_count >= len(rnd.hints):
            return
        state.revealed_count += 1
        state.error_message = ""
        refresh()

    def on_submit_guess(raw_value: str) -> None:
        rnd = current_round()
        if not rnd:
            return
        guess = raw_value.strip()
        if not guess:
            state.error_message = "Введи назву країни"
            refresh()
            return

        target = normalize_search_text(rnd.country_name)
        normalized_guess = normalize_search_text(guess)
        if normalized_guess == target or guess.upper() == rnd.iso3.upper():
            state.won = True
            state.last_points = calculate_points(state.revealed_count, len(rnd.hints))
            state.error_message = ""
        else:
            state.error_message = f"Неправильно! «{guess}» — не та країна"
        refresh()

    def on_next_country() -> None:
        if state.rounds:
            state.round_index = (state.round_index + 1) % len(state.rounds)
        state.revealed_count = 1
        state.won = False
        state.error_message = ""
        refresh()

    def render_game_screen(rnd: RoundData) -> None:
        with ui.column().classes("w-full max-w-[620px] items-center gap-7"):
            ui.label("ВГАДАЙТЕ КРАЇНУ").classes(
                "text-4xl sm:text-5xl font-black tracking-tight text-slate-900 text-center"
            )

            visible = rnd.hints[: state.revealed_count]
            with ui.row().classes("w-full justify-center items-stretch gap-3 flex-wrap"):
                if not visible:
                    ui.label("Підказки відсутні").classes(
                        "bg-[#d6dde6] rounded-2xl px-6 py-4 text-sm font-semibold"
                    )
                for card in visible:
                    render_hint_card(card, rnd.iso3)

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
                                        "hover:bg-[#d6dde6] cursor-pointer text-left transition-colors"
                                    )
                                    .on("click", lambda _, picked=opt.name_uk: select_country(picked))
                                )
                    suggestions_box.set_visibility(True)

                guess_input.on("keydown.enter", lambda: on_submit_guess(guess_input.value or ""))

                has_more = state.revealed_count < len(rnd.hints)
                btn_label = "Наступна\nпідказка" if has_more else "Усі підказки\nвідкрито"
                # Quasar <q-btn> forces primary blue text unless text-color is explicitly set.
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

    def render_win_screen(rnd: RoundData) -> None:
        with ui.column().classes("w-full max-w-[520px] items-center text-center gap-6"):
            ui.label("ПРАВИЛЬНО!").classes(
                "text-4xl sm:text-5xl font-black tracking-tight text-slate-900"
            )
            render_silhouette(rnd.iso3, size_px=220)
            ui.label(f"{rnd.country_name} · +{state.last_points}").classes(
                "text-2xl font-bold text-slate-900"
            )
            (
                ui.button("Наступна країна", on_click=on_next_country)
                .props('flat no-caps text-color="grey-10"')
                .classes(
                    "bg-[#a8d5c2] hover:bg-[#93c9b2] font-semibold "
                    "rounded-2xl px-9 py-4 text-base"
                )
            )

    def refresh() -> None:
        root.clear()
        with root:
            rnd = current_round()
            if not rnd:
                ui.label("Немає доступних раундів").classes("text-lg font-bold text-slate-700")
                return
            if state.won:
                render_win_screen(rnd)
            else:
                render_game_screen(rnd)

    refresh()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Вгадайте країну", port=8080, reload=False)
