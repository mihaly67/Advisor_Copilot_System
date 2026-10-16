# Session: kornyezet_mt5_venv_rovidtve_20260923
*Időbélyeg: 2026-09-23T14:28:07.789739*

# Környezet Rögzítés — MT5, venv, könyvtárak
*Időbélyeg: 2026-09-23*

## MetaTrader 5 (Wine)
- **Telepítési útvonal:** `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/`
- **MQL5 Scripts mappa:** `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Scripts/`
- **MQL5 Indicators mappa:** `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Indicators/Indicators/`
- **MQL5 Files (CSV output):** `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Files/`
- **NEM kell telepíteni** — már fut Wine alatt
- **Python MetaTrader5 csomag NEM kell** — offline pipeline MT5 nélkül dolgozik, az EA külön fut

## Központi venv
- **Útvonal:** `/home/Jules/jules_venv/`
- **Python:** `/home/Jules/jules_venv/bin/python3`
- **Pip:** `/home/Jules/jules_venv/bin/pip`

### Telepítve (VAN):
| Csomag | Verzió | Rendszer |
|---|---|---|
| ta | 0.11.0 | Feature engineering (RSI, MACD, MFI, Stoch, BB, EMA, ATR, ROC) |
| lightgbm | 4.7.0 | Modell betanítás |
| optuna | 5.0.0 | 4D küszöb kalibráció |
| scikit-learn | 1.8.0 | Train/test split, metrikák |
| pandas | 3.0.3 | Adatfeldolgozás |
| numpy | 1.26.4 | Numerikus |
| joblib | 1.5.3 | Modell mentés (.pkl) |
| pyzmq | 27.2.0 | Éles copilot ZMQ |
| PyQt5 | 5.15.10 | HUD GUI |
| pyqtgraph | 0.14.0 | HUD grafikon |
| matplotlib | 3.11.1 | SHAP heatmap vizualizáció |
| catboost | 1.2.10 | (kísérleti, nem használt) |

### HIANYZIK (telepítendő):
| Csomag | Miért kell | Telepítés |
|---|---|---|
| shap | Feature importance heatmap, redundancia azonosítás | `/home/Jules/jules_venv/bin/pip install shap` |

### Opcionális (később):
| Csomag | Miért | Telepítés |
|---|---|---|
| MetaTrader5 | Éles copilot ZMQ helyett direkt MT5 API (NEM kötelező, EA ZMQ-jel működik) | `/home/Jules/jules_venv/bin/pip install MetaTrader5` |

## Projekt útvonalak
- **Projekt gyökér:** `/home/Jules/LGBM_mlops/`
- **Master CSV:** `/home/Jules/LGBM_mlops/Master_csv/`
- **Python pipeline:** `/home/Jules/LGBM_mlops/Micro_LGBM/src/`
- **MQL5 Scripts (forrás másolat):** `/home/Jules/LGBM_mlops/MQL5_Scripts/` (üres)
- **Terv fájlok:**
  - `/data/Brain/_qwen_analysis/SCALPER_PIPELINE_PLAN_20260923.md`
  - `/data/Brain/_qwen_analysis/NAVSYSTEM_V222_PYTHON_FORDITAS_20260923.md`
  - `/data/Brain/_qwen_analysis/PROGRESS_UPDATE_20260923.md`

## Pipeline futtatás
```bash
cd /home/Jules/LGBM_mlops/Micro_LGBM/src
/home/Jules/jules_venv/bin/python3 pipeline_master.py
```

## Megjegyzés a `ta` könyvtárról
- A `ta` v0.11.0 tartalmazza: RSI, MACD, MFI, Stochastic, EMA, SMA, BB, ATR, ROC, CCI, ADX, Keltner
- **Williams' %R (WPR):** Lehet, hogy hiányzik a `ta`-ból → implementáláskor ellenőrzendő
  - Alternatíva 1: `talib.WILLR(high, low, close, timeperiod)` (TA-Lib, ha telepítve)
  - Alternatíva 2: Manuális implementáció (egyszerű képlet: (HighestHigh - Close) / (HighestHigh - LowestLow) * -100)