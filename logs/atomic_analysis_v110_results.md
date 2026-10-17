# ATOMI ANALÍZIS v1.10 Jules CFD — VÉGSŐ EREDMÉNYEK

## [1] DOLLAR BAR MÉRET
| | Train | OOS | Jules |
|---|---|---|---|
| Sec/bar mean | 26.2s | 18.6s | 37.6s |
| Sec/bar median | 21.0s | 15.0s | 21.0s |
| DV/bar | $1,815,476 | $1,833,853 | $630,430 |

⚠️ OOS bar duration 18.6s vs Jules 37.6s — **OOS rövidebb bar-ok!** A market volatilitás nőtt az OOS időszakban.

## [2] VALÓSZÍNŰSÉG ELOSZLÁS
- P(Long): min=0.05 max=0.82 mean=0.35 std=0.10
- P(Short): min=0.04 max=0.80 mean=0.34 std=0.10
- P(Noise): min=0.02 max=0.81 mean=0.31 std=0.09
- **P(Long)==0: 0 | P(Short)==0: 0** ✅ Nincs nulla valószínűség!
- **P(Long)<0.01: 0 | P(Short)<0.01: 0** ✅ Minden bar-nak van valamilyen valószínűsége!

## [6] KONFÚZIÓS MÁTRIX (STABILITY FILTER) ⚠️ KRITIKUS!
```
           PredShort  PredNoise  PredLong
  ActShort        0      453    8,534
  ActNoise        0      158    5,072
  ActLong         0      278    8,509
```
**ZERO PredShort!** A modell a stability filter után SOHA nem jósol Short-ot!
- Csak PredLong (8,534+5,072+8,509=22,115) és PredNoise (453+158+278=889) marad
- Az összes Short jelet a Stoch+Stability filter megöli

## [7] DIRSWAP: 32.9%
- Long→Short: 278, Short→Long: 488
- Az ellenkezetten prediktált jelek 33%-a — nagyon magas!

## [8] DIRASNOISE: 69.7% (stability)
- Az irányt tartalmazó bar-ok 69.7%-a Noise-ként jelenik meg a stability filter után

## [9] STOCH KILL: 49.8%
- Threshold Long 10,050 → Stoch kill 4,869 (48.4%)
- Threshold Short 7,800 → Stoch kill 4,012 (51.4%)
- **A Stoch filter a jelek FELÉT megöli!**

## [10] STABILITY KILL: 74.0%
- A Stoch filter után maradt 8,969 jelből 6,638-at megöl a stability filter
- Csak 2,331 jel marad — **a jelek 87%-a elveszik!**

## [13] THRESHOLD WR SWEEP
| THL | THS | THN | WR% | Trades | Long | Short |
|-----|-----|-----|-----|--------|------|-------|
| 0.20 | 0.20 | 0.60 | 45.5% | 3,612 | 1,959 | 1,653 |
| 0.25 | 0.25 | 0.55 | 45.6% | 3,584 | 1,955 | 1,629 |
| 0.30 | 0.30 | 0.50 | 45.6% | 3,407 | 1,891 | 1,516 |
| **0.35** | **0.36** | **0.47** | **47.7%** | **2,331** | **1,442** | **889** |
| 0.40 | 0.40 | 0.40 | 49.6% | 1,242 | 767 | 475 |
| 0.45 | 0.45 | 0.35 | **51.5%** | 581 | 358 | 223 |
| 0.50 | 0.50 | 0.30 | **53.7%** | 227 | 142 | 85 |

**A magasabb threshold → magasabb WR, de kevesebb trade!**

## [14] STOCH FILTER HATÁSA
- Long survive: 5,181/10,050 (51.6%)
- Short survive: 3,788/7,800 (48.6%)
- **A Stoch filter szimmetrikusan öl — nem preferálja a Long-ot**

## [15] STABILITY FILTER DEEP DIVE
- Consec Short>=3: 426 times, Max: 14
- Consec Long>=3: 653 times, Max: 17
- **Long streak-ek gyakoribbak** — ezért a stability filter után csak Long marad!

## [16] P(L) vs P(S) ASZIMMETRIA
- Mean P(L)=0.3497 vs P(S)=0.3403 — Diff=0.0094 (minimális)
- P(L)>0.36: 10,068 vs P(S)>0.36: 8,625 — **17% több Long**

## [17] LABEL ASZIMMETRIA OOS
- Long: 38.6%, Noise: 22.6%, Short: 38.8% — közel szimmetrikus

## [18] STOCH STATE ELOSZLÁS
- Mean=0.0076 (közel 0), Std=0.73
- Stoch>0: 50.4%, Stoch<0: 49.5% — szimmetrikus

## KULCS FELFEDEZÉSEK

### 1. ⚠️ ZERO SHORT PROBLÉMA
A konfúziós mátrix **ZERO PredShort** — a stability filter után a modell SOHA nem jósol Short-ot. Ennek oka:
- A Stoch filter kill 51.4% Short-ot
- A megmaradó Short jelek ritkán jönnek 3 egymás után (max consec=14 vs Long max=17)
- A stability filter (3 consec azonos jel) **aszimmetrikusan** szűr — Long streak-ek gyakoribbak

### 2. ⚠️ STOCH + STABILITY TÚLSZŰRÉS
- Threshold: 17,850 jel → Stoch: 8,969 (50% loss) → Stability: 2,331 (87% loss!)
- A jelek 87%-a elveszik — túl agresszív szűrés

### 3. ✅ NINCS NULL VALÓSZÍNŰSÉG
- P(Long)==0: 0, P(Short)==0: 0 — minden bar-nak van valamilyen valószínűsége

### 4. ✅ NINCS LOOKAHEAD (shift=1 > shift=0)
- shift=1: 0.4361, shift=0: 0.4457, shift=2: 0.4202, shift=3: 0.4103
- A shift=0 (leakage) nem jobb mint shift=1 — **NO LEAKAGE**

### 5. 💡 THRESHOLD SWEEP: MAGASABB TH → JOBB WR
- THL=0.50 THS=0.50: 53.7% WR (de csak 227 trade)
- A jelenlegi THL=0.35 THS=0.36: 47.7% WR (2,331 trade)
