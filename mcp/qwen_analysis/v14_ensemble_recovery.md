# V14 Ensemble Pipeline — Áramszünet Recovery

**Dátum**: 2026-10-10 21:50
**GPU**: P4000 (cuda:0)
**Idő**: 546s (~9 perc)

## Áramszünet helyreállítás

Az áramszünet 2026-10-10 21:08-kor történt. A V14 MLP tréning korábban lefutott (20:48), de az ensemble NEM működött mert a régi LGBM v5 feature nevek `Column_0...Column_16` voltak (névtelenek).

## Megoldás

A pipeline_v14.py ensemble részét újraírtuk:
- **Régi**: LGBM v5 betöltés (0 közös feature → ensemble kudarc)
- **Új**: LGBM tanítás az azonos 27 feature-ökkel → **common features!**

## Eredmények

| Modell | valAUC | Megjegyzés |
|--------|--------|------------|
| MLP (h=64,l=4,dp=0.1) | 0.821 | 14,849 params, d/p=16.9 |
| LGBM (500 trees) | 0.833 | 27 feature, early stop |
| **Ensemble (w=0.65/0.35)** | **0.839** | **+2.2% vs MLP alone** |
| OOS (purged CV) | 0.810 ± 0.009 | Nincs overfitting |

## Feature Importance

### MLP (permutation):
1. consecutive_f +0.225
2. trend_micro +0.172
3. PastRet_2_f +0.125
4. body_sign_f +0.103
5. delta_pivot_dist +0.063 ← PIVOT!

### LGBM:
1. delta_pivot_dist 2068 ← PIVOT DOMINÁL!
2. delta_sr_zone_micro 1536
3. PastRet_2_f 1134
4. consecutive_f 1098
5. body_atr_f 990

## Kimentett fájlok

- `models/v14/mlp_meta_v12.pt` — MLP modell
- `models/v14/lgbm_v14.pkl` — LGBM modell
- `models/v14/features.txt` — 27 feature név
- `models/v14/ensemble_config.json` — ensemble config

## Következő lépés

MLP signal → ZMQ → EA integráció (live copilot)
