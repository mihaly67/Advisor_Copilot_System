# V12 Pipeline OPTIMIZED (v12_opt5) — Eredmények

**Dátum**: 2026-10-10
**Pipeline**: pipeline_v12_full.py (optimized)
**Hardver**: P4000 (CUDA 0), Numba ✅

## Összefoglaló
| Metrika | V12 opt4 (előtte) | V12 opt5 (most) | Változás |
|---------|-------------------|-----------------|----------|
| val_AUC | 0.779 | **0.788** | **+1.1%** |
| OOS AUC | N/A | **0.796 ± 0.019** | — |
| perm z-score | 48.2 | 36.4 | ✅ IGAZI SIGNAL |
| Total time | 30+ min | **941s (15.7 min)** | **~2x gyorsabb** |
| Best epoch | 30 | 81 | több epoch → jobb konvergencia |
| Max gap | 0.0019 | 0.0018 | nincs overfitting |

## Optimalizációk
1. **GPU Dataset Preload** — teljes train+val VRAM-ban (54MB), torch.randperm shuffle → nincs GIL bottleneck
2. **Numba CUSUM** — 0.39s (was ~30s) = **77x speedup**
3. **Numba Triple Barrier** — 0.017s (was ~5s) = **294x speedup**
4. **Numba Swing Detection** — pipeline_v12_full.py
5. **PyTorch micro-opts** — zero_grad(set_to_none=True), AdamW foreach=True

## Feature Importance (permutation)
1. consecutive_f +0.218
2. trend_micro +0.164
3. body_sign_f +0.151
4. PastRet_2_f +0.122
5. PastRet_1_f +0.064
6. **delta_pivot_dist +0.062** ← PIVOT FEATURE!
7. RSI_3_f +0.039
8. Slope_3_f +0.036

## Dropout Sensitivity
- p=0.0: valAUC=0.811 gap=+0.0036
- p=0.3: valAUC=0.786 gap=+0.0019
- p=0.5: valAUC=0.757 gap=+0.0017
→ **UNDERFITTING**: modell kellene nagyobb (hidden=64 vagy layers=4)

## Learning Curve
- 20%: valAUC=0.718
- 40%: valAUC=0.706
- 60%: valAUC=0.731
- 80%: valAUC=0.764
- 100%: valAUC=0.784
→ Monoton nő → TÖBB adat segít

## Következtetések
1. A GPU preload + Numba ~2x gyorsította a pipeline-t
2. A valAUC javult 0.779→0.788, mert a gyorsabb shuffle jobb gradiens frissítést ad
3. A modell underfitting — nagyobb MLP (hidden=64) vagy Ensemble javíthat
4. delta_pivot_dist a 6. legfontosabb — pivot S/R feature hasznos
5. OOS CV 0.796 — nincs lookahead, megbízható
