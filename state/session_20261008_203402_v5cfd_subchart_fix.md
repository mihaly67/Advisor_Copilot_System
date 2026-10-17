# Session: v5cfd_subchart_fix
*Időbélyeg: 2026-10-08T20:34:02.757777*

# V5 CFD HUD Subchart Fix (2026-10-08 v3)

## Gyökéroka
A `lightweight_charts` Python wrapper `Line` osztály `create_line(name='')` (üres name) esetén
a `SeriesCommon.update()` és `.set()` metódusok **`'value'` kulcsot** várnak a Series-ben/DataFrame-ben.
A korábbi kód `'P(Long)'` és `'P(Short)'` kulcsot küldött, amit a JS library nem ismert fel → `Value is null`.

## Megoldás (Opció A — v1.17 kompatibilis)
- `create_line()` marad `name=''` (üres, ahogy a v1.17-ben működött)
- `.set()` hívás: `pd.DataFrame([{'time':ts_str, 'value':pl}])`
- `.update()` hívás: `pd.Series({'time':ts_str, 'value':pl})`
- **NEM** `'P(Long)'`/`'P(Short)'` kulcs, hanem `'value'`!

## További javítások
- `autoScale:false` + `scaleMargins:{top:0.1,bottom:0.1}` a subchart Y-tengely fix [0,1] tartományhoz
- Anchor vonalak: `horizontal_line(1.0)` és `horizontal_line(0.0)` + `horizontal_line(0.5)` küszöb
- Timestamp parse: rugalmas (unix epoch float VAGY datetime string)

## Teszt eredmények
- `[HUD] ts=2026-10-08 21:30:00 pl=0.408 ps=0.592 has_pred=True is_init=True` ✅
- Nincs `Value is null` JS hiba ✅
- Nincs `[HUD Error]` ✅
- Subchart P(Long) zöld / P(Short) piros vonalak rajzolódnak ✅
