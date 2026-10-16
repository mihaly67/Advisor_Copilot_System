# Session: vizualizacio_modszer_20260924
*Időbélyeg: 2026-09-24T02:07:16.838851*

# Vizualizációs módszer rögzítve — 2026-09-24

## VIZUALIZÁCIÓ FORMÁTUM (predictions_visualization.html mintára)
- Script: `/data/dev/projects/z-ai-copilot/src/visualize_v2.py`
- 3-panel Plotly, sötét theme (#111111 bg, #000000 paper, fehér font)
- Panel 1: Ár (OHLC vonalak) + Actual/Prediktált Long/Short/Noise jelzések
  - Actual Long: sötétzöld triangle-up, opacity 0.35
  - Actual Short: sötétvörös triangle-down, opacity 0.35
  - Pred Long: világoszöld triangle-up, confidence-alapú méret
  - Pred Short: magenta triangle-down, confidence-alapú méret
  - Pred Noise: szürke circle, size 4, opacity 0.25
- Panel 2: P(Long)/P(Short)/P(Noise) idősor + threshold vonalak
- Panel 3: Actual Label vs Predicted Label scatter
- Entry: következő bar Open (anti-lookahead)
- Csak OOS test set (utolsó 20%), utolsó 2000 bar

## HASZNÁLAT
```
python3 src/visualize_v2.py --version v5           # Long+Short
python3 src/visualize_v2.py --version v5 --short_zero  # Long-only
```
Output: `/data/dev/projects/z-ai-copilot/docs/viz_v{X}.html`

## VERZIÓK MOST
- viz_v1.html: 82 feature, Long+Short (653 Long, 19 Short)
- viz_v5.html: 8 feature, Long+Short (491 Long, 58 Short)
- version_comparison.html: 7 verzió cumulative profit curve

## MÓDSZER RÖGZÍTVE
- .clinerules/ml-python.md kiegészítve a verzió-kezelési szabályokkal
- train_lgbm_v2.py + shap_prune.py + visualize_v2.py = teljes pipeline
- Minden verzió mentve, soha nincs felülírás