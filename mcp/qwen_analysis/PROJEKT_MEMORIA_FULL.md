# XAUUSD LightGBM Copilot — Részletes Projekt Memória

## Utolsó frissítés: 2026.09.24.

---

## 1. PROJEKT CÉL

XAUUSD (arany) scalping copilot LightGBM modellel. A modell **nem robot** — manuális kereskedőnek ad predikciót és ajánlást. A kereskedő figyeli a chartot és a modell javaslata alapján dönt.

**Követelmény:**
- Folyamatos predikció minden bar-on (nem csak trade jeleknél)
- Külön jelölve az **ajánlott belépés** (P(trade) > küszöb)
- Kelly-based pozícióméret ajánlás
- Napi ~90 trade lehetőség (60 kevés volt)

---

## 2. TECH STACK

- **Python 3.11** (jules_venv: `/home/Jules/jules_venv/bin/python3`)
- **LightGBM** (GPU: P4000, `device='gpu'`)
- **pandas, numpy, scikit-learn, shap, scipy**
- **MetaTrader5** (adatgyűjtés)
- **MQL5** (EA: ZMQ publisher)

---

## 3. KÖNYVTÁR STRUKTÚRA

```
/data/dev/projects/z-ai-copilot/
├── src/
│   ├── prado_dollar_bars.py      — Dollar bar képző ($444K alap threshold)
│   ├── dom_feature_engineer_mtf.py — Feature engineering (114 feature)
│   ├── dom_labeler_v6.py          — Triple barrier labeling (Long/Short/Noise)
│   ├── dom_labeler_v7.py          — Binary labeling (Long/Short)
│   ├── dom_labeler_v8.py          — Meta-labeling (Primary: Slope_Close_14 → side, Secondary: trade/pass)
│   ├── train_lgbm_v2.py          — Multiclass trainer (3 osztály)
│   ├── train_lgbm_meta.py         — Binary meta-labeling trainer
│   └── kelly_sizing_eval.py      — Kelly position sizing értékelő
├── Master_csv/
│   ├── raw/Scalper_Copilot_MTF_Data.csv — 4.2M tick snapshot (18 oszlop)
│   └── processed/
│       ├── dollar_bars_adaptive.csv      — $444K threshold (43,508 bar)
│       ├── dollar_bars_thr222k.csv       — $222K threshold (87,016 bar)
│       ├── features_dollar_bars_adaptive.csv — 114 feature ($444K)
│       ├── features_thr222k.csv          — 114 feature ($222K)
│       ├── labeled_dollar_bars_v6.csv   — V6 triple barrier ($444K)
│       ├── labeled_dollar_bars_v7.csv   — V7 binary ($444K)
│       └── labeled_dollar_bars_v8.csv   — V8 meta-labeling ($444K)
├── models/
│   ├── v10/ — 82 feature, V6 labeling
│   ├── v11/ — 20 feature
│   ├── v12/ — 10 feature
│   ├── v13/ — 100 feature (+18 irány-specifikus)
│   ├── v14/ — 100 feature, V7 binary (Accuracy 49.6% — random)
│   ├── v15/ — (félkész)
│   ├── v16/ — 114 feature, V7 binary
│   ├── v17/ — 114 feature, V6 labeling (Slope_Close_14 top 10!)
│   ├── v18/ — 30 feature, V6 labeling (Win 45.4%, Opp 44.9%)
│   ├── meta_v1/ — 30 feature, V8 meta-labeling ($444K) ← LEGJOBB
│   ├── meta_v2/ — 114 feature, V8 meta-labeling
│   └── meta_v3_222k/ — 30 feature, V8 meta-labeling ($222K) — rosszabb
└── /data/Brain/_qwen_analysis/
    ├── SHORT_DIAGNOSTIKA_V5_GYOKEROK.md
    ├── RAG_IRANY_MEGOLDAS.md
    └── RAG_KOCKAZATKEZELES_TRADE_SZAM.md
```

---

## 4. MODELL TÖRTÉNET ÉS EREDMÉNYEK

### V10-V12 (82→20→10 feature, V6 labeling)
- Short recall 0%→82% de opposite 42% maradt
- Modell nem tud megkülönböztetni Long vs Short irányt

### V13 (100 feature, +18 irány-specifikus)
- Bar_Direction, Price_Vel_Signed, Wick_Asymmetry stb.
- SHAP: irány-feature-ök alacsonyak (0.03-0.05)
- Opposite 42% maradt

### V14 (V7 binary labeling, 100 feature)
- Accuracy 49.62% — gyakorlatilag random (50/50)
- SHAP_Long=0.0 minden feature-nél — modell csak Short-ot mond

### V17 (V6 labeling, 114 feature, +18 nyers return)
- **Slope_Close_14 bekerült top 10-be** (SHAP=0.057)
- PastLogRet_1 első irány-diszkrimináló (L_minus_S=-0.009)
- Opposite 43.5%

### V18 (30 feature, V6 labeling)
- Win 45.4%, Opposite 44.9%, Profit $1432
- 30 feature pruning nem hozott áttörést

### META_V1 (30 feature, V8 meta-labeling, $444K) ← LEGJOBB
- **AUC: 0.533**
- Accuracy: 51.85%
- Primary: Slope_Close_14 > 0 → Long, < 0 → Short
- Secondary: bináris trade(1)/pass(0)

### META_V3 ($222K threshold) — rosszabb
- AUC: 0.523 (0.533→0.523)
- Kisebb barok = több zaj

---

## 5. KELLY POSITION SIZING EREDMÉNYEK (meta_v1, $444K)

### P(trade) distribution:
- 10th percentile: 0.428
- 25th percentile: 0.464
- 50th percentile: 0.500
- 75th percentile: 0.542
- 90th percentile: 0.599
→ Modell probabilities nagyon közel 0.5-höz (szűk tartomány)

### Módszer összehasonlítás:

| Módszer | Trades | Win% | Profit | Sharpe | MaxDD | AvgSize |
|---------|--------|------|--------|--------|-------|---------|
| FLAT 1% | 6168 | 50.8% | 32.4 | 5.55 | 0.25 | 1.0% |
| FLAT 2% | 6168 | 50.8% | 64.7 | 5.55 | 0.50 | 2.0% |
| **Kelly 0.25x** | **6168** | 50.8% | **230.5** | 5.45 | 1.48 | 6.6% |
| Kelly 0.50x | 6168 | 50.8% | 461.0 | 5.45 | 2.96 | 13.2% |
| Confidence | 6168 | 50.8% | 36.1 | 5.52 | 0.24 | 1.1% |
| Kelly+Conf | 6168 | 50.8% | 215.8 | 5.35 | 1.44 | 6.2% |
| **Kelly 0.25x th0.45** | **5104** | **51.5%** | **216.0** | **5.75** | 1.45 | 7.3% |
| **Kelly 0.25x th0.50** | **3133** | **52.6%** | **162.8** | **6.18** | 1.03 | 8.5% |
| Kelly+Conf th0.45 | 5104 | 51.5% | 208.6 | 5.76 | 1.46 | 7.2% |

### Long/Short:
- Long: 3119 trades, 1587 wins (50.9%), profit=108.15
- Short: 3049 trades, 1548 wins (50.8%), profit=122.33
- Szimmetrikus — nincs aszimmetria

### Legjobb ajánlás: **Kelly 0.25x th=0.45**
- ~90 trade/nap, Win 51.5%, Sharpe 5.75
- Pozícióméret: Kelly alapú, átlag 7.3% (capped 5%)

---

## 6. GYŐKÉROKOK ÉS FELISMERÉSEK

### 6.1. Circular labeling (megoldva)
- V5: ADX<20 → Short címke, de ADX feature is használatban → circular
- V6: regime filter KI, szimmetrikus PT (1.2$/1.2$)
- Eredmény: Short 14.6%→43.1%, circularity broken (ADX<20: 100%→39.4%)

### 6.2. ATR normalizálás megöli az irány-szignált (megoldva)
- Bar_Direction = (close-open) / ATR → ATR-normalizált
- Magas ATR → kicsi érték nagy mozgásnál; alacsony ATR → nagy érték kis mozgásnál
- Megoldás: nyers signed returns (PastRet_1-10, PastLogRet_1-10, Slope_Close_14, MomScore_14)
- Eredmény: Slope_Close_14 bekerült top 10 SHAP-ba

### 6.3. WPR nem működik dollar bar-okon (bizonyított)
- Cohen's d ≈ 0.03 — nem diszkriminál
- Dollar bar aggregáció (nem időalapú) megtöri az overbought/oversold logikát

### 6.4. ATR_Micro dominálja a SHAP-ot (#1 minden verzióban)
- SHAP_Noise=0.234 — Noise-specifikus, nem irány-specifikus
- A modell megtanulta: "nagy volatilitás = Noise"
- Nem fáradozik az irányon

### 6.5. Dollar bar threshold $222K rosszabb
- Több bar = több zaj
- AUC 0.533→0.523, Win 50.8%→47.6%
- $444K marad az eredeti threshold

---

## 7. RAG KUTATÁS EREDMÉNYEK

### 7.1. LGBM-Stock-Prediction-main (score 0.61)
- Nyers signed returns (past_return_1-10, past_log_return_1-10) ATR nélkül
- momentum_score = regresszió slope × R² (annualizált)
- slope of close/ema/high/low (14-bar rolling)

### 7.2. mlfinlab meta-labeling (score 0.64)
- get_events(): pt_sl array, target=volatility
- get_bins(): side_predictionnel → bináris 0/1 (trade/no-trade)
- Case 1 (nincs side): bin in (-1,1) = irány
- Case 2 (side megadva): bin in (0,1) = meta-label

### 7.3. XAUUSD Scalping AI (score 0.64) — közvetlen XAUUSD!
- Aszimmetrikus pozícióméret: Long 2%, Short 0.02% (100x különbség)
- Aszimmetrikus TP/SL: Long TP=1000pt SL=400pt, Short TP=10pt SL=20pt
- Win rate: Short 70%+, Long 60%+
- Session: London/NYC (mi is 08:00-23:59)
- Meta-model: entry_clf + lstm + transformer + xgb → meta.joblib

### 7.4. DART Risk Management (score 0.64)
- Kelly: f* = (p·b - q) / b
- Fractional Kelly (0.5-0.75x)
- Volatility-adjusted: Size = (Account × Risk%) / (ATR × Multiplier)
- Drawdown limit 15%

### 7.5. Tensortrade "Path to Profitability" (score 0.48)
- Reduce frequency 10x
- Position sizing binary BSH helyett
- Confidence threshold

### 7.6. Kalshi Edge Filter (score 0.46)
- Edge = AI_prob - market_prob
- Min edge 8%, min confidence 50%

---

## 8. KÖVETKEZŐ LÉPÉSEK

### 8.1. Folyamatos predikció implementálása (KÖVETKEZŐ TASK)
A felhasználó kérése: **folyamatos predikció minden bar-on**, külön jelölve az ajánlottat.

Tervezett kimenet (JSON vagy konzol):
```json
{
  "timestamp": "2026-09-24 15:30:00",
  "bar_info": {
    "close": 2650.5,
    "atr_micro": 3.2,
    "slope_close_14": 0.15
  },
  "prediction": {
    "p_trade": 0.52,           // mindig jelen van
    "p_pass": 0.48,            // mindig jelen van
    "side": "LONG",            // primary modell (Slope_Close_14)
    "kelly_size": 0.066,       // Kelly 0.25x fraction
    "recommended": false       // csak ha P > 0.45
  },
  "recommendation": {
    "action": "WAIT",          // vagy TRADE
    "direction": "LONG",
    "position_size_pct": 5.0, // capped Kelly
    "confidence": "MEDIUM"     // LOW/MEDIUM/HIGH
  }
}
```

### 8.2. Éles prediktor (MT5 + ZMQ)
- MT5 EA küldi a tick/bar adatot ZMQ-n
- Python fogadja → feature számolás → modell predikció → kimenet
- Vizuális: konzol vagy lightweight chart overlay

### 8.3. Modell javítás lehetőségei
- Erősebb primary modell (multi-signal: EMA crossover + ADX + slope)
- Ensemble (XAUUSD repo minta: lgbm + xgb + meta)
- Calibrated probabilities (platt scaling) — P(trade) tartomány szűk
- Fixed-horizon labeling alternatíva (return > threshold at bar N)

---

## 9. FONTOS FÁJLOK

### Train scriptek:
- `src/train_lgbm_v2.py` — multiclass (Target_Label -1/0/+1 → 0/1/2)
- `src/train_lgbm_meta.py` — binary meta (Target_Meta 0/1)
- `src/kelly_sizing_eval.py` — Kelly sizing értékelő

### Labelerek:
- `src/dom_labeler_v6.py` — triple barrier (PT/SL/vertical)
- `src/dom_labeler_v7.py` — binary fixed-horizon
- `src/dom_labeler_v8.py` — meta-labeling (primary slope → side, secondary trade/pass)

### Adat:
- Bemenet: `Master_csv/raw/Scalper_Copilot_MTF_Data.csv` (4.2M sor, 18 oszlop)
- Dollar bar: `dollar_bars_adaptive.csv` ($444K, 43,508 bar, ~546/nap)
- Feature: `features_dollar_bars_adaptive.csv` (114 feature, 31,147 sor)

### Modell (legjobb):
- `models/meta_v1/model.pkl` — 30 feature, V8 meta-labeling, AUC=0.533
- `models/meta_v1/features.txt` — 30 feature lista
- `models/v17/features_top30.txt` — top 30 feature (kézzel curált)

### Kelly formula:
```
Kelly = (P × 2.0 - (1-P)) / 2.0 × 0.25
Pénz = Tőke × Kelly_fraction × capped(5%)
```

---

## 10. KÖRNYEZET

- **OS**: MX Linux
- **CPU**: Xeon 20/60
- **GPU**: P4000 (Pascal, LightGBM GPU), P2000 (Qwen MCP)
- **RAM**: 32GB
- **Python**: 3.11 (jules_venv)
- **LightGBM**: GPU mode (`device='gpu', gpu_platform_id=0, gpu_device_id=0`)
- **MT5**: IC Markets XAUUSD CFD, no real volume (tick-count proxy)

### GRUB/Kernel figyelmeztetés:
NVIDIA driver telepítés szétkonfigurálhatta a GRUB-ot/kernel-t.
MX Linux bootolás után nem lesz kép → GRUB/kernel ellenőrzés szükséges.

---

## 11. PROFIT RENDSZER

- **PT (Profit Taking)**: +2.0$ (win)
- **SL (Stop Loss)**: -1.0$ (loss/opposite)
- **Ratio (b)**: 2.0
- **Dollar bar threshold**: $444,000 (adaptív, ATR-normált)
- **Session szűrés**: 08:00-23:59 (London/NYC)
- **Max bars**: 8 (triple barrier vertical)
