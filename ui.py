import random
from dataclasses import dataclass, field
from typing import Any

from nicegui import ui

from app.hints import get_hints, playable_countries
from app.round import Round
from app.queries import accepted_names

# ... (ТУТ ЗАЛИШ: SILHOUETTE_COLOR, MAX_SUGGESTIONS, FALLBACK_COUNTRIES,
# CountryOption, HintCard, normalize_search_text, _build_option, load_country_options,
# _match_rank, filter_countries, find_country_shape, _extract_polygons,
# geojson_to_svg_path, render_silhouette, render_hint_card) ...


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
        if getattr(h, "kind", "") == "map":
            ui_cards.append(HintCard(is_silhouette=True, tall=True, wide=True))
        else:
            kind_label = str(getattr(h, "kind", "")).capitalize()
            ui_cards.append(HintCard(label=kind_label, value=str(getattr(h, "text", ""))))

    state.iso3 = iso3
    state.primary_name = primary_name
    state.ui_cards = ui_cards
    state.current_round = Round(
        hints=[h.text for h in raw_hints],
        accepted_names=list(names)
    )
    state.won = False
    state.error_message = ""


@ui.page("/")
def index_page() -> None:
    state = GameUIState()
    start_new_round(state)
    country_options = load_country_options()

    ui.query("body").classes("bg-white text-slate-900 m-0")
    root = ui.column().classes(
        "w-full min-h-screen items-center justify-center px-4 py-8 bg-white"
    )

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

            revealed_count = len(state.current_round.shown) if state.current_round else 0
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
                                        "hover:bg-[#d6dde6] cursor-pointer text-left transition-colors"
                                    )
                                    .on("click", lambda _, picked=opt.name_uk: select_country(picked))
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
                    "bg-[#a8d5c2] hover:bg-[#93c9b2] font-semibold "
                    "rounded-2xl px-9 py-4 text-base"
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
