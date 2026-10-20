# V6 Curve-to-Price Direction Mapping — Session 2026-10-20

## Felismerés összefoglaló

### A probléma
User vizuálisan ~70-75% trend accuracy-t lát FLIP charton (piros görbe magas → bear, zöld magas → bull), de forward-return statisztika csak ~54% WR-t mutat. Ez a discrepancy feloldása.

### A végső felismerés

**A V6 modell KONTRARIÁN (mean-reversion) prediktor — a TBM 2 perces label mean-reversion-t kódol.**

#### Kulcs számok (78 nap, 659K tick):

| Metrika | EREDETI | FLIP |
|---------|---------|------|
| Hátranéző (jelenlegi gyertya) match | **23.0%** | **77.0%** |
| Előrenéző 1 tick WR | **58.1%** | **41.8%** |
| 78 nap PnL | **+1,864,530** | **-1,864,530** |
| Erős dominancia (>0.10) backward | **11.8%** | **88.2%** |
| Erős dominancia (>0.10) forward | **59.8%** | **40.0%** |

#### Cross-Tab (gyertya irány vs. domináns predikció):

| | P(Long) > P(Short) | P(Short) > P(Long) |
|---|---|---|
| **BULL gyertya** | 76,560 (23%) | 256,304 (77%) |
| **BEAR gyertya** | 251,649 (77%) | 75,251 (23%) |

#### Bear streak vs. eredeti predikció (NEM mean-reversion — rögtön 1. bear-nél!):

| Bear streak | EREDETI Long% | FLIP Short% |
|---|---|---|
| 1 bear | 72.7% | 72.7% |
| 3 bear | 83.4% | 83.4% |
| 5 bear | 87.1% | 87.1% |
| 10 bear | 95.3% | 95.3% |

#### TBM Label elemzés (5000 tick minta):

| Label | BULL után | BEAR után |
|-------|-----------|-----------|
| Long TP (y=1) | 30.5% | **37.9%** |
| Long SL (y=-1) | 54.5% | 45.5% |
| Long Noise (y=0) | 50.6% | 49.4% |

Label eloszlás: TP=32.1%, SL=57.2%, Noise=10.7%

#### A 58% forward WR NEM valós edge:

| Stratégia | Forward WR |
|-----------|-----------|
| Mindig Long | 50.3% |
| Trivial kontrarián (BEAR→Long) | 54.4% |
| Eredeti modell | 58.1% |

Edge a trivial felett: csak **+3.7%** — statisztikailag szignifikáns (Z=60, n=659K) de gyakorlatilag elhanyagolható.

#### BTC micro-struktúra (7s tick):
- BEAR után következő tick: **55% BULL** (visszapattan), 45% BEAR
- BULL után következő tick: **54% BEAR** (visszapattan), 46% BULL

### A FLIP illúzió

A FLIP **NEM idő megfordítás** — csak a kimenet címkéit cseréltük. A modell belső súlyai változatlanok.

- FLIP vs előző tick: 77.0% — jónak látszik (ILLÚZIÓ!)
- FLIP vs következő tick: 41.8% — rossz
- A FLIP a JELENT mutatja helyesen, a JÖVŐT rosszul

### P(Long) és P(Short) tulajdonságok

- P(L)+P(S) átlag = 0.88 (NEM 1.0 — külön modellek)
- P(L) és P(S) KÜLÖN LightGBM modellből jönnek
- P(L) = P(TP_long hit first | features) — NEM P(next tick up)
- A forward WR > P(L) mert micro-bounce hozzáad

### Konkrét példa: 2026-08-21 12:00 drawdown

12:00:20-12:01:30 között folyamatos BEAR trend:
- Ár: 78869 → 78245 (−624$)
- Eredeti: P(Long)>P(Short) minden gyertyán → Long jelez → **HIBAS**
- FLIP: P(Short)>P(Long) minden gyertyán → Short jelez → **HELYES vizuálisan**

### Konklúzió

1. **V6 TBM 2min horizon → mean-reversion label → kontrarián modell**
2. **Eredeti: backward 23% (ellentétes a trenddel), forward 58% (micro-bounce + trivial)**
3. **FLIP: backward 77% (követi a trendet), forward 42% (veszt)**
4. **A 58% forward WR = 54% trivial bounce + 4% learned edge — nem valós edge**
5. **A FLIP illúzió: a jelenlegi irányt mutatja helyesen, de a jövőt rosszul**
6. **V8-hoz KELL más label/feature/horizon ha trend-following jelet akarunk**
7. **Scalpernél 10-20 perc NEEM — más megoldás kell**

### Következő session feladat

**ÉLES DEMO TESZT**: split logika — eredeti vs FLIP — demo számlán, hogy kiderüljön a valóság:
- Eredeti signal: P(L)>P(S) → Long, P(S)>P(L) → Short
- FLIP signal: P(S)>P(L) → Long, P(L)>P(S) → Short
- Mindkettőt párhuzamosan futtatni és PnL/WR-t hasonlítani
- Csak ez fogja eldönteni melyik a valóság

### Fájlok amiket létrehoztunk

- `/tmp/v6_streak_label.py` — bear/bull streak vs predikció elemzés
- `/tmp/v6_trend_pnl.py` — trend-szintű PnL összehasonlítás
- `/tmp/v6_drawdown_detail.py` — 08.21 drawdown részletes
- `/tmp/v6_label_deep.py` — TBM label vs gyertya irány deep dive
- `/tmp/v6_58_real.py` — 58% WR valós edge vs trivial elemzés
- `/tmp/v6_prob_analysis.py` — P(Long)/P(Short) vs forward WR
- `/tmp/v6_flip_illusion.py` — FLIP illúzió elemzés
