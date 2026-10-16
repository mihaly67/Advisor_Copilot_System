# Session: jules_cfd_correct_db_ohlc_results
*Időbélyeg: 2026-10-07T19:41:45.060678*

Jules CFD CORRECT Pipeline Results — 2026-10-07

KULCS FELISMERES: A features_dollar_bars.csv Stoch_K es Wick_ATR M1 gyertyan szamitottak!
- Stoch_K: correlation 0.82 dollár bar Stoch-szal
- Wick_ATR: correlation 0.02 (!!!) a dollar bar wick-el

HELYES pipeline: jules_cfd_correct.py
- Minden feature DOLLAR BAR OHLC-n szamitva
- Stoch window=14 smooth=3 on dollar bar OHLC
- Wick on dollar bar OHLC
- ATR on dollar bar OHLC

EREDMENYEK:
| Metrika | M1 feature (elozo) | Dollar Bar OHLC (HELYES) |
|---------|--------------------|---------------------------|
| OOS WR  | 41.2%              | 51.1% (+9.9%)             |
| Vizsga  | 39.4%              | 46.6% (+7.2%)             |
| Swap%   | 52.3%              | 42.5% (-9.8%)             |

Feature importance MEGVALTOZOTT:
- M1: Dist_* dominalt (60%+)
- Dollar Bar OHLC: Wick + Tick_Speed + Stoch dominál (85%+), Dist_* = 0%!

PROBLEMA: Túl kevés trade (45 OOS, 118 vizsga) - stability filter túl szigorú

FILES:
- Script: /data/dev/projects/z-ai-copilot/src/jules_cfd_correct.py
- Model: /data/dev/projects/z-ai-copilot/models/jules_cfd/lgbm_jules_cfd_correct.pkl
- Results: /data/dev/projects/z-ai-copilot/docs/jules_cfd/jules_cfd_correct_results.json