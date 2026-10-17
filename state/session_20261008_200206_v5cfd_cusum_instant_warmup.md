# Session: v5cfd_cusum_instant_warmup
*Időbélyeg: 2026-10-08T20:02:06.033663*

# V5 CFD Live Pipeline — CUSUM azonnal aktív (2026-10-08 v2)

## Bug javítások
1. **BAR_HISTORY_LEN 30→60**: A deque túl kicsi volt, sosem érte el a CUSUM_WARMUP_BARS=50-ot
2. **CUSUM_WARMUP_BARS 50→30**: Csökkentve a gyorsabb aktiváláshoz
3. **MacroReceiver HUD broadcast eltávolítva**: Csak macro_cache-t frissít, nem küld HUD-ot (ez okozta a P(L)=0.0 flood-ot a HUD-ban)
4. **has_pred flag**: A `_hud_dict` és `eval_and_broadcast` jelzi ha van érvényes predikció, a HUD csak akkor rajzol subchart-ot
5. **200 történeti dollár bar warmup**: `warmup_from_csv()` — 80000 tick → 841 dollár bar → bar_close_history + CUSUM state feltöltve azonnal
6. **HUD timestamp parse**: Rugalmas — unix epoch float VAGY datetime string

## Fájlok
- Copilot: `/home/Jules/LGBM_mlops/Micro_LGBM/src/mt5_live_copilot_v5_cfd.py` (~380 sor)
- HUD: `/home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py` (~160 sor)
- Start: `/home/Jules/LGBM_mlops/start_v5_cfd.sh`

## Élő eredmények
- CUSUM AZONNAL AKTÍV (841 bar history + CUSUM state betöltve CSV-ből)
- CUSUM ↓ → Fade Long ✅
- CUSUM ↑ → Fade Short ✅
- Signal: -1 Short, 0 No trade, 1 Long ✅
- EA csatlakozik MACRO:5555 + TICK:5556 ✅

## Ismert issue
- HUD subchart: `js: Value is null` — nem kritikus, első update hiba
- A CUSUM threshold $2.39 a history-ból számítva (841 bar), élő adatokkal finomodik
