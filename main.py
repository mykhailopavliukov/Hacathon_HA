from nicegui import ui
import app.ui  # Завантажує сторінку @ui.page("/") з нашого UI

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Вгадайте країну", port=8080, reload=False)
