# V11 MLP Terv — Lépésről Lépésre

## Cél
MLP (perceptront variáns) a LGBM mellé — **diszkrepancia-jelző**, nem felülíró.
Per-bar predikció, 3-szintű S/R, swing azonosítás, mikro/közép/makro trend.
Normalizáció + featuring + pipeline + tanítás P4000-n.

## Fázisok

### Fázis 1: Normalizáció + Feature mérnökség (2-3 óra)
1. **RankGauss normalizáció** — minden feature N(0,1)-be
2. **S/R azonosítás 3 szinten**:
   - Mikro: ZigZag pivot (már van Micro_R/S a dollár bar-ban)
   - Közép: Sec_R/S (már van)
   - Makro: Ter_R/S (már van) + round number levels
3. **Swing detection** (vállak):
   - Swing High/Low detection (N-bar left/right)
   - Swing age, retracement, type encoding
4. **3-szintű trend**:
   - Mikro: Slope_3, RSI_3, body_sign → trend_micro
   - Közép: EMA_8/20 crossover → trend_mid
   - Makro: SMA_50/200 regime → trend_macro
5. **NN? Új feature-ök listája**:
   - dist_to_sr_micro/ATR, dist_to_sr_sec/ATR, dist_to_sr_ter/ATR
   - above_below_sr_micro, above_below_sr_sec, above_below_sr_ter
   - swing_type, swing_age, swing_retracement
   - trend_micro, trend_mid, trend_macro
   - trend_alignment (micro==mid==macro?)

### Fázis 2: Dataset + DataLoader (1-2 óra)
1. **Sliding window dataset** — window_size=10-20 bar
2. X = [bar_{t-W}, ..., bar_{t-1}] → 37×W feature matrix
3. y = meta_label (0 vagy 1)
4. **Blocked time-series split** — soha random!
5. PyTorch DataLoader, batch_size=64, P4000-re

### Fázis 3: MLP Architektúra (1-2 óra)
1. **Perceptront variáns**:
   ```
   Input(37×W) → BatchNorm → Linear(H) → ReLU → Dropout(0.3)
   → Linear(H) → ReLU → Dropout(0.2)
   → Linear(H//2) → ReLU
   → Linear(1) → Sigmoid → probability
   ```
2. **Residual skip**: x + Linear(x) minden hidden layer-ben
3. **BatchNorm** — stabilizálja a tanítást
4. **Focal Loss** — class imbalance (22% TP vs 78% SL)
5. H ∈ {32, 64, 128}, W ∈ {10, 15, 20}

### Fázis 4: Tanítás + Optuna (2-3 óra)
1. **Blocked 5-fold CV** — time-series purge
2. **Optuna**: lr, hidden_size, num_layers, window_size, dropout, weight_decay
3. **Early stopping** — patience=20
4. **GPU P4000** — CUDA, batch parallelism
5. **Metrics**: AUC, profit@threshold, calibration curve

### Fázis 5: Diszkrepancia rendszer (1 óra)
1. **Per-bar**:
   - p_lgbm = LGBM.predict_proba(features)
   - p_mlp = MLP.forward(normalized_features)
   - Δ = p_lgbm - p_mlp
   - flag = |Δ| > threshold
2. **Nem felülír!** Csak jelzi ha nem ért egyet
3. **Vizualizáció**:
   - Probability timeline (LGBM kék, MLP piros, Δ szürke)
   - S/R szintek horizontális vonalakkal
   - Swing pontok markerekkel
   - Trend szalag (micro/mid/macro színek)

### Fázis 6: Vizualizáció — a végső ítélet (2 óra)
1. **Plotly interaktív** — sötét theme
2. **Per-bar probability heatmap** — szín = confidence
3. **S/R szintek** — 3 szint, strength = vonal vastagság
4. **Swing vállak** — ▲▼ markerek
5. **Trend szalag** — mikro/közép/makro színek
6. **LGBM vs MLP disagreement** — ⚠️ ikon
7. **PnL timeline** — equity curve

## Kulcs döntések

| Döntés | Választás | Indok |
|---|---|---|
| Normalizáció | RankGauss | Uniform, NN-barát, LGBM→NN átmenet |
| Architektúra | MLP (nem LSTM) | Jules kérte perceptront, kevesebb param, interpretálhatóbb |
| Loss | Focal Loss | Class imbalance (22% TP) |
| CV | Blocked time-series | Soha random! lookahead prevention |
| MLP szerepe | Diszkrepancia-jelző | Nem felülír LGBM-et, csak jelzi |
| S/R encoding | dist/ATR + above_below | Scale-free, NN érti |
| Trend encoding | {-1,0,+1} per szint | Egyszerű, interpretálható |

## Sorrend
1. ✅ Tanulmányozás (ez a dokumentum)
2. ⬜ RankGauss normalizáció implementáció
3. ⬜ S/R + Swing + Trend feature generálás
4. ⬜ Dataset + DataLoader
5. ⬜ MLP architektúra + Focal Loss
6. ⬜ Tanítás + Optuna
7. ⬜ Diszkrepancia rendszer
8. ⬜ Vizualizáció
