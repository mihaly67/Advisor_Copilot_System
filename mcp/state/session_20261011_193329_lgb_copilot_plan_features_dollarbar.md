# Session: lgb_copilot_plan_features_dollarbar
*Időbélyeg: 2026-10-11T19:33:29.266712*

LGB Copilot BTCUSD — Feature és Dollár Bar Terv

## 1. DOLLÁR BAR MÉRET
- Auto threshold: sweep + fine-tune, target ~700 bar/nap (XAUUSD tempo match)
- BTCUSD: $165K/bar (gen_dollar_bars_instrument.py már megcsinálja)
- Online nem kell dollár bar — EA M1 tick-eket küld

## 2. FEATURE PIPELINE — EGYETLEN MODUL (offline = online)
- Bemenet: OHLCV + ATR_M15 + RSI_M15 + S/R szintek (Scalper EA küldi / CSV-ből)
- NINCS RankGauss, NINCS clip, NINCS MLP ensemble
- LGBM fa → nem kell Gauss transzformáció!

## 3. FEATURE LISTA
### Meglévő (jó): body_sign, body_ratio, wick_u_r/l_r, PastRet_1/2, consecutive, above_ema8/20, ema8_gap, ema_fast_slow, RSI_3/5, Slope_3/5, vol_ratio, vol_calm, Bullish_Bar, Conviction_Bar, delta_sr_zone_sec/micro, round_10_dist, trend_micro, sw_high/low_dist
### Bővítendő: above_ema50, rsi_m15_cent, rsi_oversold/overbought, slope/body/velocity_atr, trend_strength, price_percentile, mom_persistence, vol_surge, macd_bullish, bar_direction (TB side!), delta_sr_zone_ter, above_micro_r, above_sec_r

## 4. TRIPLE BARRIER
- Side-aware: side=+1 (Long) → TP fent, SL lent; side=-1 (Short) → TP lent, SL fent
- Side forrás: dollár bar direction (Close > Open = +1, Close < Open = -1)
- KÉT LGBM: lgbm_long + lgbm_short

## 5. ADATOK
- M1_History_BTCUSD.csv: 1.38M M1 OHLCV (2024.01.03-tól)
- Scalper_Copilot_MTF_Data_v2_BTCUSD.csv: 5.23M tick (ATR, RSI, S/R)
- BTCUSD_külön_vizsga.csv: OOS (2026.10.05-től, Scalper formátum)
