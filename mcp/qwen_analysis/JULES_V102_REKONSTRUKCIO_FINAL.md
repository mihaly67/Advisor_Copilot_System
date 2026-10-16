# Jules v1.02 Rekonstrukció — Teljes Dokumentáció

## Dátum: 2026.09.26.

## 1. Gyökérok azonosítása
- Z.ai `dom_labeler_v5.py` aszimmetrikus PT/SL: PT_Long=1.2$ vs PT_Short=1.8$
- ADX≥20 regime filter blokkolta 59.6%-ot a Short predikcióknak
- Eredmény: 91.7% Long-bias, 82% Noise label
- SHAP bizonyította: Regime_ADX 10x dominancia (label leakage)

## 2. MQL5 forrás megkutatva
- `AI_Labeled_Data_Exporter_v8.1.mq5` pontos paraméterek:
  - PT=1.5×ATR (nem 2.0)
  - SL=1.0×ATR
  - max_bars=15 (nem 5)
  - A Python script rossz paraméterekkel dolgozott!

## 3. jules_labeler.py létrehozva
- Side: Slope_Close_14 > 0 → Long(+1), < 0 → Short(-1)
- Target_Meta: szimmetrikus triple barrier (PT=1.5×ATR, SL=1.0×ATR, 15 bar)
- 3-class label: Target_Meta=1 & Side=1→Long, Target_Meta=1 & Side=-1→Short, else→Noise
- Label eloszlás: Long=19.1% Short=21.2% Noise=59.8% (SZIMMETRIKUS!)

## 4. train_jules_v102.py létrehozva
- 15 NavSystem feature (FEATURES_V5)
- class_weight: {0:1.0, 1:noise_w, 2:1.0} — Short=Long egyenlő
- noise_weight sweep: 0.8→54.1%, **0.7→52.1%** (best), 0.6→49.0%, 0.5→46.5%
- Szimmetrikus profit: LW=+2.0, LL=-1.0, SW=+2.0, SL=-1.0
- Thresholds: th_long=0.35, th_short=0.50, th_noise=0.60

## 5. Eredmények
| Metrika | Test | OOS | Külön Vizsga |
|---|---|---|---|
| Accuracy | 51.7% | 52.1% | 53.4% |
| Pred Long | - | 17.4% | 18.1% |
| Pred Short | - | 21.5% | 21.5% |
| Pred Noise | - | 61.1% | 60.4% |

## 6. Vizualizáció (viz_jules_v102.py)
- 3-panel Plotly (sötét theme, 1600×1200)
- Panel 1: Candlestick + Actual/Pred Long/Short/Noise markers (confidence-based size)
- Panel 2: P(Long/Short/Noise) + threshold vonalak
- Panel 3: Actual Label vs Predicted
- HTML: viz_jules_v102.html, viz_jules_v102_oos.html, viz_jules_v102_kulon_vizsga.html

## 7. SHAP Analízis (shap_analyze_oos.py)
- Top 3: Slope_Close_14(1.95), MomScore_14(0.44), Mom10_Direction(0.18)
- NINCS Regime feature leakage (0 Regime a 15-ben)
- Slope_Close_14 szimmetrikus: Short=2.97, Long=2.86
- Output: shap_beeswarm_3class.png, shap_bar_3class.png, shap_stacked_top15.png

## 8. Leakage Audit
- Feature lookahead: NINCS (minden feature .shift(1) a dom_feature_engineer_mtf.py-ben)
- Slope_Close_14 vs Close[i] corr = -0.002 (nem látja jelenlegi bar Close-át)
- Label lookahead: VAN by design (Target_Meta 15 bar — triple barrier, OK)
- Pivot leakage: NINCS jules_v102-ben (0 pivot feature). DE: Micro_R corr(High)=0.9995 a CSV-ben
- Entry price: close[i] nem open[i+1] (kisebb bias, nem leakage)
- Robustness: Shuffled label Acc=44.2% (nincs leakage), Time-shifted Acc=49.7% (stabil)
- **KONKLÚZIÓ: NINCS adatszivárgás, 52.1% OOS accuracy valós**

## 9. Külön Vizsga CSV (run_kulon_vizsga.py)
- Forrás: Scalper_Copilot_MTF_Data_külön_vizsga.csv (386K sor raw MTF)
- Pipeline: dollar bars(4,063) → features(2,952) → jules label → model eval
- Accuracy: 53.4% (OOS-nál jobb!)
- Label: Long=599(20.3%) Short=544(18.4%) Noise=1809(61.3%)

---

## KÖVETKEZŐ TASK: Pivot távolságok hozzáadása

### Cél
Dist_Micro_R_ATR, Dist_Sec_R_ATR, Dist_Ter_R_ATR, Dist_Micro_S_ATR, Dist_Sec_S_ATR, Dist_Ter_S_ATR (6 feature) hozzáadása a FEATURES_V5-höz jövőbelátás nélkül.

### Miért biztonságos?
- A dom_feature_engineer_mtf.py minden feature-re .shift(1) van alkalmazva
- A Dist_*_ATR feature-ök is shift(1)-elve vannak (95. sor: `...shift(1)`)
- A nyers Micro_R/S értékek NEM biztonságosak (corr(High)=0.9995) — SOHA ne add hozzá

### Lépések
1. features_v5.py: FEATURES_V5 += 6 Dist_*_ATR (+ wick/breakout flag-ek opcionálisan)
2. train_jules_v102.py: újra betanítás (21+ feature)
3. shap_analyze_oos.py: SHAP az új modellre → ha pivot feature bejön top-ban → siker
4. run_kulon_vizsga.py: külön vizsga újra
5. viz_jules_v102.py: vizualizáció
6. Ha pivot feature-ök bejönnek SHAP top-ban → Jules terv megvalósult

### Fájlok
- /data/dev/projects/z-ai-copilot/src/features_v5.py
- /data/dev/projects/z-ai-copilot/src/train_jules_v102.py
- /data/dev/projects/z-ai-copilot/src/shap_analyze_oos.py
- /data/dev/projects/z-ai-copilot/src/run_kulon_vizsga.py
- /data/dev/projects/z-ai-copilot/src/viz_jules_v102.py

### Python venv
/home/Jules/jules_venv/bin/python3

### Base path
/data/dev/projects/z-ai-copilot
