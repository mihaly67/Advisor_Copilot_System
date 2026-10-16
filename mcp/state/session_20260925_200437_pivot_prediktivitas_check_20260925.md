# Session: pivot_prediktivitas_check_20260925
*Időbélyeg: 2026-09-25T20:04:37.860011*

# PIVOT PREDIKTIVITÁS — KÉTSÉGEK (2026.09.25.)

## Korrelációk a V8 CSV-n (31,139 bar):
### Breakout (|fwd_ret_5|) vs pivot:
- Dist_Micro_R_ATR: corr=-0.1024 (legjobb, de gyenge)
- Dist_Micro_S_ATR: corr=+0.0708
- Wick_Lower_ATR: corr=+0.0891

### Direction (fwd_ret_5 signed):
- Minden pivot feature: corr ~0.003-0.005 (NULLA)
- Minden NavSystem momentum: corr ~0.005-0.012 (NULLA)

### Side prediction accuracy:
- Pivot-based: 49.6% (baseline=50%)
- Slope-based: 49.8% (baseline=50%)

## KÖVETKEZTETÉS:
SEMMI sem prediktív a V8 adaton. Nem csak a Slope_Close_14 halott —
a pivot távolságok ÉS a NavSystem momentum feature-ök is.
Az OOS WR=51.5% nem a modell hibája, hanem a feature-öké.
