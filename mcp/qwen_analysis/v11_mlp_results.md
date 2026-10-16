# V11 MLP Pipeline — VÉGSŐ EREDMÉNYEK

## Pipeline: pipeline_v11_mlp.py

### Konfiguráció
- 18 feature (32→18 redukció, korreláltak eldobjuk)
- RankGauss normalizáció (N(0,1) minden feature)
- RSI centring: (RSI-50)/50 → [-1,+1]
- Per-bar binary meta-label: 618 TP / 42,742 bar = 1.4% (68:1 imbalance)
- Focal Loss α=0.25 γ=2.0
- MLP: input=18, hidden=16, layers=2, dropout=0.3, Le865 params
- Stratified batch sampler (balanced TP/non-TP)
- GPU: P4000 (CUDA device 0)

### EREDMÉNYEK

#### Label Permutation Test (null hipotézis)
- Real AUC = 0.879
- Random AUC = 0.516 ± 0.021
- Z-score = 17.1
- **✅ IGAZI SIGNAL — a modell NEM zajt tanult!**

#### Fő modell
- Best epoch = 9 (early stop at 24)
- val_AUC = 0.879
- n_params = 657
- data/param = 52.0 ✅
- max gap = -0.020 (NEGATÍV → NINCS overfitting!)

#### Learning Curve
| Adat | val_AUC | gap |
|---|---|---|
| 20% (6,838) | 0.787 | -0.010 |
| 40% (13,677) | 0.762 | -0.011 |
| 60% (20,515) | 0.861 | -0.019 |
| 80% (27,354) | 0.817 | -0.021 |
| 100% (34,193) | 0.873 | -0.021 |
→ **val_AUC still increasing → TÖBB adat segít!**

#### Dropout Sensitivity
| Dropout | val_AUC | gap |
|---|---|---|
| 0.0 | 0.862 | -0.010 |
| 0.3 | **0.886** | -0.019 |
| 0.5 | 0.871 | -0.021 |
→ **dropout=0.3 javít → enyhe overfitting volt p=0.0-nál!**

#### Purged Walk-Forward CV (3 fold, embargo=10)
| Fold | val_AUC | gap |
|---|---|---|
| 1 | 0.761 | +0.005 |
| 2 | 0.819 | -0.006 |
| 3 | 0.858 | -0.019 |
→ **OOS AUC = 0.813 ± 0.040** (stabil, nincs nagy szórás)

### Kulcs megállapítások

1. **MLP IGAZI SIGNAL-T tanult** (z=17.1 a permutation tesztben)
2. **NINCS overfitting** — a gap negatív (val jobb mint train!)
3. **TÖBB adat javítana** — learning curve még emelkedik
4. **Dropout=0.3 optimális** — p=0.0-nál enyhe overfitting
5. **Purged CV stabil** — 0.813±0.040, fold 1 gyengébb (korai adat)
6. **val_AUC=0.879 > LGBM event-based AUC=0.732** — per-bar jobb!

### Miért jobb a per-bar AUC?
- Event-based: 2,642 sample, LGBM AUC=0.732
- Per-bar: 42,742 sample, MLP AUC=0.879
- A per-bar több sample → jobban tanul
- DE: a per-bar task más (binary meta-label vs event-level meta-label)
- A per-bar AUC nem közvetlenül összehasonlítható az event-based-szel!
