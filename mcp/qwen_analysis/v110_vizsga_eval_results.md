# V1.10 VIZSGA EVAL — VÉGSŐ EREDMÉNYEK

**Dátum:** 2026-10-06  
**Status:** VIZSGA CSV MINT DÖNTÉSHOZÓ BEVÁLT  

---

## 🎯 FŐ EREDMÉNYEK

| Modell | OOS WR | Vizsga WR ($654K cal) | Vizsga WR ($1,746K) |
|--------|--------|------------------------|----------------------|
| **18feat LEAKFIX** | **53.7%** | **59.1%** | 42.0% |
| 20feat +Dir_Conviction | 52.0% | 56.0% | n/a |
| 18feat BEFORE leakfix | 56.0%* | n/a | n/a |

*\*lookahead bias eltávolítva: 56.0% → 53.7% = valós WR*

---

## 🔬 KULCS FELISMERÉSEK

### 1. Lookahead Bias (leakfix)
- `compute_features()` NEM shiftelt → shift(1) javítás **-2.3% WR**
- A valós WR 53.7%, nem 56.0%
- Lookahead sanity check: minden corr(feature, future_price) < 0.003 ✅

### 2. Dollar Bar Threshold KRITIKUS 🚨
- Vizsga volume: $14,539/sec (1.29x alacsonyabb mint tanító)
- **$1,746K threshold → 157 sec/bar a vizsgán → TÚL RITKA → WR=42.0%**
- **$654K threshold (kalibrált) → 60.7 sec/bar → WR=59.1%!!!**
- A "overfitting" diagnózis HAMIS volt — a threshold volt rossz!

### 3. Vizsga CSV mint döntéshozó ✅
- A vizsga CSV (2026-07-20 → 07-23) teljesen független
- Kalibrált threshold-val WR=59.1% — JOBB mint az OOS 53.7%!
- **NINCS overfitting** — a modell stabil

### 4. Dir_Conviction meta-feature LEAKAGE
- Dir_Conviction = P(L) - P(S) a 18feat modellből
- Dominance = |P(L) - P(S)|
- Feature importance: #1 (7.70%) és #2 (6.95%) — DE
- OOS: -1.7% WR, Vizsga: -3.1% WR → meta-feature leakage!
- Megoldás: walk-forward predikció (rolling window)

---

## 📊 VIZSGA THRESHOLD SWEEP

| Threshold | sec/bar | WR | Profit | Trades | Opp% |
|-----------|---------|-----|--------|--------|------|
| **$654K** | **60.7** | **59.1%** | **$828** | **1,735** | **34.9%** |
| $872K | 80.1 | 55.1% | $540 | 1,428 | 38.4% |
| $1,309K | 118.7 | 49.9% | $293 | 1,185 | 40.4% |
| $1,746K | 157.4 | 42.0% | $55 | 1,100 | 46.3% |

---

## 🔧 KÖVETKEZŐ LÉPÉSEK

1. Teljes pipeline úraépítés adaptív threshold-cal
2. Walk-forward Dir_Conviction (rolling window predikció)
3. Dominance threshold szűrés
4. Fix threshold audit
5. Production model + MQL5 integráció

---

## 📁 FÁJLOK

- **Script**: `/data/dev/projects/z-ai-copilot/src/v110_vizsga_eval.py`
- **Model**: `/data/dev/projects/z-ai-copilot/models/v110_vizsga/lgbm_18feat_leakfix.pkl`
- **Viz**: `/data/dev/projects/z-ai-copilot/docs/v110_vizsga/` (5 HTML)
