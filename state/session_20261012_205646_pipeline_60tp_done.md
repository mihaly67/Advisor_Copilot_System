# Session: pipeline_60tp_done
*Időbélyeg: 2026-10-12T20:56:46.890347*

$60 TP PIPELINE KÉSZ — feature + tréning + viz

Config: SIMPLE_TP_DIST=60, SIMPLE_TP_MAX_BARS=10, $1.04M threshold, 3 bar/min

Tréning eredmények (test, 37 feature, look-ahead bias javítva):
  Long:  AUC=0.6506  WR@0.5=76.7% (150 pred)  CV AUC=0.680
  Short: AUC=0.6385  WR@0.5=65.3% (452 pred)
  EMA:   AUC=0.6385  WR@0.5=75.0% (4 pred)

Vizualizációk:
  viz_signals_*.html — dollár bar címkék (▲LONG ▼SHORT) — template
  viz_pred_*.html — P(Long) zöld + P(Short) piros görbék + küszöb vonalak — template

  Felső panel: OHLC candles + ▲ Long sig + ▼ Short sig
  Alsó panel: P(Long) zöld vonal, P(Short) piros vonal, küszöb=0.45 arany, 0.5 szürke

Scripts:
  viz/viz_signals_1day.py --date YYYY-MM-DD  (címkék)
  viz/viz_pred_1day.py --date YYYY-MM-DD --thr 0.45  (predikciók)

Fájlok:
  models/lgbm_simple_tp_{long,short,ema}.txt
  models/features_simple_tp.txt (37 feature)
  models/results_simple_tp.json