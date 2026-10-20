# V6 FLIP Illúzió Analízis — 2026-10-20

## Felismerés: A V6 modell mean-reversion-t tanult, nem trend-following-t

### A számok:

| Metrika | EREDETI | FLIP |
|---------|---------|------|
| Hátranéző (jelenlegi gyertya) match | **23.0%** | **77.0%** |
| Előrenéző (következő tick) WR | **58.1%** | **41.8%** |
| 78 nap PnL | **+1,864,530** | **-1,864,530** |

### BTC micro-struktúra (7s tick):
- BEAR után következő tick: **55% BULL** (visszapattan), 45% BEAR (folytatódik)
- BULL után következő tick: **54% BEAR** (visszapattan), 46% BULL (folytatódik)

### A TBM label mean-reversion-t kódol:
- Long TP (y_long=1) gyakoriság: BEAR után **37.9%**, BULL után **30.5%**
- BEAR után gyakrabban Long TP → modell BEAR→Long-ot tanul → KONTRARIÁN

### Bear streak vs predikció:
| Streak hossz | EREDETI Long% | FLIP Short% |
|---|---|---|
| 1 bear | 72.7% | 72.7% |
| 3 bear | 83.4% | 83.4% |
| 5 bear | 87.1% | 87.1% |
| 10 bear | 95.3% | 95.3% |

### A FLIP illúzió:
- FLIP vs előző tick: **77.0%** — jónak látszik (ILLÚZIÓ!)
- FLIP vs következő tick: **41.8%** — rossz
- A FLIP a JELENT mutatja helyesen, a JÖVŐT rosszul
- A modell belső súlyok NEM változtak — csak a kimenet címkéit cseréltük

### Konklúzió:
1. V6 TBM 2min horizon → mean-reversion label → kontrarián modell
2. Eredeti: forward 58% WR (micro-bounce scalping), backward 23% (ellentétes a trenddel)
3. FLIP: backward 77% (követi a trendet), forward 42% (veszt)
4. V8-hoz KELL más label/feature/horizon, ha trend-following jelet akarunk
5. Vagy: hosszabb horizon (10-20 perc) ahol trend-continuation dominál
