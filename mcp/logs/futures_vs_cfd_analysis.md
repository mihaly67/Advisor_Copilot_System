# Jules Pipeline: Futures vs CFD — VÉGSŐ ÖSSZEHASONLÍTÁS

## Kérdés: Lehet CFD-re állítani a rendszert?

### Válasz: IGEN, technikailag igen, de a teljesítmény drasztikusan csökken

## Pipeline konfiguráció
| | Jules (Futures) | CFD adaptáció |
|---|---|---|
| Szimbólum | GCEQ26 micro gold futures | XAUUSD CFD |
| Volume forrás | `volume_real + TICK_FLAG_BUY/SELL` | Tick-count proxy |
| Threshold | $444,000 | $1,746,000 (kalibrált ×3.93) |
| Bid≠Ask volume | **66%** (directionális!) | **2.3%** (szimmetrikus) |
| Sec/bar mean | 37.6s | 40.1s ✅ |
| Sec/bar median | 21.0s | 21.0s ✅ |

## Eredmények
| Metrika | Jules Futures | CFD | Különbség |
|---|---|---|---|
| **WR (threshold)** | **62.4%** | 48.3% | **-14.1%** |
| **WR (+ Stoch)** | **63.7%** | 47.3% | **-16.4%** |
| **WR (+ Stable)** | — | 47.7% | — |
| Trades (threshold) | 13,394 | 17,850 | +33% |
| Noise label | **9.9%** | **20.7%** | **+11%** |
| Circ | — | 0.1167 | — |
| Leakage | — | NO ✅ | — |
| Walk-Forward | — | 49.3%±2.6% | — |

## Miért csökken a teljesítmény?

### 1. Directionális volume elvesztése
- **Futures**: `TICK_FLAG_BUY → Ask_Volume`, `TICK_FLAG_SELL → Bid_Volume`
  - Bid≠Ask 66%-ban → OBI (Order Book Imbalance) jelek elérhetők
- **CFD**: Nincs `TICK_FLAG_BUY/SELL`, nincs `volume_real`
  - Bid≈Ask 97.7%-ban → **Nincs directionális volume info**
  - OBI mindig ≈0 → haszontalan feature

### 2. Noise duplázódik
- Futures: 9.9% noise → a labeler 90%-ban tud irányt adni
- CFD: 20.7% noise → a labeler csak 79%-ban ad irányt
- A CFD spread szélesebb, price dynamics oldalazóbb

### 3. Volume skálázás
- A tick-count proxy MINDEN ticket számolja (bid+ask update)
- A futures volume csak a tényleges trade-eket
- Arány: CFD $71,856/sec vs Futures $18,271/sec = 3.93x

## Javaslatok CFD javításra

1. **DOM depth (MarketBook) volume proxy** — MT5 `MarketBookGet` → valósi bid/ask depth
2. **Tick flag szűrés** — csak `TICK_FLAG_LAST` + `TICK_FLAG_VOLUME` ticket számolni
3. **Label paraméter hangolás** — PT/SL növelése CFD spread-hez
4. **Több feature** — OBI helyett pl. CVD (Cumulative Volume Delta) proxy
5. **Külön CFD modell tanítása** — ne Jules futures paramétereit használni
