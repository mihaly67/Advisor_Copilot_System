# NN/MLP Tanulmányi Jegyzetek — V10→V11 átmenet

## 1. Tankönyvek (repók amiket tanulmányoztam)

### Financial-Forecasting-MLP-main
- **MLP architektúra**: `nn.Linear(input, hidden) → ReLU → ... → nn.Linear(hidden, 1)`
- Hidden size: 16-64, layers: 1-5
- **Preprocess**: differencing (de-trend) → MinMaxScaler(-1,1)
- **Dataset**: sliding window (window_size=2-8), X=window, y=next
- **BlockedCV**: time-series split, nem random!
- **Optuna**: lr, hidden_size, hidden_layers, num_epochs, window_size, lambda_reg
- **Loss**: L1Loss (MAE) vagy SMAPE
- **Adam optimizer** weight_decay (L2 regularizáció)

### decision_features.py (meta-labeling-harness)
- **Kulcs elv**: minden feature scale-free (returns, ratios, gaps, centred oscillators)
- **Feature kategóriák**:
  1. Trailing returns: ret_1, ret_5, ret_10, ret_21, ret_63
  2. MA structure: sma20_gap, sma50_gap, sma200_gap, fast_slow, slope
  3. Oscillators: rsi_14 (centred!), macd_hist, donchian_pos, dist_high, dist_low
  4. Volatility: atr_pct, vol_20, vol_ratio, range_20d
  5. Microstructure: gap_open, vol_z, dvol_ratio
  6. Market-relative: relret, beta, resid_ret, xsec_rank
- **Pre-entry rule**: `pre = df[df.index < entry_ts]` — semmi lookahead!

### Financial-Time-Series-Forecasting-main
- **GAF (Gramian Angular Field)**: time series → 2D image → CNN
- **CNN+LSTM pipeline**: ResNet feature extraction → LSTM forecasting
- GAF lassú és bonyolult — MLP direct approach is sufficient for our case

## 2. Normalizáció stratégiák (mit tanultam)

| Módszer | Range | Használat | Pro | Kontra |
|---|---|---|---|---|
| MinMaxScaler | [-1,1] vagy [0,1] | MLP input | Egyszerű | Outlier-ék rossz |
| StandardScaler | z-score | Ha normál eloszlás | Stabil | Nem bounded |
| RobustScaler | median/IQR | Outlier-ékkel | Robust | Lassabb |
| **RankGauss** | → N(0,1) | **LGBM→NN átmenet** | Uniform, NN-barátd | Non-linear |
| **Online scaler** | rolling | Éles predikció | Nincs lookahead | Komplex |

**Döntés**: RankGauss a legjobb NN-hez — minden feature-et normál eloszlásba transzformál

## 3. MLP vs LSTM vs más

| Architektúra | Param count | P4000 mem | Tanulás | Interpretability |
|---|---|---|---|---|
| **MLP** (3-5 layer) | ~1-10K | <100MB | Gyors | Közepes (SHAP) |
| LSTM | ~10-100K | <500MB | Lassú | Gyenge |
| CNN-1D | ~5-50K | <200MB | Közepes | Gyenge |
| Transformer | ~100K+ | >1GB | Nagyon lassú | Gyenge |

**Döntés**: MLP a primary — perceptront variáns, ahogy Jules kérte
- BatchNorm + Dropout + residual skip
- P4000-n 8GB VRAM → bőséges

## 4. S/R (Support/Resistance) azonosítás — 3 szint

### Algoritmus:
1. **ZigZag pivot detection** — már van a dollár bar-ban (Micro_R/S, Sec_R/S, Ter_R/S)
2. **Fractal S/R** — Williams fractal: high[i] > high[i±1] → resistance
3. **Volume-weighted S/R** — ahol sok volume van adott árszinten
4. **Round number S/R** — 4220, 4225, 4230 stb. (psychological levels)

### Encoding NN-nek:
- `dist_to_SR_level_1 / ATR` — normalized távolság
- `above_below_SR_1` — {-1, 0, +1} (alatt/rajta/felett)
- `SR_strength_1` — hányszor érintette (count)

## 5. Swing azonosítás (vállak)

- **Swing High**: high[i] > high[i-1] AND high[i] > high[i+1]
- **Swing Low**: low[i] < low[i-1] AND low[i] < low[i+1]
- **Left/Right strength**: milyen mély a swing (hanyadik bar mindkét oldalon)
- **Encoding**: 
  - `swing_type` ∈ {high, low, none}
  - `swing_age` — hány barja történt
  - `swing_retracement` — mennyit lépett vissza (Fibonacci szintek)

## 6. Mikro/Közép/Makro trend

| Szint | Window | Feature |
|---|---|---|
| **Mikro** | 3-5 bar | Slope_3, RSI_3, body_sign |
| **Közép** | 8-20 bar | EMA_8/20, RSI_14, Slope_10 |
| **Makro** | 50-200 bar | SMA_50/200, trend_regime |

Encoding: `trend_micro ∈ {-1, 0, +1}`, `trend_mid`, `trend_macro`
Alignment: micro↑ + mid↑ + macro↑ = strong trend (nem jó MR-re!)

## 7. Per-bar predikció architektúra

```
Dollar bar érkezik (OnTick)
  → Feature generálás (37+ új SR/swing/trend feature-ök)
  → Normalizáció (RankGauss / rolling z-score)
  → LGBM predikció: p_lgbm, weight_sigmoid
  → MLP predikció: p_mlp
  → Diszkrepancia: Δ = p_lgbm - p_mlp
  → Ha |Δ| > threshold → ⚠️ diszkrepancia flag (nem felülír!)
  → Végső döntés: LGBM主导, MLP advisory
  → Vizualizáció: probability heatmap per bar
```
