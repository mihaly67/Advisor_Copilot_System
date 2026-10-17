# Session: model_capabilities_full_20260924
*Időbélyeg: 2026-09-24T13:30:20.990167*

XAUUSD LightGBM Copilot teljes modell képesség-leírás és statisztikák.

LEGJOBB MODELL: V5 (Long-only, 8 feature, +$2611 profit, 47.8% win, 16.8% opp)
FEATURE: Regime_ADX, Regime_Trending, ATR_Micro, Trend_EMA_Slow_Dist, Dist_Sec_R_ATR, Kyle_Lambda, Micro_RSI_14, Dist_Sec_S_ATR

META-LABELING: meta_v1 (30 feat, AUC=0.533) — NEM segít, profit < baseline
KELLY: 0.25x th=0.45 → 7x profit javulás flat-hez képest

PIPELINE V2 EVOLÚCIÓ: v0(31f,+$386) → v1(82f,+$2414) → v5(8f,+$2611)
SHORT PROBLÉMA: körkörös labeling (ADX<20→Short), 70.8% opposite, meta-labeling nem segít

ADAT: 31,139 Dollar Bar ($444K), 114 feature, Train 24,911 / Test 6,228
GPU: P4000 (compute) + P2000 (display), NVIDIA 580.178.04

KÖVETKEZŐ: Éles prediktor (live_predictor.py + ZMQ), folyamatos P(trade) kimenet