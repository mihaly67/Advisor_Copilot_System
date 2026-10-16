# Session: v10_v3_model_final
*Időbélyeg: 2026-10-09T23:35:28.240562*

V10 V3 MODELL KÉSZ

Pipeline: dollar_bars(42,742) → CUSUM(2,642 events) → TB(PT=0.75×ATR, SL=0.5×ATR, mb=6) → 37 features → LGBM

LONG modell (lgbm_long_v3.txt):
- 61 fa, lr=0.01, AUC_train=0.915, AUC_OOS=0.728
- Threshold: 0.45 → OOS ~14 trade, 60% Win, +0.42% PnL
- Confidence kalibrált: [0.45-0.50) = WIN, [0.30-0.45) = LOSE

SHORT modell (lgbm_short_v3.txt):
- 47 fa, lr=0.01, AUC_train=0.906, AUC_OOS=0.728
- Threshold: 0.40 → OOS ~6-19 trade, 83% Win, +0.37% PnL
- Confidence kalibrált: [0.40-0.45) = WIN, [0.30-0.40) = LOSE

Breakeven Win% = 49.6% (PT=$6.2, SL=$4.2, Cost=$1 → Net_Win=$5.2 = Net_Loss=$5.2)

Top features: vol_ratio_f, consecutive_f, ticks_inv_f, RSI_3_f, PastRet_2_f

NavSystem pivot-ek KELLETLEN gyengék (Near_Micro_R -4.2% Δ) — nem kerültek be

Key insight: A modell szelektivitásra tanul — kiszűr 85%+ eventet, csak high confidence esetén lép be