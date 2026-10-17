# Session: leakage_audit_kesz_20260925
*Időbélyeg: 2026-09-25T19:59:22.782192*

# LEAKAGE AUDIT — KRITIKUS FELFEDEZÉS (2026.09.25.)

## 🚨 FŐ PROBLÉMA: IN-SAMPLE LEAKAGE

A dual_model_jules_nav.py az EGÉSZ V8 CSV-n (31,139 bar) értékel, de a NavSystem v1.01 az első 80%-on tanult!

### Eredmények:
| Részhalmaz | Trades | WR | Profit | Opp | P/T |
|---|---|---|---|---|---|
| **Train (in-sample)** | 3,473 | **97.1%** | +6,646 | 13 | 1.91 |
| **Test (OOS)** | 542 | **51.5%** | +295 | 38 | 0.54 |
| Full (leaked!) | 4,015 | 91.0% | +6,941 | 51 | 1.73 |

A 91% WR azért volt "ilyen jó", mert a NavSystem a saját tréning adatain is prediktált!
OOS: WR=51.5% — alig jobb mint érmefeldobás!

## 🚨 MÁSODIK PROBLÉMA: PRIMARY MODEL NINCS PREDIKTÍV ERŐ

Corr(Slope_Close_14, fwd_ret_5) = 0.006 — gyakorlatilag NULLA!

A V8 labeler Side = Slope_Close_14 > 0 → Long, < 0 → Short. De a Slope_Close_14
nem predikt semmit (corr=0.006 a jövőbeli return-nel). Tehát:
- A Side gyakorlatilag VÉLETLONSZERŰ
- A triple barrier kimenete (Target_Meta) is gyakorlatilag véletlenszerű
- A NavSystem véletlenszerű címkéket tanul → overfittel a tréning adatra

## ✅ KISEBB PROBLÉMÁK (nem kritikusak):
1. Entry price: close[i] nem open[i+1] → mean diff = 0.0042$ (elanyomtalanítható)
2. Slope_Close_14 backward-looking → nem lookahead (de nem is prediktív!)

## 🔧 SZÜKSÉGES JAVÍTÁSOK:

### 1. OOS értékelés:
- Csak a test set-en (utolsó 20%) szabad értékelni
- Vagy walk-forward validation

### 2. Primary model javítása:
- Slope_Close_14 → valami ami tényleg prediktív (momentum, EMA kereszt)
- Vagy: a NavSystem legyen a primary (nem side-alapú, hanem direction-alapú)

### 3. Label javítása:
- A V8 meta-labeling (Side+Target_Meta) túl gyenge alap
- Vissza a V5 triple barrier-hoz (amelynek az entry-je open[i+1])
- Vagy új label: direction-alapú (Long ha felfelé mozgás, Short ha lefelé)

## 📊 JULES V5 KÜLÖN:
A Jules V5 a scalper-copilot adatain tanult (más time range, más bars).
A V8-on WR=24% — ez is rossz, de más okból: más labeling, más feature skálák.
A Jules-nek nincs in-sample leakage a V8-on (más adat), de nem is teljesít jól.

## Fájlok:
- /data/dev/projects/z-ai-copilot/src/leakage_audit.py
- /data/dev/projects/z-ai-copilot/src/dom_labeler_v8.py (forráskód)