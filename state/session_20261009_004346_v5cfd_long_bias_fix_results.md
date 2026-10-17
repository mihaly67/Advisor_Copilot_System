# Session: v5cfd_long_bias_fix_results
*Időbélyeg: 2026-10-09T00:43:46.746811*

# V5 CFD Long-Bias Fix Eredmények (2026-10-09)

## Változtatások
1. **PT=SL=1.0 szimmetrikus Triple Barrier** (volt PT=1.5 SL=1.0)
2. **CUSUM_x_Bar interakció feature** = CUSUM_Direction × Bar_Direction
3. **scale_pos_weight=1.012** alkalmazva (volt class_weight=None)

## Tréning eredmények
- Label eloszlás: Long=5,887 (49.7%) Short=5,957 (50.3%) — kiegyensúlyozott!
- 17 feature (volt 16) — CUSUM_x_Bar hozzáadva
- CUSUM_x_Bar importance: **8.50%** (CUSUM_Direction csak 0.32%)
- OOS AUC = 0.498 (véletlen szint — fundamentális probléma)

## Live eredmények (BTC, ~2 perc)
| Metrika | Régi modell | Új modell |
|---------|------------|-----------|
| SHORT tradék | 3 | **7** |
| LONG tradék | 353 | **10** |
| ML:S predikciók | ~3 | **61** |
| ML:L predikciók | ~1680 | **81** |

## Modell scenárió tesztek
| Scenárió | P(Long) | Döntés | conf |
|----------|---------|--------|------|
| CUSUM UP + bearish | 0.446 | **SHORT** | 0.11 |
| CUSUM DN + bullish | 0.546 | **LONG** | 0.09 |
| CUSUM UP + bullish | 0.519 | LONG | 0.04 |
| CUSUM DN + bearish | 0.445 | **SHORT** | 0.11 |

## Hátralevő problémák
1. **OOS AUC≈0.50** — a feature-k nem prediktívek a 1-bar lookahead TB label-ekhez
2. **Confidence alacsony** (0.02-0.37) — NOISE_THRESHOLD=0.15 kiszűri a legtöbbet
3. **Momentum Long-bias** — Pulse_DF_Curve, Price_Velocity, RSI trend-követőek
4. **Vizsga Short WR=18.6%** — a vizsga időszak erős uptrend volt

## Következő lépések
1. **Csökkentsük NOISE_THRESHOLD** 0.15→0.08 hogy több tradé jöjjön
2. **Vizsgáljuk MAX_BARS** növelését (5→10) hogy a TB label-ek stabilabbak legyenek
3. **Meta-labeling** — CUSUM direction mint primary, ML mint secondary filter
4. **Momentum feature-k** RSI_overbought/oversold flag-ek hozzáadása
