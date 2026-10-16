# LGBM Copilot — Fejlesztői Környezet

> **Hely:** `/data/LGBM_copilot/`
> **Lemez:** `/dev/sdb1` (219GB, 10% használat, 188GB szabad)
> **Cél:** MT5 EA + LGBM/LSTM copilot fejlesztés — Dollar Bar Triple Barrier módszerrel
> **Előd rendszer:** `/home/Jules/LGBM_mlops` (referencia, kritikai elemzés: `docs/analysis/`)

## Architektúra

```
MT5 EA (MQL5) → TCP Socket → Python Backend → LGBM/LSTM → ZMQ PUB → HUD
     ↑                                                           ↓
     └───────────── PRED|Signal|P_Long|P_Short|P_Noise ←──────────┘
```

## Mappastruktúra

| Mappa | Tartalom |
|-------|----------|
| `src/data_pipeline/` | Dollar Bar generálás, feature engineering (anti-leakage) |
| `src/labeling/` | Triple Barrier címkézés (ATR-alapú, anti-overlabeling) |
| `src/models/` | LGBM és LSTM modellek tanítása |
| `src/evaluation/` | Walk-forward CV, purged k-fold, multi-regime teszt |
| `src/live/` | Éles copilot backend (TCP 5555/5556, ZMQ PUB 5557) |
| `src/utils/` | Segédprogramok (adatbetöltés, normalizáció, stb.) |
| `data/raw/` | Nyers MT5 CSV adatok (tick, OHLCV) |
| `data/processed/` | Feldolgozott (Dollar Bar, fused features) |
| `data/labeled/` | Triple Barrier címkézett adatok |
| `data/exam/` | Vak vizsga adatok (out-of-sample) |
| `models/lgbm/` | LightGBM modellek (.pkl) |
| `models/lstm/` | LSTM modellek (.pth) |
| `models/scalers/` | Normalizációs paraméterek (.npy) |
| `scripts/mt5_collectors/` | MQL5 adatgyűjtő scriptek (.mq5) |
| `scripts/batch/` | Batch feldolgozó scriptek (.sh) |
| `config/` | Konfigurációs fájlok (JSON, YAML) |
| `notebooks/` | Jupyter notebookok (elemzés, vizualizáció) |
| `tests/` | Tesztek (anti-leakage, adatintegritás) |
| `logs/` | Futtatási naplók |
| `docs/architecture/` | Architektúra dokumentáció |
| `docs/methodology/` | Metodológia (Dollar Bar, Triple Barrier, 3MTF) |
| `docs/analysis/` | Qwen elemzések, kritikai elemzés |
| `MT5/Experts/` | EA forráskódok (.mq5) |
| `MT5/Scripts/` | MT5 scriptek (.mq5) |
| `MT5/Indicators/` | Indikátorok (.mq5) |
| `MT5/Include/` | Include fájlok (.mqh) |
| `cache/` | GPU cache, intermediate files |
| `_qwen_analysis/` | Qwen mélyelemzés kimenetek |

## Fejlesztési elvek (a Jules rendszer hibáiból tanulva)

1. **Anti-leakage** — minden feature shift(1) előtt rolling, ZigZag csak real-time (MT5-ből)
2. **Feature konzisztencia** — training = evaluation = live (ugyanazok a feature-ök)
3. **ATR-alapú barrier** — nem fix dollar, volatilitás-skálázott
4. **Walk-forward validáció** — purged k-fold CV, multi-regime, multi-day
5. **Unified threshold** — egyetlen konfiguráció training/eval/live
6. **Dinamikus Dollar Bar threshold** — instrumentum-specifikus, EMA-based
7. **OOS LSTM training** — strictly out-of-sample LGBM predikciókkal
