# Session: direction_features_study_complete
*Időbélyeg: 2026-10-06T00:19:54.800359*

IRANY FEATURE-K STUDY KÉSZ (49s)

EREDMÉNYEK:
  A_10feat (baseline):  WR=54.0% P=$2,844 T=8,138  Opp=2,206 (33.4%)
  B_18feat (+8 dir):    WR=56.0% P=$3,181 T=7,934  Opp=2,144 (32.5%)

JAVULÁS: +2.0% WR, +$336 profit, -62 opposite swap, -0.9% swap%

8 ÚJ IRANY FEATURE (és feature_importance rank a 18feat modellben):
  1. RSI_M15_signed  → #1 (7.97%) ← LEGFONTOSABB ÚJ!
  2. MACD_Hist_ATR   → #8 (5.76%)
  3. RSI_signed       → #10 (5.29%)
  4. ROC_5            → #11 (5.22%)
  5. BB_ZScore        → #12 (4.64%)
  6. MFI_signed       → #13 (4.45%)
  7. OBI_ZScore       → #14 (4.43%)
  8. Price_Vel_ATR    → #15 (4.12%)

KULCS FELISMERÉS: RSI_M15_signed a #1 feature az 18feat modellben!
  - Ez a M15 RSI előjel-alakja: (RSI_M15 - 50) / 50
  - M15 = 15 perces timeframe trend irány → LONG-TERM KONTEXTUS

SWAP CSÖKKENÉS: 2,206 → 2,144 (-62, -0.9%)
  - A P(L)-P(S) gap nőtt swap-kor: 0.020 → 0.028
  - A modell magabiztosabb az irány feature-kekkel

KIMENET:
  Script: /data/dev/projects/z-ai-copilot/src/direction_features_study.py
  Viz: /data/dev/projects/z-ai-copilot/docs/v110_direction/
  Models: /data/dev/projects/z-ai-copilot/models/v110_direction/