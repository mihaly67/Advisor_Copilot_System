# Session: v11_mlp_pipeline_complete
*Időbélyeg: 2026-10-10T03:55:42.499570*

V11 MLP PIPELINE COMPLETE:
- pipeline_v11_mlp.py implemented and tested
- 18 features (32→18 reduction), RankGauss normalized, RSI centred
- Per-bar binary meta-label (618 TP / 42,742 bar = 1.4%, 68:1 imbalance)
- MLP: 657 params, H=16, L=2, dropout=0.3, Focal Loss α=0.25 γ=2.0
- LABEL PERMUTATION: Real AUC=0.879, Random=0.516±0.021, z=17.1 → ✅ IGAZI SIGNAL
- FŐ MODELL: val_AUC=0.879, best_ep=9, gap=-0.020 → NINCS overfitting
- LEARNING CURVE: val_AUC still increasing at 100% → TÖBB adat segít
- DROPOUT: p=0.3 optimális (0.886 vs 0.862 p=0.0) → enyhe overfitting p=0.0-nál
- PURGED CV: OOS AUC = 0.813 ± 0.040 → stabil
- Model saved: models/v11/mlp_meta_v11.pt
- NEXT: LGBM vs MLP discrepancy, S/R features, visualization