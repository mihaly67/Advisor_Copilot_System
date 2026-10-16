# V5 CFD Subchart: Zajzóna + Küszöb Line Series megoldás

## Probléma
A subcharton nem látszottak a zajzóna (0.425/0.575) és küszöb (0.50) vonalak.

## Ok
A `horizontal_line()` a subchart-on létrejött JS-ben, de a **subchart priceScale** nem frissült mert:
- Nincs OHLC series a subchart-ban (csak line series-ek)
- `horizontal_line` priceLine-jai a belső chart priceScale-hez adódnak, de autoScale nem veszi figyelembe őket

## Megoldás
Zajzóna és küszöb most **line series**-ként implementáltak:
```python
self.noise_lo_line = self.sub.create_line(color='rgba(255,165,0,0.4)', width=1, style='dotted')
self.noise_hi_line = self.sub.create_line(color='rgba(255,165,0,0.4)', width=1, style='dotted')
self.thresh_line = self.sub.create_line(color='rgba(255,255,255,0.3)', width=1, style='dashed')
```

Init-ben (első `.set()` hívás) és update-ben is kitöltve állandó értékekkel (0.425, 0.575, 0.50).

## Előnyök
1. A line series **autoScale-ben részt vesz** → Y-tengely [0,1] fixálva
2. Vizuálisan látszik a zajzóna határ
3. Nincs `_interval=0` bug (mint anchor line-nél volt)
4. `horizontal_line(0.0)` és `horizontal_line(1.0)` megmaradnak label-ként

## Fájlok módosítva
- `/home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py`
