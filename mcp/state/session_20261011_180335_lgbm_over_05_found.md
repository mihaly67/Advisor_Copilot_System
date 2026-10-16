# Session: lgbm_over_05_found
*Időbélyeg: 2026-10-11T18:03:35.451454*

# BTCUSD Predikció Javítás — FŐ FELFEDEZÉS

## KULCS FELFEDEZES: A modell NEM "P(ár fel)"-t prediktál, hanem "P(trade sikeres | CUSUM event)"!

- Backtest AUC 0.88 = meta-label AUC (Triple Barrier siker)
- Élő AUC ≈ 0.50 ha "ár fel/le" label-t használunk — mert NEM EZC AZ a feladat!

## Javítás kísérletek eredménye:

### 1. Feature clip lazítás ±5→±10 → ❌ RONTJA (feature mismatch)
### 2. vol_ratio log1p transform → ❌ RONTJA (AUC 0.50, feature mismatch)
### 3. EREDETI transzformáció (clip ±5, nincs log) → ✅ LGBM=0.53!

## Élő eredmények EREDETI transzformációval (BTCUSD):

| Idő | Ár | MLP | LGBM | ENS | Signal |
|-----|-----|-----|------|-----|--------|
| 18:59 | 83817 | 0.217 | 0.142 | 0.195 | 🔴 SHORT |
| 19:00 | 83724 | 0.212 | **0.534** | 0.309 | 🟡 SHORT+ (LGBM LONG!) |
| 19:01 | 83647 | 0.162 | 0.185 | 0.169 | 🔴 SHORT |
| 19:02 | 83694 | 0.174 | 0.158 | 0.169 | 🔴 SHORT |

## LGBM ÁTLÉPTE 0.5-öt! De w_mlp=0.70 lehúzza az ensemble-t.

## A VALÓS PROBLÉMA:
1. w_mlp=0.70 → MLP dominál, MLP sosem > 0.5
2. MLP RankGauss scaler feature drift miatt beszorult [0.13-0.36]-ba
3. LGBM NEM használ scaler-t → kevésbé drift-érzékeny → jobban mozog

## KÖVETKEZŐ# LÉPÉS:
1. **w_lgbm növelése** → 0.50 vagy 0.70 (MLP csökkentése)
2. **VAGY LGBM-only** → signal = LGBM > 0.5 = LONG
3. **MLP scaler újra tanítás** → élő adaton (drift javítás)
4. **HUD** → LGBM görbe + 0.5 küszöb, nincs MLP, nincs ensemble
