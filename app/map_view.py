from nicegui import ui

from app import map_data

NO_LABELS_TILE_URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
DEFAULT_CENTER = (20.0, 0.0)
DEFAULT_ZOOM = 2


class CountryMap:
    """Leaflet map wrapper with country highlighting from GeoJSON."""

    def __init__(self) -> None:
        # Disable default OSM tiles so country names do not spoil the game
        self.map = ui.leaflet(
            center=DEFAULT_CENTER, zoom=DEFAULT_ZOOM, options={"worldCopyJump": True}
        ).classes("w-full h-96 rounded-lg shadow")
        self.map.clear_layers()
        self.map.tile_layer(
            url_template=NO_LABELS_TILE_URL,
            options={"attribution": "&copy; OpenStreetMap &copy; CARTO", "maxZoom": 10},
        )
        self._active_layers: list[ui.leaflet.layer] = []

    def clear_highlight(self) -> None:
        """Remove all highlighted country polygons."""
        for layer in self._active_layers:
            self.map.remove_layer(layer)
        self._active_layers.clear()

    def reset_view(self) -> None:
        """Clear highlights and return the camera to world overview."""
        self.clear_highlight()
        self.map.set_center(DEFAULT_CENTER)
        self.map.set_zoom(DEFAULT_ZOOM)

    def highlight_country(self, iso3: str, color: str = "#2563eb", focus: bool = True) -> bool:
        """Highlight a country by iso3. Returns False if geometry is missing."""
        feature = map_data.get_country_feature(iso3)
        if not feature:
            return False

        self.clear_highlight()
        layer = self.map.generic_layer(
            name="geoJSON",
            args=[
                feature,
                {
                    "style": {
                        "color": color,
                        "weight": 2,
                        "fillColor": color,
                        "fillOpacity": 0.35,
                    }
                },
            ],
        )
        self._active_layers.append(layer)

        if focus:
            bounds = map_data.get_feature_bounds(feature)
            if bounds:
                (min_lat, min_lon), (max_lat, max_lon) = bounds
                self.map.run_map_method(
                    "fitBounds",
                    [[min_lat, min_lon], [max_lat, max_lon]],
                    {"padding": [24, 24], "maxZoom": 6},
                )
        return True
