# Session: copilot_pipeline_done
*Időbélyeg: 2026-10-12T21:11:55.092006*

COPILOT PIPELINE KÉSZ — folyamatos P(Long)/P(Short) minden dollár bar-ra

Config: SIMPLE_TP_DIST=$30, SIMPLE_TP_MAX_BARS=10, threshold=$1.04M (3 bar/min)
Címkézés: $30 TP, első érkezés logika (melyik irány hamarabb)
  Long TP: 48.2%  Short TP: 48.6%  Combo: 40.8% L / 40.6% S / 18.5% timeout

Tréning (37 feature, 50/50 label):
  Long:  AUC=0.616  WR@0.5=57.0%  WR@0.55=61.0%  WR@0.65=73.6%
  Short: AUC=0.612  WR@0.5=54.9%  WR@0.55=56.7%  WR@0.70=67.2%
  EMA:   AUC=0.602  WR@0.5=57.6%  WR@0.65=74.8%
  CV AUC: 0.644 ± 0.021

Folyamatos copilot: minden dollár bar-ra P(Long) és P(Short)
  @0.4 küszöb: ~48K jelzés/50K bar = szinte minden bar-ra van predikció
  @0.5 küszöb: ~34K/50K
  @0.55 küszöb: ~19K/50K

Vizualizációk:
  viz_pred_*.html — P(Long) zöld + P(Short) piros görbék + küszöb
  viz_signals_*.html — dollár bar címkék ▲LONG ▼SHORT