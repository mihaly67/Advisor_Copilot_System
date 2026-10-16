# 📊 STANDARD: OOS Vizualizáció — Plotly Dark Theme

**Dátum:** 2026-09-29  
**Minta fájl:** `/data/dev/projects/z-ai-copilot/docs/v104/viz_v104_3day.html`  
**Generator script:** `/data/dev/projects/z-ai-copilot/src/viz_v104_3day.py`

## Leírás
Ez a standard OOS (Out-of-Sample) modell vizualizáció formátum. Minden új modell OOS értékelésekor ezt a layoutot kell használni.

## Layout (3 Plot)
1. **Árfolyam + Trade Szignálok** (500px)
   - Kék vonal: Close ár idősor
   - ▲ Zöld (#228B22): Long nyert trade marker
   - ▲ Világoszöld (#90EE90): Long vesztett trade marker
   - ▼ Piros (#B22222): Short nyert trade marker
   - ▼ Világosrózsaszín (#FFB6C1): Short vesztett trade marker
   - Hover: "Long ✓ $+2" / "Short ✗ $-1"

2. **Cumulative Profit ($)** (350px)
   - Zöld vonal + fill: futó profit görbe
   - Szürke dashed vonal: y=0 (break-even)

3. **Napi Profit ($)** (300px)
   - Zöld bár: nyereséges nap
   - Piros bár: vesztéses nap

## Statisztika Panel (felett)
- Modell név + dátumtartomány
- Trade szám (Long/Short)
- Win Rate (Long/Short)
- Nettó Profit (kiemelt kék)
- Bruttó Nyereség + Bruttó Veszteség
- Profit/Forgalom %
- Threshold paraméterek

## Téma
- **Dark theme** (#1a1a2e háttér, #16213e plot, #eee szöveg)
- **Plotly CDN** v3.6.0: `https://cdn.plot.ly/plotly-3.6.0.min.js`
- **Standalone HTML** — nincs szerver szükséges

## Profit Modell
- Long Win (LW) = +$2.0
- Long Loss (LL) = -$1.0
- Short Win (SW) = +$2.0
- Short Loss (SL) = -$1.0

## Generator Script Struktúra
```python
# 1. Modell + OOS adat betöltés
# 2. predict_thr(): 3-class threshold szűrés
# 3. get_trades(): trade lista profit/loss
# 4. pick3(): utolsó 3 nap kiválasztás (vagy N nap paraméterezhető)
# 5. build_html(): Plotly trace JSON + HTML template
# 6. html_tmpl(): f-string HTML sablon
```

## Használat új modellhez
1. Másoljuk a `viz_v104_3day.py`-t → `viz_<modell>_3day.py`
2. Cseréljük: MODEL_DIR, OOS_PATH, OUT_PATH, thresholds
3. Futtassuk: `/home/Jules/jules_venv/bin/python3 -u viz_<modell>_3day.py`
4. Eredmény: `docs/<modell>/viz_<modell>_3day.html`

## Fontos
- Minden viz HTML standalone — Plotly CDN-ről tölt
- A dark téma konzisztens a HUD-dal (Breeze Dark)
- A trade markerek interaktívak (hover info)
