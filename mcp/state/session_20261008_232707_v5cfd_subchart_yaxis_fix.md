# Session: v5cfd_subchart_yaxis_fix
*Időbélyeg: 2026-10-08T23:27:07.291780*

# V5 CFD HUD Subchart Y-tengely fix (2026-10-09)

## Probléma
A subchart Y-tengelye beragadt az árfolyam skálába (XAUUSD $4100+, BTC $81000+) ahelyett, hogy [0,1] valószínűség tartományt mutatna.

## Gyökéroka
A lightweight_charts v4.1.0-rc2 (Python wrapper) `autoScale:true` esetén a Y-tengélyt a series adatpontjaihoz igazítja. Ha csak 1-2 pont van (pl. value=0.516), a tartomány nem fedi a [0,1]-et. Az `autoScale:false` nem segít mert nincs `setVisibleRange()` a v4.x API-ban (csak v5.x).

## Megoldás
Az init-nél a P(Long) line 3 pontot kap:
- 2 perccel korábban: value=0.0 (alsó anchor)
- 1 perccel korábban: value=1.0 (felső anchor)  
- jelen idő: value=pl (tényleges valószínűség)

Az autoScale ezekhez a pontokhoz (0.0–1.0) igazítja a Y-tengelyt → [0,1] fixálva.

## Tanult leckék
1. `lightweight_charts` v4.x NINCS `setVisibleRange()` a priceScale-en — csak v5.x-ben
2. `create_line(color='rgba(0,0,0,0)',width=0)` → `_interval=0` → `ZeroDivisionError: float floor division by zero` a `.update()` hívásnál
3. Anchor series megközelítés NEM működik v4.x-ben a `_interval=0` bug miatt
4. A `horizontal_line(0.0)` és `horizontal_line(1.0)` priceLine-ok NEM befolyásolják az autoScale-t

## Fájlok
- `/home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py`
- `/home/Jules/LGBM_mlops/Micro_LGBM/src/mt5_live_copilot_v5_cfd.py`
