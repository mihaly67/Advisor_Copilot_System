# Session: optuna_v110_complete
*Időbélyeg: 2026-10-04T21:13:46.320862*

OPTUNA V1.10 JULES CFD COMPLETE. 4 configs compared: Original(47.7%/2331), Profit-opt(47.5%/11336), WR-opt(61%/200), Balanced(59.3%/273). KEY: Short WR>Long WR (64.7% vs 52.8% on Balanced). Stoch deadzone 0.29-0.38 is the most important new parameter. Asymmetric Stoch kill (-0.25/0.27). THL>THS. CONFUSION MATRIX BUG FIXED (encoding mismatch 0/1/2 vs -1/0/1). Root cause: CFD tick-count volume has no directional info vs futures TICK_FLAG_BUY/SELL.