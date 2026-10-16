# Pipeline V9 — Microstructure Feature-ök (DOM nélkül)
*2026-09-23 20:15*

## Új feature-ök implementálva (AFML Ch.19 alapján)

8 microstructure feature **DOM nélkül**, csak OHLCV + tick adatból:

| Feature | Formula | Mit mér |
|---|---|---|
| **Roll_Spread** | 2√(-Cov(dP,dP_{t-1})) | Effective bid-ask spread |
| **Kyle_Lambda** | Σ|dP| / Σ√V | Price impact per volume |
| **Amihud_Illiq** | Σ|r| / ΣDV | Illikviditás |
| **Trade_Flow_Imb** | BVC: buy_vol-sell_vol/V | Vételi/eladási nyomás |
| **VPIN** | Σ|V_buy-V_sell| / ΣV | Informed trading valószínűség |
| **Run_Length** | Consecutive same-dir bars | Momentum persistence |
| **Micro_Price_Dist** | (Close-mid)/spread | Close vs weighted mid |
| **Kyle_Vol_Sync** | dP_bucket/√V_bucket | Volume-sync Kyle |

## Eredmény V9 vs korábbi verziók

| Verzió | Feature | Accuracy | Long R | Long P | Opposite |
|---|---|---|---|---|---|
| V1 (eredeti) | 48 | 40.3% | 17% | — | ~25% (Short dom) |
| V6 (agresszív) | 14 | 37.7% | 37% | 43% | 32.1% |
| V8 (momentum) | 19 | 39.0% | 43% | 50% | 31.0% |
| **V9 (microstructure)** | **23** | **40.2%** | **44%** | **51%** | **30.7%** |

## SHAP Top feature-ök

| Feature | SHAP_Long | SHAP_Short | SHAP_Total | Megjegyzés |
|---|---|---|---|---|
| ATR_Micro | 0.100 | 0.094 | 0.133 | #1 (volatilitás) |
| **Kyle_Lambda** | **0.032** | **0.031** | **0.038** | **#2! microstructure** |
| Pulse_DF_Curve | 0.040 | 0.016 | 0.034 | #3 |
| Stoch_D | 0.038 | 0.030 | 0.032 | #5 |
| **Micro_Price_Dist** | 0.024 | 0.016 | 0.028 | **#8 microstructure** |
| **VPIN** | 0.022 | 0.023 | 0.026 | **#11 microstructure** |
| **Run_Length** | 0.026 | 0.028 | 0.025 | **#11 momentum persist** |
| **Trade_Flow_Imb** | 0.023 | 0.016 | 0.024 | **#12 Long+ ✅** |

## Diszkrimináció (Cohen d)

| Feature | d | Megjegyzés |
|---|---|---|
| **Run_Length** | **+0.058** | LEGJOBB! Long=0.17, Short=0.06 |
| VPIN | -0.049 | VPIN magasabb Short-nál |
| Roll_Spread | -0.038 | |
| Kyle_Lambda | -0.038 | |
| Trade_Flow_Imb | -0.033 | Short-nál magasabb buy imbalance |

## Predikció eloszlás (Test set)
- Pred Long: 696 | Pred Short: 626 | Pred Noise: 678
- **Kiegyensúlyozott** — a modell nem Short-dominált

## Következő lépések
1. **Optuna 4D threshold calibration** — magasabb küszöb → kevesebb opposite
2. Run_Length > 2 szűrés → csak erős momentum belépés
3. VPIN > 0.5 szűrés → csak informed trading esetén
4. Long PT precision 51% már használható megfelelő position sizing-gel
