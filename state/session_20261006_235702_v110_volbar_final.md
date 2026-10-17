# Session: v110_volbar_final
*Időbélyeg: 2026-10-06T23:57:02.259907*

V110 VOLBAR PIPELINE KESZ!

Paraméterek:
- Bar: Volatility bar, ATR_target=$3.0 (kumulatív |Δprice| ≥ $3.0)
- CSV: Scalper_Copilot_MTF_Data_v2.csv (tanito, CFD), Scalper_Copilot_MTF_Data_külön_vizsga.csv (vizsga, CFD)
- Triple Barrier: PT=$1.5, SL=$1.0, max_bars=8
- Threshold (optimized): THL=0.384, THS=0.501, THN=0.202
- Features: 18 feat with shift(1) leakfix

ATR sweep results:
  $1.5: OOS=41.4% Viz=41.1%
  $2.0: OOS=44.1% Viz=43.4%
  $3.0: OOS=46.4% Viz=49.0% ← BEST
  $5.0: OOS=45.7% Viz=43.4%
  $8.0: OOS=44.3% Viz=42.6%

Final results (with optimized threshold):
  OOS: WR=50.8% P=$616.5 T=2281
  Vizsga: WR=51.7% P=$241.5 T=826
  Gap: -0.9% → STABIL

Previous (wrong) results were INVALID (used futures CSV, not CFD).
This is the first correct CFD pipeline with volatility bars.

Files:
- Pipeline: /data/dev/projects/z-ai-copilot/src/v110_volbar_pipeline.py
- Optimize: /data/dev/projects/z-ai-copilot/src/v110_volbar_optimize.py
- Model: /data/dev/projects/z-ai-copilot/models/v110_volbar/lgbm_18feat_volbar_opt.pkl
- Results: /data/dev/projects/z-ai-copilot/docs/v110_volbar/volbar_opt_results.json
- Viz: /data/dev/projects/z-ai-copilot/docs/v110_volbar/viz_*.html