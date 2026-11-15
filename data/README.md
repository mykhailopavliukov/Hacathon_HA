# Дані

Усі дані відкриті. Ключ для склейки — `iso3` (ISO 3166-1 alpha-3; Косово — `XKX`, як у World Bank).

| Файл | Що всередині | Джерело |
|---|---|---|
| `countries.csv` | 197 країн (члени ООН + Палестина, Ватикан, Тайвань, Косово): українська назва, столиця, регіон, мови, валюти, сусіди, площа, координати центру | [mledoze/countries](https://github.com/mledoze/countries) (ODbL), назви — Natural Earth |
| `shapes.geojson` | Контури країн (MultiPolygon), властивість `iso3`. Крим — у складі України | [Natural Earth](https://www.naturalearthdata.com/) 1:50m (public domain) |
| `indicators.csv` | Відібрані показники та українські шаблони фраз | складено вручну |
| `stats.csv` | Значення показників: рядок = країна, стовпчик = `id` з `indicators.csv` (найсвіжіше значення, порожньо = немає даних) | [World Bank WDI](https://data.worldbank.org/), [FAOSTAT](https://www.fao.org/faostat/) |

## countries.csv
`iso3, name_uk, name_en, m49, capital_en, capital_uk, region_uk, subregion_uk, languages_uk, currencies_uk, borders, neighbors_count, area_km2, lat, lng, landlocked, has_shape, flag`

- `borders` — коди сусідів через `;` (порожньо для острівних держав)
- `languages_uk`, `currencies_uk` — через `; `
- рядки вже відсортовані за українським алфавітом

## indicators.csv
`id, source, code, role, unit_uk, decimals, use_top, use_bottom, template_top, template_bottom`

- `role`: `base` — базові підказки (населення, ВВП на душу, тривалість життя); `fact` — кандидати в рекорди/антирекорди
- `use_top` / `use_bottom`: чи можна робити рекорд (топ зверху) / антирекорд (топ знизу)
- `template_*`: фраза з `{rank}`, наприклад `{rank} місце у світі за виробництвом кави`
- для FAOSTAT `code` — назва продукту, значення — виробництво в тоннах
