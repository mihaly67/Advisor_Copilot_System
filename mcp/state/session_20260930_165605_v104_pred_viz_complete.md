# Session: v104_pred_viz_complete
*Időbélyeg: 2026-09-30T16:56:05.105779*

# v1.04 Predikciós Vizualizáció Kész — 2026.09.30

## FÁJLOK
- Script: /data/dev/projects/z-ai-copilot/src/viz_v104_pred.py
- HTML: /data/dev/projects/z-ai-copilot/docs/v104/viz_v104_pred.html (444 KB, CDN Plotly)
- Model: /data/dev/projects/z-ai-copilot/models/v104/lgbm_v104.pkl (42 feat)
- OOS: /data/dev/projects/z-ai-copilot/Master_csv/processed/labeled_oos_slope1.csv

## MEGOLDÁSOK (korábbi 7 próbálkozás problémáira)
1. **Candlestick** a 2152 egyedi Scatter vonal helyett → HTML 444 KB (volt 5.6 MB!)
2. **Threshold**: THL=0.50, THS=0.50, THN=0.50 → kiegyensúlyozott: L:807 S:944 N:401
3. **Színek konzisztensek**: Short=#B22222 (FireBrick/téklavörös), Long=#228B22 (ForestGreen/erdőzöld)
4. **2 panel** (volt 3): Panel 1=Candlestick+háromszögek, Panel 2=Valószínűség+Threshold vonalak

## LAYOUT
- Panel 1 (55%): OHLC Candlestick + ▲ Long (erdőzöld) + ▼ Short (téklavörös) + ● Noise (szürke)
- Panel 2 (45%): P(Long)/P(Short)/P(Noise) görbék + THL/THS/THN dashed vonalak

## EREDMÉNY (3 nap, 2152 bars)
- Pred: Long:807 Short:944 Noise:401
- Accuracy: 62.4%
- THL=0.50 THS=0.50 THN=0.50

## VERIFIKÁCIÓ
- Candlestick trace: ✓
- triangle-up (Long ▲): ✓
- triangle-down (Short ▼): ✓
- THL/THS/THN vonalak: ✓
- Dark theme (#111111/#000000): ✓
- #228B22 (ForestGreen) és #B22222 (FireBrick): ✓