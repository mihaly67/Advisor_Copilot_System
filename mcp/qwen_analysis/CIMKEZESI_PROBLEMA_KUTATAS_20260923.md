# Címkézési Probléma — Kutatási Eredmények
*Időbélyeg: 2026-09-23*

## A Probléma (User által megfogalmazva)

### Vesztő pozíció → EGYÉRTELMŰ
- SL elérése → zárás → új predikció. Ennyi.

### Profitos pozíció → KIHÍVÁS
1. **PT elérése**: ha eléri a profit targetet, az NEM jelenti automatikusan a zárást!
   - Lehet, hogy a profit TOVÁBB nő
   - Kérdés: mikor álljon le és adjon új predikciót?
2. **3× küszöb (user javaslat)**: ha a profit eléri a 3× PT-t → adjon új predikciót + zárási javaslat
   - Ha eléri a 3×-ot, TOVÁBB tolja a maximumot (trailing)
3. **Visszaesések**: profit pozícióban is lehet drawdown
   - Tartós visszaesés → nullába eshet → SL-be szaladhat
   - Ezt figyelnie kell!

## Jules Eredeti Labeler (dom_labeler_v5.py)
- **Triple Barrier** statikus küszöbökkel: PT=1.5$, SL=1.0$
- **max_bars=5** (vertical barrier — 5 bar után Noise)
- **Strict wick**: intra-bar SL/PT ütközés → SL nyer (konzervatív)
- **NEM VAN** trailing, NEM VAN dinamikus exit, NEM VAN profit menedzsment

## RAG-ból talált megoldások

### 1. Freqtrade Trailing Stop (legérettebb)
```
stoploss = -0.10
trailing_stop = True
trailing_stop_positive = 0.02       # 2% trailing ha pozitív
trailing_stop_positive_offset = 0.03  # trailing aktiválódik 3% profit felett
trailing_only_offset_is_reached = True  # addig statikus SL
```
**Logika:**
- Entry 100$, SL=90$ (-10%)
- Ár megy 103$-ig (offset elérése) → trailing aktiválódik
- SL most: 103$ × 0.98 = 100.94$
- Ár esik 101$-ra → SL trigger 100.94$-n
- **Kulcs:** offset = küszöb a trailing aktiválásához

### 2. Kalshi AI Trading Bot — Dynamic Exit Strategy
`calculate_dynamic_exit_strategy(confidence, volatility, time_to_expiry, price, edge)`
- **Trailing take-profit** at 20% gain
- **Stop-loss** at 15% drawdown
- **Confidence-decay exits** when AI conviction drops
- **Time-based exits** with max hold period
- **Smart SL calculator** (utility modul)

`should_exit_position(position)` — 4 kimenet:
1. Trailing profit trigger
2. Drawdown túl nagy
3. Confidence lecsökkent
4. Time lejárt

### 3. López de Prado mlfinlab (eredeti Triple Barrier)
`apply_pt_sl_on_t1(close, events, pt_sl, molecule)` — Snippet 3.2
- **pt_sl[0]** = profit taking szorzó (ATR-norm)
- **pt_sl[1]** = stop loss szorzó (ATR-norm)
- **Aszimmetrikus**: PT ≠ SL
- **Vertical barrier**: max időkorlát
- **Side prediction**: meta-model mondja irányt

### 4. Hunter Project — Exit Time Estimation
`estimate_exit_time(entry_time, pnl_pct, reason)`
- CSV-ből becsült exit time PnL és reason alapján

## Tervezett Megoldás: Z.ai Copilot Adaptive Labeler

### Koncepció: 4 rétegű exit rendszer

```
┌─────────────────────────────────────────────────┐
│  RÉTEG 1: Statikus Triple Barrier (belépés)     │
│  PT=1.5$, SL=1.0$, max_bars=5                   │
│  → ha PT eléri: NEM zár, megy Réteg 2-be       │
│  → ha SL eléri: ZÁR → új predikció             │
│  → ha vertical: ZÁR (Noise) → új predikció     │
├─────────────────────────────────────────────────┤
│  RÉTEG 2: Trailing Profit (PT elérése után)     │
│  activation_offset = 1.5$ (PT elérése)          │
│  trailing_distance = 0.5$ (ATR-norm)            │
│  → trailing SL = max_profit - trailing_dist     │
│  → ha ára esik trailing SL alá: ZÁR → új pred  │
├─────────────────────────────────────────────────┤
│  RÉTEG 3: Profit Extenzió (3× PT elérése)       │
│  ha profit ≥ 3 × PT = 4.5$:                    │
│    → trailing_distance szűkül: 0.3$             │
│    → új predikció generálása (ZÁR javaslat)    │
│    → ha modell mást mond: ZÁR + fordított       │
├─────────────────────────────────────────────────┤
│  RÉTEG 4: Drawdown Védelem                      │
│  max_drawdown_from_peak = 1.0$ (SL szint)       │
│  ha profit visszaesik > max_dd: ZÁR → új pred  │
│  (ez független a trailing-től)                  │
└─────────────────────────────────────────────────┘
```

### Label Kimenet (bővített)
- **+1**: Long (PT elérése várható)
- **-1**: Short (PT elérése várható)
- **0**: Noise (SL vagy vertical barrier)
- **+2**: Long Extended (trailing profit → 3× PT elérése)
- **-2**: Short Extended

### Fontos: ez a LABELER módosítás, NEM a live EA
- A labeler tanítja a modellt, hogy mikor van PT vs SL
- A live EA-ban (MQ5) implementáljuk a trailing logikát
- A labeler most: statikus Triple Barrier → később bővítjük

## Következő Lépés
1. Most: implementáljuk a statikus Triple Barrier labelert (Jules módja, adaptálva)
2. Később: bővítjük trailing + profit extension rétegekkel
3. Live EA: MQ5-ben implementáljuk a 4 rétegű exit rendszert
